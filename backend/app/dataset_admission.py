"""Deterministic, fail-closed daily dataset admission, without price output."""
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import hashlib
from .admission_contracts import fingerprint, validate_candidate, instant
from .dataset_evidence import verified_records, REGISTRY_VERSION
from . import dataset_evidence
from .history_rights import require_ibkr_archive_rights, POLICY as IBKR_POLICY
from .b32_review import PROTOCOL as RETROSPECTIVE

POLICY='dataset-admission-v1'
PROTOCOL='daily-trend-admission-v1'


def code_hash():
    return hashlib.sha256(b''.join(Path(__file__).with_name(name).read_bytes() for name in
        ('admission_contracts.py','dataset_evidence.py','dataset_admission.py','admission_fixture.py','admission_history.py','admission_market.py','dataset_manifests.py','history_rights.py','b32_review.py') if Path(__file__).with_name(name).exists())).hexdigest()


def evaluate(candidate:dict,evidence:dict|None=None,*,protocol=PROTOCOL)->dict:
    if protocol not in (PROTOCOL, RETROSPECTIVE):
        raise ValueError('ADMISSION_PROTOCOL_UNKNOWN')
    retrospective=protocol==RETROSPECTIVE
    checks=[]
    records={}
    def check(code,ok,detail,kind=None):
        record=records.get(kind)
        labels={'domain':'Dominio y proveedor','native_currency':'Moneda nativa','source_integrity':'Integridad de fuentes','identity':'Identidad histórica','calendar':'Calendario exacto','rights':'Derechos de uso','universe':'Universo predeclarado','knowledge_time':'Disponibilidad temporal','corporate_actions':'Acciones corporativas','price_semantics':'Semántica de precios','protocol_depth':'Profundidad del protocolo','ohlcv_grain':'Calidad y frecuencia OHLCV','evidence_integrity':'Integridad de evidencias','execution_future_gates':'Validación, riesgo y ejecución pendientes','candidate_contract':'Contrato de entrada','period_cutoff':'Periodo conocido al corte','ibkr_current_rights':'Derechos actuales IBKR'}
        checks.append({'code':code,'state':'PASS' if ok else 'BLOCKED','label':labels[code],
            'detail':'VERIFIED' if ok else detail,'evidence_refs':([{'id':record['id'],'hash':record['hash']}] if record else [])})
    try:
        c=validate_candidate(candidate)
    except (ValueError,TypeError,RecursionError):
        c=None
    if c is None:
        check('candidate_contract',False,'INVALID_BOUNDED_CANDIDATE')
        manifest={'version':'admission-manifest-v1','policy':POLICY,'protocol':protocol,'code_hash':code_hash(),
          'candidate_hash':None,'domain':'INVALID','provider':'INVALID','listing_id':None,'period':None,'as_of':None,
          'scope':{'family':'DAILY_TREND','registry_version':REGISTRY_VERSION,'registry_hash':fingerprint(dataset_evidence.trusted_registry())},
          'input_scope':None,'source_refs':[],'source_errors':['INVALID_BOUNDED_CANDIDATE'],'checks':checks,'counts':{'received':0,'expected':0,'usable':0,'warmup':60},
          'readiness':{'research':'BLOCKED','backtest':'BLOCKED','execution_sim':'BLOCKED'},'engineering_state':'BLOCKED'}
        return dict(manifest,manifest_id=fingerprint(manifest))
    records,errors=verified_records(c,evidence if evidence is not None else dataset_evidence.registered_evidence(c))
    synthetic=c['domain']==c['provider']=='SYNTHETIC_TEST'
    testnames=all(c[k].startswith('TEST') for k in ('listing_id','symbol','venue'))
    realnames=all(not c[k].startswith('TEST') for k in ('listing_id','symbol','venue'))
    domain_ok=(synthetic and testnames) or (c['domain']=='MARKET_DATA' and c['provider']!='SYNTHETIC_TEST' and realnames)
    if retrospective:
        domain_ok=domain_ok and c['domain']=='MARKET_DATA' and c['provider']=='ALPACA' and c['feed']=='iex' and c['adjustment']=='raw'
    check('domain',domain_ok,'DOMAIN_PROVIDER_NAMESPACE_MISMATCH')
    check('native_currency',c['currency'] is not None,'NATIVE_CURRENCY_UNKNOWN')
    check('period_cutoff',c['end']<=c['cutoff'][:10],'PERIOD_AFTER_CUTOFF')
    check('evidence_integrity',not errors,','.join(errors) or 'EVIDENCE_MISSING')
    check('source_integrity',bool(c['sources']) and not c['source_errors'] and len({s['id'] for s in c['sources']})==len(c['sources']) and all(s['received_at']<=c['cutoff'] and (synthetic or not s['id'].startswith('TEST')) for s in c['sources']),','.join(c['source_errors']) or 'SOURCE_MISSING_ERRORS_DUPLICATE_OR_AFTER_CUTOFF')
    bars=c['bars']; days=[b['session'] for b in bars]
    quality=True
    for b in bars:
        o,h,l,cl,v=(Decimal(b[k]) for k in ('open','high','low','close','volume'))
        quality=quality and min(o,h,l,cl)>0 and v>=0 and v==v.to_integral_value() and l<=min(o,cl)<=max(o,cl)<=h
    check('ohlcv_grain',bool(bars) and quality and days==sorted(set(days)) and all(c['start']<=d<=c['end'] for d in days),'INVALID_OHLCV_DUPLICATE_OR_UNORDERED_SESSION')
    def payload(kind): return records.get(kind,{}).get('payload',{})
    def covered(p): return p.get('start')==c['start'] and p.get('end')==c['end']
    identity=payload('identity'); intervals=identity.get('intervals',[])
    identity_ok=isinstance(intervals,list) and 0<len(intervals)<=5000
    cursor=date.fromisoformat(c['start']).toordinal()
    if identity_ok:
        for interval in intervals:
            try:
                first=date.fromisoformat(interval['start']).toordinal()
                last=date.fromisoformat(interval['end']).toordinal()
                identity_ok=identity_ok and first==cursor and last>=cursor and interval['end']<=c['end'] and all(interval[k]==c[k] for k in ('symbol','venue','currency','identity_hash','listing_id')) and interval['asset_class']=='COMMON_STOCK' and interval['aliases']==[]
                cursor=last+1
            except (KeyError,ValueError,TypeError): identity_ok=False
    check('identity',identity_ok and cursor==date.fromisoformat(c['end']).toordinal()+1,'IDENTITY_INTERVAL_GAP_OR_ATTRIBUTE_MISMATCH','identity')
    cal=payload('calendar'); sessions=cal.get('sessions',[]); calendar_ok=covered(cal) and isinstance(sessions,list) and 0<len(sessions)<=5000
    normalized=[]
    if calendar_ok:
        try:
            tz=ZoneInfo(cal['timezone'])
            calendar_ok=calendar_ok and cal['venue']==c['venue']
            for s in sessions:
                normalized.append({'session':s['session'],'open':instant(s['open']),'close':instant(s['close']),'next_open':instant(s['next_open'])})
            calendar_ok=all(s['open']<s['close']<s['next_open'] and s['close']<=c['cutoff'] and c['start']<=s['session']<=c['end'] for s in normalized)
            calendar_ok=calendar_ok and cal['venue']==c['venue'] and all(datetime.fromisoformat(s[k]).astimezone(tz).date().isoformat()==s['session'] for s in normalized for k in ('open','close'))
            calendar_ok=calendar_ok and [s['session'] for s in normalized]==days and days==sorted(set(days)) and all(normalized[i]['next_open']==normalized[i+1]['open'] for i in range(len(normalized)-1))
        except (KeyError,ValueError,TypeError,ZoneInfoNotFoundError): calendar_ok=False
    check('calendar',calendar_ok,'EXACT_SESSIONS_OR_EXPLICIT_OPEN_CLOSE_EVIDENCE_MISSING','calendar')
    actions=payload('actions'); actions_ok=covered(actions) and actions.get('status')=='NO_EVENTS' and actions.get('events')==[] and actions.get('coverage')==['SPLITS','DIVIDENDS']
    check('corporate_actions',actions_ok,'ACTIONS_COVERAGE_MISSING_OR_EVENTS_UNSUPPORTED','actions')
    sem=payload('semantics')
    semantics_ok=actions_ok and covered(sem) and sem.get('unit')==c['unit'] and sem.get('currency')==c['currency'] and sem.get('feed')==c['feed'] and sem.get('adjustment')==c['adjustment'] and sem.get('price_basis')=='EXECUTABLE_UNADJUSTED' and (c['adjustment']=='UNADJUSTED' or sem.get('equivalence')=='ZERO_ACTIONS_EQUIVALENT')
    if retrospective:
        semantics_ok=(actions_ok and covered(sem) and all(sem.get(k)==c[k] for k in ('unit','currency','feed','adjustment'))
            and sem.get('price_basis')=='IEX_DAILY_OPEN_PROXY' and sem.get('execution_claim') is False
            and sem.get('open_close_basis')=='ELIGIBLE_REGULAR_SESSION_TRADES')
    check('price_semantics',semantics_ok,'EXECUTABLE_PRICE_EQUIVALENCE_NOT_EVIDENCED','semantics')
    knowledge=payload('knowledge'); observations=knowledge.get('observations',[]); knowledge_ok=calendar_ok and isinstance(observations,list) and len(observations)==len(normalized) and knowledge.get('basis')=='PER_BAR_PUBLICATION'
    if knowledge_ok:
        try:
            knowledge_ok=all(o['session']==s['session'] and s['close']<=instant(o['available_at'])<s['next_open'] and instant(o['available_at'])<=c['cutoff'] for o,s in zip(observations,normalized))
        except (KeyError,ValueError,TypeError): knowledge_ok=False
    if retrospective:
        knowledge_ok=(calendar_ok and knowledge.get('basis')=='CURRENT_REVISED_HISTORY'
            and knowledge.get('signal_information')=='PRIOR_SESSION_CLOSE_ASSUMED'
            and knowledge.get('point_in_time_claim') is False and observations==[])
    check('knowledge_time',knowledge_ok,'PER_BAR_AVAILABLE_AT_MISSING_OR_LOOKAHEAD','knowledge')
    universe=payload('universe')
    try:
        universe_ok=covered(universe) and universe.get('universe_hash')==c['universe_hash'] and universe.get('rule')=='FIXED_PREDECLARED_SINGLE_ASSET' and instant(universe['selected_at'])<c['start']+'T00:00:00+00:00' and instant(universe['selected_at'])<=instant(records['universe']['published_at']) and universe.get('inclusions')==[c['listing_id']] and universe.get('exclusions')==[] and universe.get('membership_coverage')=={'start':c['start'],'end':c['end'],'listing_id':c['listing_id'],'events':[],'as_of':c['cutoff']}
    except (KeyError,ValueError,TypeError): universe_ok=False
    if retrospective:
        try:
            selected=instant(universe['selected_at'])
            universe_ok=(covered(universe) and universe.get('universe_hash')==c['universe_hash']
                and universe.get('rule')=='FIXED_EX_POST_SINGLE_ASSET'
                and c['end']+'T23:59:59+00:00'<selected<=instant(records['universe']['published_at'])<=c['cutoff']
                and bool(c['sources']) and selected<=min(s['received_at'] for s in c['sources'])
                and universe.get('inclusions')==[c['listing_id']] and universe.get('exclusions')==[]
                and universe.get('survivorship_bias_acknowledged') is True and universe.get('oos_reserved') is False)
        except (KeyError,ValueError,TypeError): universe_ok=False
    check('universe',universe_ok,'PREPERIOD_SELECTION_INCLUSION_DELISTING_EVIDENCE_MISSING','universe')
    rights=payload('rights'); rights_ok=synthetic and rights.get('scope')=='SYNTHETIC_ENGINEERING_ONLY'
    if not synthetic:
        try:
            retention=rights['retention']; days_allowed=retention['days']
            retention_ok=(set(retention)=={'days','review'} and type(days_allowed) is int
                and 1<=days_allowed<=36600 and retention['review']=='FINITE_REVIEWED'
                and bool(c['sources']) and all(datetime.fromisoformat(s['received_at'])+timedelta(days=days_allowed)>=datetime.fromisoformat(c['cutoff']) for s in c['sources']))
            rights_ok=(covered(rights) and all(rights.get(k)==c[k] for k in ('provider','feed','listing_id'))
                and len(rights['account_scope_hash'])==64 and all(ch in '0123456789abcdef' for ch in rights['account_scope_hash'])
                and rights['uses']==['LOCAL_RESEARCH','BACKTEST','ARCHIVE'] and retention_ok
                and rights['cost_eur']=='0' and rights['redistribution']=='PROHIBITED'
                and all(instant(rights['valid_from'])<=s['received_at'] for s in c['sources'])
                and instant(rights['valid_to'])>=c['cutoff'])
        except (KeyError,ValueError,TypeError,OverflowError): rights_ok=False
        if retrospective:
            try:
                retention=rights['retention']
                rights_ok=(covered(rights) and all(rights.get(k)==c[k] for k in ('provider','feed','listing_id'))
                    and len(rights['account_scope_hash'])==64 and all(ch in '0123456789abcdef' for ch in rights['account_scope_hash'])
                    and rights['uses']==['LOCAL_RESEARCH','BACKTEST','ARCHIVE']
                    and rights['scope']=='PERSONAL_LOCAL_NONCOMMERCIAL' and rights['cost_eur']=='0'
                    and rights['redistribution']=='PROHIBITED' and retention['provider_period']=='UNSPECIFIED'
                    and retention['internal_review_days']==30
                    and instant(rights['valid_from'])<=min(s['received_at'] for s in c['sources'])
                    and c['cutoff']<=instant(rights['valid_to'])==instant(retention['review_expires_at'])
                    and datetime.fromisoformat(instant(rights['valid_to']))-datetime.fromisoformat(instant(rights['valid_from']))==timedelta(days=30))
            except (KeyError,ValueError,TypeError,OverflowError): rights_ok=False
    check('rights',rights_ok,'UNVERIFIED_ACCOUNT_FEED_USE_ARCHIVE_RETENTION_ZERO_COST','rights')
    ibkr_ok=True
    if c['provider']=='IBKR_TWS':
        try: require_ibkr_archive_rights()
        except ValueError: ibkr_ok=False
    check('ibkr_current_rights',ibkr_ok,'CURRENT_IBKR_ACCOUNT_USE_SCOPE_UNVERIFIED')
    check('protocol_depth',len(days)==252 if retrospective else len(days)>=252,'MINIMUM_252_SESSIONS_60_WARMUP_192_USABLE')
    passed=all(ch['state']=='PASS' for ch in checks)
    research_gates={'domain','native_currency','period_cutoff','evidence_integrity','source_integrity','ohlcv_grain','identity','rights','ibkr_current_rights'}
    research_passed=all(ch['state']=='PASS' for ch in checks if ch['code'] in research_gates)
    check('execution_future_gates',False,'B4_VALIDATION_B5_RISK_B6_OMS_RECONCILIATION_REQUIRED')
    ready=('ENGINEERING_ONLY' if synthetic else 'BACKTEST_READY') if passed else 'BLOCKED'
    if retrospective and passed: ready='BACKTEST_READY_EXPLORATORY'
    research_ready=('ENGINEERING_ONLY' if synthetic else 'RESEARCH_READY') if research_passed else 'BLOCKED'
    manifest={'version':'admission-manifest-v1','policy':POLICY,'protocol':protocol,'code_hash':code_hash(),
       'candidate_hash':fingerprint(c),'domain':c['domain'],'provider':c['provider'],'listing_id':c['listing_id'],
       'period':{'start':c['start'],'end':c['end']},'as_of':c['cutoff'],
       'scope':{'family':'DAILY_TREND','registry_version':REGISTRY_VERSION,'registry_hash':fingerprint(dataset_evidence.trusted_registry()),'ibkr_policy_version':IBKR_POLICY['version'],'ibkr_policy_hash':fingerprint(IBKR_POLICY),'statistical_acceptance':False},
       'input_scope':{k:c[k] for k in ('version','identity_hash','symbol','venue','currency','universe_hash','frequency','adjustment','feed','unit')},
       'source_refs':c['sources'],'source_errors':c['source_errors'],'checks':checks,'counts':{'received':len(days),'expected':len(sessions) if isinstance(sessions,list) else 0,'warmup':60,'usable':max(0,len(days)-60)},
       'readiness':{'research':research_ready,'backtest':ready,'execution_sim':'BLOCKED'},'engineering_state':'ENGINEERING_READY' if passed else 'BLOCKED'}
    if retrospective:
        manifest['scope'].update(temporal_basis='CURRENT_REVISED_HISTORY',universe_basis='EX_POST_SINGLE_SURVIVOR',
            fill_basis='IEX_DAILY_OPEN_PROXY',point_in_time_claim=False,oos_reserved=False,
            review_expires_at=rights.get('valid_to'))
    return dict(manifest,manifest_id=fingerprint(manifest))
