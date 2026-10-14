"""Consulta lazy con cache, cuota persistente y evidencia de conexión separada."""
import hashlib
import threading
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.database import DataRecord, DataQuota
from app.data_catalog import CATALOG
from app.data_config import DataSettings
from app.data_contracts import DataResult
from app.data_http import SafeDataHttp, FetchError
from app.data_parsers import parse
from app.data_registry import ingest

REASONS = {
 'AVAILABLE_VERIFIED':'Datos reales recibidos y uso local autorizado.',
 'RIGHTS_RESTRICTED':'Acceso o visualización restringidos; no se muestran valores.',
 'NO_CREDENTIALS':'Configure la clave gratuita en .env local; no se ha consultado la API.',
 'CONFIG_REQUIRED':'Configuración o endpoint oficial pendiente de verificación.',
 'NOT_IMPLEMENTED':'Modalidad candidata; no se cuenta como adaptador.',
 'PLAN_REQUIRED':'No se ha comprobado un endpoint gratuito utilizable.',
 'NOT_VERIFIED':'Adaptador implementado, todavía sin petición HTTP real comprobada.',
 'RATE_LIMITED':'Cuota local o del proveedor agotada; respete el próximo plazo.',
 'AUTH_FAILED':'Credenciales rechazadas.', 'OFFLINE':'Conexión no disponible.',
 'TIMEOUT':'El proveedor superó el tiempo límite.', 'ERROR':'El proveedor rechazó la consulta.',
 'INVALID_PAYLOAD':'La respuesta no cumple su contrato.', 'NO_DATA':'Respuesta válida sin observaciones.',
 'DELAYED':'Serie histórica o EOD; no representa una cotización en tiempo real.',
 'DISABLED':'Fuente desactivada por configuración local.', 'STALE':'Cache caducada; datos históricos, nunca ejecutables.',
}

class DataService:
    def __init__(self, engine, settings=None, http=None, clock=None):
        self.engine=engine;self.settings=settings or DataSettings()
        self.http=http or SafeDataHttp(self.settings)
        self.clock=clock or (lambda:datetime.now(timezone.utc));self.lock=threading.RLock()

    def initial(self, source):
        state=source.block or ('NO_CREDENTIALS' if source.credentials and not all(self.settings.secret(k) for k in source.credentials) else 'NOT_VERIFIED')
        if source.auth=='sec' and state=='NO_CREDENTIALS':state='CONFIG_REQUIRED'
        if source.id in self.settings.data_disabled_sources.split(',') or (not source.credentials and not self.settings.data_public_enabled):state='DISABLED'
        return DataResult(access_id=source.id,state=state,reason=REASONS[state])

    def quality(self):
        now=self.clock();rows=[]
        with Session(self.engine) as session:
            for source in CATALOG.values():
                initial=self.initial(source);record=session.get(DataRecord,'status:'+source.id)
                result=DataResult.model_validate(record.payload) if record else initial
                # Configuración actual manda; una clave retirada no conserva AVAILABLE.
                if initial.state in ('DISABLED','NO_CREDENTIALS','CONFIG_REQUIRED','PLAN_REQUIRED','NOT_IMPLEMENTED'):
                    result=initial.model_copy(update={'checked_at':result.checked_at,'latency_ms':result.latency_ms,'http_status':result.http_status,'real_connection':result.real_connection})
                elif not source.rights.display_allowed or not source.rights.access_allowed:
                    result=result.model_copy(update={'state':'RIGHTS_RESTRICTED','reason':REASONS['RIGHTS_RESTRICTED'],'usable':False})
                elif result.usable and record and now>datetime.fromisoformat(record.expires_at):
                    result=result.model_copy(update={'state':'STALE','reason':REASONS['STALE'],'usable':False})
                quota=session.get(DataQuota,source.provider)
                rows.append({'access_id':source.id,'provider':source.provider,'name':source.name,'implemented':source.implemented,'data_kind':source.kind,'asset_class':source.asset_class,'country':source.country,'market':source.venue,'feed':source.feed,'docs':source.docs,'rights':source.rights.model_dump(mode='json'),'quota_note':source.quota_note,'quota_used':quota.used if quota else 0,'next_allowed_at':quota.blocked_until if quota else None,**result.model_dump(mode='json',exclude={'observations'})})
        return {'checked_at':now.isoformat(),'counts':{'candidate_providers':len({s.provider for s in CATALOG.values()}),'candidate_access_modes':len(rows),'implemented_adapters':sum(r['implemented'] for r in rows),'implemented_providers':len({r['provider'] for r in rows if r['implemented']}),'verified_connections':sum(r['real_connection'] for r in rows),'verified_providers':len({r['provider'] for r in rows if r['real_connection']}),'usable_sources':sum(r['usable'] for r in rows),'usable_providers':len({r['provider'] for r in rows if r['usable']}),'no_credentials':sum(r['state']=='NO_CREDENTIALS' for r in rows),'rights_restricted':sum(r['state']=='RIGHTS_RESTRICTED' for r in rows)},'sources':rows}

    def query(self, access_id: str):
        source=CATALOG[access_id];initial=self.initial(source)
        if initial.state!='NOT_VERIFIED':return initial
        if not source.implemented:return initial.model_copy(update={'state':'NOT_IMPLEMENTED','reason':REASONS['NOT_IMPLEMENTED']})
        if not source.rights.access_allowed:return initial.model_copy(update={'state':'RIGHTS_RESTRICTED','reason':REASONS['RIGHTS_RESTRICTED']})
        now=self.clock();identity=repr((source.url,source.params,source.feed,source.rights.model_dump(mode='json')))
        key='cache:'+source.id+':'+hashlib.sha256(identity.encode()).hexdigest()[:32]
        # RLock serializa consultas del proceso; SQLite protege cuotas de otros procesos.
        with self.lock:
            with Session(self.engine) as session, session.begin():
                session.connection().exec_driver_sql('BEGIN IMMEDIATE')
                cached=session.get(DataRecord,key)
                if cached and now<datetime.fromisoformat(cached.expires_at):
                    result=DataResult.model_validate(cached.payload).model_copy(update={'cache_hit':True})
                    if self.http.real:ingest(session,result.observations)
                    return result
                quota=session.get(DataQuota,source.provider)
                if quota is None:
                    quota=DataQuota(key=source.provider,window_start=now.isoformat(),used=0,failures=0);session.add(quota)
                if quota.blocked_until and now<datetime.fromisoformat(quota.blocked_until):
                    return DataResult(access_id=source.id,state='RATE_LIMITED',reason=REASONS['RATE_LIMITED'])
                if (now-datetime.fromisoformat(quota.window_start)).total_seconds()>=source.window:
                    quota.window_start=now.isoformat();quota.used=0
                if quota.used>=source.limit:
                    quota.blocked_until=(datetime.fromisoformat(quota.window_start)+timedelta(seconds=source.window)).isoformat()
                    return DataResult(access_id=source.id,state='RATE_LIMITED',reason=REASONS['RATE_LIMITED'])
                quota.used+=1
            start=time.perf_counter();status=None
            try:
                raw,status=self.http.fetch(source);received=self.clock();observations=parse(source,raw,received)
                state='AVAILABLE_VERIFIED' if observations and source.rights.display_allowed else 'RIGHTS_RESTRICTED' if observations else 'NO_DATA'
                if state=='AVAILABLE_VERIFIED' and source.kind=='market_quote':
                    if any('HISTORICAL_EOD' in o.quality_flags for o in observations):state='DELAYED'
                    elif all((received-o.observed_at).total_seconds()>max(60,source.ttl) for o in observations):state='STALE'
                result=DataResult(access_id=source.id,state=state,reason=REASONS[state],checked_at=received,latency_ms=round((time.perf_counter()-start)*1000),http_status=status,real_connection=self.http.real and bool(observations),usable=bool(observations) and source.rights.display_allowed and self.http.real and state!='STALE',normalized_count=len(observations),observations=observations if source.rights.display_allowed else ())
                failure=None
            except FetchError as error:
                failure=error;result=DataResult(access_id=source.id,state=error.state,reason=REASONS[error.state],checked_at=self.clock(),latency_ms=round((time.perf_counter()-start)*1000),http_status=error.status)
            except (ValueError,KeyError,TypeError,IndexError,OverflowError):
                failure=None;result=DataResult(access_id=source.id,state='INVALID_PAYLOAD',reason=REASONS['INVALID_PAYLOAD'],checked_at=self.clock(),latency_ms=round((time.perf_counter()-start)*1000),http_status=status)
            with Session(self.engine) as session, session.begin():
                quota=session.get(DataQuota,source.provider)
                if result.state in ('AVAILABLE_VERIFIED','DELAYED','STALE','NO_DATA','RIGHTS_RESTRICTED'):quota.failures=0
                else:
                    quota.failures+=1
                    if failure and failure.state=='RATE_LIMITED' or quota.failures>=3:
                        quota.blocked_until=(self.clock()+timedelta(seconds=max(60,failure.retry_after if failure else 60))).isoformat()
                expiry=self.clock()+timedelta(seconds=source.ttl)
                public=result.model_dump(mode='json',exclude={'observations'})
                public['observations']=[]
                self._save(session,'status:'+source.id,public,expiry)
                if source.rights.storage_allowed and result.observations:
                    self._save(session,key,result.model_dump(mode='json'),expiry)
                    if self.http.real:ingest(session,result.observations)
                # Cache acotada; nunca guarda cuerpos/headers/secretos originales.
                keys=list(session.scalars(select(DataRecord.key).order_by(DataRecord.updated_at.desc()).offset(256)))
                if keys:session.execute(delete(DataRecord).where(DataRecord.key.in_(keys)))
            return result

    def _save(self,session,key,payload,expiry):
        row=session.get(DataRecord,key)
        if row is None:row=DataRecord(key=key,payload=payload,expires_at=expiry.isoformat(),updated_at=self.clock().isoformat());session.add(row)
        else:row.payload=payload;row.expires_at=expiry.isoformat();row.updated_at=self.clock().isoformat()

def select_equivalent(observations, *, kind, series_id, feed, period_precision, venue, currency, unit, now):
    """Fallback solo entre observaciones de idéntica semántica, nunca IEX/SIP."""
    valid=[o for o in observations if (o.data_kind,o.series_id,o.feed,o.period_precision,o.venue,o.currency,o.unit)==(kind,series_id,feed,period_precision,venue,currency,unit) and o.rights.display_allowed and not o.stale(now)]
    return max(valid,key=lambda o:(o.observed_at,o.received_at)) if valid else None
