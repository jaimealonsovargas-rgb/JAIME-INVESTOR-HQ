"""Bounded collection orchestration; no new scheduler or readiness promotion."""
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
import json
import re
from app.history_contracts import BatchRequest
from app.history_rights import require_rights
from app.history_store import HistoryStore
from app.ibkr_history_transport import IbkrHistoryTransport,HistoryTransportError,decimal_string
from app.storage_budget import StorageGovernor,StorageBlocked,MIB
from app.data_identity import fingerprint


class SyntheticHistoryTransport:
    provider='SYNTHETIC_TEST'
    def __init__(self,clock):self.clock=clock
    def fetch(self,request):
        if request['provider']!=self.provider or not request['listing_id'].startswith('TEST_'):
            raise HistoryTransportError('INVALID_RESPONSE')
        bars=[]; day=date.fromisoformat(request['start']); end=date.fromisoformat(request['end'])
        while day<=end:
            value=Decimal(10+(day.toordinal()%19))
            bars.append(dict(session=str(day),open=str(value),high=str(value+2),low=str(value-1),close=str(value+1),volume='100'))
            day+=timedelta(days=1)
        return dict(provider=self.provider,request_hash=fingerprint(request),completed=True,
                    received_at=self.clock().isoformat(),feed='SYNTHETIC_TEST',bars=bars)


def normalize(response,request,now):
    """Canonical shared snapshot. No receipt time/revision in content identity."""
    if len(json.dumps(response,allow_nan=False))>512*1024:raise ValueError('INVALID_RESPONSE')
    if (response.get('provider')!=request['provider'] or response.get('request_hash')!=fingerprint(request)
            or response.get('completed') is not True):raise ValueError('INVALID_RESPONSE')
    received=datetime.fromisoformat(response['received_at'])
    if received.utcoffset() is None or received>now+timedelta(seconds=5) or received<now-timedelta(minutes=5):
        raise ValueError('INVALID_RESPONSE')
    feeds={'SYNTHETIC_TEST'} if request['provider']=='SYNTHETIC_TEST' else {'DELAYED_HISTORY_ADVISORY_2188','HISTORICAL_UNCONFIRMED'}
    if response.get('feed') not in feeds:raise ValueError('INVALID_RESPONSE')
    values=response['bars']
    if not isinstance(values,list) or len(values)>64:raise ValueError('INVALID_RESPONSE')
    bars=[];previous=''
    for bar in values:
        if not isinstance(bar,dict) or set(bar)!={'session','open','high','low','close','volume'}:raise ValueError('INVALID_RESPONSE')
        session=bar['session']
        if str(date.fromisoformat(session))!=session or not request['start']<=session<=request['end'] or session<=previous:
            raise ValueError('INVALID_RESPONSE')
        canonical=dict(session=session)
        for key in ('open','high','low','close','volume'):
            if not isinstance(bar[key],str):raise ValueError('INVALID_RESPONSE')
            canonical[key]=decimal_string(bar[key],volume=key=='volume')
        opened,high,low,closed=[Decimal(canonical[k]) for k in ('open','high','low','close')]
        if not low<=min(opened,closed)<=max(opened,closed)<=high:raise ValueError('INVALID_RESPONSE')
        bars.append(canonical);previous=session
    payload=dict(version='history-normalized-v1',request={k:v for k,v in request.items() if k!='revision'},
                 feed=response['feed'],bars=bars)
    coverage=dict(observed_sessions=len(bars),first_session=bars[0]['session'] if bars else None,
        last_session=bars[-1]['session'] if bars else None,feed=response['feed'],currency=request['contract']['currency'],
        unit='PRICE_PER_SHARE',identity='PINNED_REQUEST_NOT_VERIFIED',calendar='NOT_VALIDATED',gaps='NOT_ASSESSED',
        corporate_actions='NOT_VERIFIED',adjustment=request['adjustment'],backtest_ready=False,execution_ready=False,
        retention='SYNTHETIC_EVIDENCE_PRESERVE' if request['provider']=='SYNTHETIC_TEST' else 'REQUIRES_REVIEWED_ENTITLEMENT',
        raw_response_storage='RAM_ONLY',cache_policy='REUSE_24H_NOT_RETENTION_PERIOD')
    return payload,coverage,received.astimezone(timezone.utc)


class HistoryService:
    def __init__(self,engine,*,clock=None,transport=None,storage=None):
        self.engine=engine;self.store=HistoryStore(engine)
        self.clock=clock or (lambda:datetime.now(timezone.utc))
        self.transport=transport
        self.storage=storage or StorageGovernor.for_engine(engine)

    def enqueue(self,key,request):
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',key):raise ValueError('INVALID_BATCH_ID')
        body=BatchRequest.model_validate(request)
        if body.end>=self.clock().astimezone(timezone.utc).date():raise ValueError('COMPLETED_DATES_REQUIRED')
        count=len(body.targets)*(((body.end-body.start).days//31)+1)
        with self.storage.admission(reserve=max(8*MIB,count*4096),destination='data'):
            return self.store.status(self.store.enqueue(key,body,self.clock()))

    def control(self,key,action):
        with self.storage.admission(reserve=MIB,destination='data'):
            self.store.control(key,action,self.clock())
        return self.store.status(key)

    def step(self,key):
        try:
            with self.storage.admission(reserve=8*MIB,destination='data'):
                job=self.store.claim(key,self.clock())
                if job is None:return dict(worked=False,state='NO_DUE_WORK')
                if job.get('terminal'):return dict(worked=True,state='CHECKPOINTED')
                try:
                    require_rights(job['request']['provider'])
                    transport=self.transport or (SyntheticHistoryTransport(self.clock) if job['request']['provider']=='SYNTHETIC_TEST' else IbkrHistoryTransport())
                    if transport.provider!=job['request']['provider']:raise ValueError('IDENTITY_CHANGED')
                    # A paused/cancelled/lost claim must never start a new request.
                    with self.engine.begin() as c:
                        if self.store.owned(c,job,self.clock()) is None:
                            self.store.release(c,job)
                            return dict(worked=True,state='CLAIM_LOST')
                    response=transport.fetch(job['request'])
                    payload,coverage,received=normalize(response,job['request'],self.clock())
                    accepted=self.store.accept(job,payload,coverage,received,self.clock())
                    return dict(worked=True,state='COLLECTED' if accepted else 'CLAIM_LOST')
                except HistoryTransportError as error:
                    reason='RIGHTS_UNVERIFIED' if error.reason=='RIGHTS_RESTRICTED' else error.reason
                except (ValueError,KeyError,TypeError,OverflowError):
                    reason='INVALID_RESPONSE'
                except Exception:
                    reason='PROVIDER_RUNTIME_ERROR'
                self.store.fail(job,reason,self.clock())
                return dict(worked=True,state=reason)
        except StorageBlocked as error:
            return dict(worked=False,state='STORAGE_'+error.reason)


def fixture_request(count=10):
    return dict(provider='SYNTHETIC_TEST',start='2000-01-01',end='2000-02-02',
        targets=[dict(listing_id=f'TEST_{i:05}',identity_hash=fingerprint(['TEST_ONLY',i]),
            contract=dict(conId=i+1,symbol=f'TEST_{i:05}',secType='STK',exchange='SMART',primaryExchange='TEST',currency='USD'))
                 for i in range(count)])
