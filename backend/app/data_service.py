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
from app.data_history import archive
from app.sec_quota import reserve as reserve_sec, backoff as backoff_sec
from app.alpaca_quota import reserve as reserve_alpaca, backoff as backoff_alpaca
from app.storage_budget import StorageGovernor, StorageBlocked, REASONS as STORAGE_REASONS

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

def cache_key(source):
    rights=source.rights.model_dump(mode='json')
    if not rights['local_research_allowed']:
        rights.pop('local_research_allowed')  # Preserve earlier cache identities when policy is unchanged.
    parts=(source.url,source.params,source.feed,rights)
    if source.id in ('A05','A07','A08','A11','A12','A21','B02','B03'):
        parts += ('rolling-v1',)
    identity=repr(parts)
    return 'cache:'+source.id+':'+hashlib.sha256(identity.encode()).hexdigest()[:32]


class DataService:
    def __init__(self, engine, settings=None, http=None, clock=None):
        self.engine=engine;self.settings=settings or DataSettings()
        self.http=http or SafeDataHttp(self.settings)
        self.clock=clock or (lambda:datetime.now(timezone.utc));self.lock=threading.RLock()
        self._storage = None

    @property
    def storage(self):
        if self._storage is None:
            with self.lock:
                if self._storage is None:
                    self._storage = StorageGovernor.for_engine(self.engine)
        return self._storage

    @storage.setter
    def storage(self, value):
        self._storage = value

    def initial(self, source):
        if source.id == 'A20' and not self.settings.agent_reach_public_enabled:
            return DataResult(access_id=source.id,state='DISABLED',reason='Canal público RSS auditado; activar AGENT_REACH_PUBLIC_ENABLED localmente.')
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
                if initial.state in ('DISABLED','NO_CREDENTIALS','CONFIG_REQUIRED','PLAN_REQUIRED','NOT_IMPLEMENTED','RIGHTS_RESTRICTED'):
                    result=initial.model_copy(update={'checked_at':result.checked_at,'latency_ms':result.latency_ms,'http_status':result.http_status,'real_connection':result.real_connection})
                elif not source.rights.display_allowed or not source.rights.access_allowed:
                    result=result.model_copy(update={'state':'RIGHTS_RESTRICTED','reason':REASONS['RIGHTS_RESTRICTED'],'usable':False})
                elif result.usable and record and now>datetime.fromisoformat(record.expires_at):
                    result=result.model_copy(update={'state':'STALE','reason':REASONS['STALE'],'usable':False})
                quota=session.get(DataQuota,source.provider)
                rows.append({'access_id':source.id,'provider':source.provider,'name':source.name,'implemented':source.implemented,'data_kind':source.kind,'asset_class':source.asset_class,'country':source.country,'market':source.venue,'feed':source.feed,'docs':source.docs,'rights':source.rights.model_dump(mode='json'),'quota_note':source.quota_note,'quota_used':quota.used if quota else 0,'next_allowed_at':quota.blocked_until if quota else None,**result.model_dump(mode='json',exclude={'observations'})})
        for row in rows:
            source = CATALOG[row['access_id']]
            row.update(data_tier=source.data_tier, quality_flags=source.quality_flags)
        return {'checked_at':now.isoformat(),'counts':{'candidate_providers':len({s.provider for s in CATALOG.values()}),'candidate_access_modes':len(rows),'implemented_adapters':sum(r['implemented'] for r in rows),'implemented_providers':len({r['provider'] for r in rows if r['implemented']}),'verified_connections':sum(r['real_connection'] for r in rows),'verified_providers':len({r['provider'] for r in rows if r['real_connection']}),'usable_sources':sum(r['usable'] for r in rows),'usable_providers':len({r['provider'] for r in rows if r['usable']}),'no_credentials':sum(r['state']=='NO_CREDENTIALS' for r in rows),'rights_restricted':sum(r['state']=='RIGHTS_RESTRICTED' for r in rows)},'sources':rows}

    def query(self, access_id: str):
        initial = self.initial(CATALOG[access_id])
        if initial.state != 'NOT_VERIFIED':
            return initial
        try:
            with self.storage.admission():
                return self._query(access_id)
        except StorageBlocked as error:
            # Existing cache remains readable, without ingesting or updating anything.
            source = CATALOG[access_id]
            initial = self.initial(source)
            if initial.state != 'NOT_VERIFIED':
                return initial
            if source.rights.display_allowed and source.rights.access_allowed:
                with Session(self.engine) as session:
                    row = session.get(DataRecord, cache_key(source))
                    if row:
                        result = DataResult.model_validate(row.payload)
                        fresh = (self.clock() < datetime.fromisoformat(row.expires_at)
                                 and self.clock() < datetime.fromisoformat(row.updated_at)+timedelta(seconds=source.ttl)
                                 and not (source.id=='A22' and result.observations and all(o.stale(self.clock()) for o in result.observations)))
                        return result.model_copy(update={'cache_hit':True, 'usable':result.usable and fresh,
                            'state':result.state if fresh else 'STALE',
                            'reason':STORAGE_REASONS[error.reason]+' Se conserva la última consulta guardada.'})
            return DataResult(access_id=access_id,state='ERROR',reason=STORAGE_REASONS[error.reason])

    def _query(self, access_id: str):
        source=CATALOG[access_id];initial=self.initial(source)
        if initial.state!='NOT_VERIFIED':return initial
        if not source.implemented:return initial.model_copy(update={'state':'NOT_IMPLEMENTED','reason':REASONS['NOT_IMPLEMENTED']})
        if not source.rights.access_allowed:return initial.model_copy(update={'state':'RIGHTS_RESTRICTED','reason':REASONS['RIGHTS_RESTRICTED']})
        now=self.clock();key=cache_key(source)
        # RLock serializa consultas del proceso; SQLite protege cuotas de otros procesos.
        with self.lock:
            with Session(self.engine) as session, session.begin():
                session.connection().exec_driver_sql('BEGIN IMMEDIATE')
                cached=session.get(DataRecord,key)
                if (cached and now<datetime.fromisoformat(cached.expires_at)
                        and now<datetime.fromisoformat(cached.updated_at)+timedelta(seconds=source.ttl)):
                    result=DataResult.model_validate(cached.payload).model_copy(update={'cache_hit':True})
                    if source.id == 'A22' and result.observations and all(o.stale(now) for o in result.observations):
                        result = result.model_copy(update={'state':'STALE','reason':REASONS['STALE'],'usable':False})
                    if self.http.real and result.real_connection:
                        ingest(session,result.observations)
                        archive(session,source,key,result.observations)
                    return result
                reserve = {'SEC': reserve_sec, 'ALPACA': reserve_alpaca}.get(source.provider)
                if reserve:
                    # The same provider budget is owned by issuer/market workers too.
                    # Do not reset it or count it again with this preset's limits.
                    if reserve(session, now):
                        return DataResult(access_id=source.id,state='RATE_LIMITED',reason=REASONS['RATE_LIMITED'])
                else:
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
                    if any(any(f.startswith('HISTORICAL_') for f in o.quality_flags) for o in observations):state='DELAYED'
                    elif all((received-o.observed_at).total_seconds()>max(60,source.ttl) for o in observations):state='STALE'
                    if source.id == 'A22' and all(o.stale(received) for o in observations):
                        state = 'STALE'
                result=DataResult(access_id=source.id,state=state,reason=REASONS[state],checked_at=received,latency_ms=round((time.perf_counter()-start)*1000),http_status=status,real_connection=self.http.real and bool(observations),usable=bool(observations) and source.rights.display_allowed and self.http.real and state!='STALE',normalized_count=len(observations),observations=observations if source.rights.display_allowed else ())
                failure=None
            except FetchError as error:
                failure=error;result=DataResult(access_id=source.id,state=error.state,reason=REASONS[error.state],checked_at=self.clock(),latency_ms=round((time.perf_counter()-start)*1000),http_status=error.status)
            except (ValueError,KeyError,TypeError,IndexError,OverflowError):
                failure=None;result=DataResult(access_id=source.id,state='INVALID_PAYLOAD',reason=REASONS['INVALID_PAYLOAD'],checked_at=self.clock(),latency_ms=round((time.perf_counter()-start)*1000),http_status=status)
            with Session(self.engine) as session, session.begin():
                session.connection().exec_driver_sql('BEGIN IMMEDIATE')
                quota=session.get(DataQuota,source.provider)
                if result.state in ('AVAILABLE_VERIFIED','DELAYED','STALE','NO_DATA','RIGHTS_RESTRICTED'):quota.failures=0
                else:
                    quota.failures+=1
                    if (failure and failure.state=='RATE_LIMITED') or quota.failures>=3:
                        seconds=max(60,failure.retry_after if failure else 60)
                        backoff = {'SEC': backoff_sec, 'ALPACA': backoff_alpaca}.get(source.provider)
                        if backoff:
                            backoff(session, self.clock(), seconds)
                        else:
                            quota.blocked_until=(self.clock()+timedelta(seconds=seconds)).isoformat()
                expiry=self.clock()+timedelta(seconds=source.ttl)
                public=result.model_dump(mode='json',exclude={'observations'})
                public['observations']=[]
                self._save(session,'status:'+source.id,public,expiry)
                if source.rights.storage_allowed and result.observations:
                    self._save(session,key,result.model_dump(mode='json'),expiry)
                    if self.http.real and result.real_connection:
                        ingest(session,result.observations)
                        archive(session,source,key,result.observations)
                        if source.id == 'A22':
                            from app.universe_zse import register_listing
                            register_listing(session, result.observations[0])
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
