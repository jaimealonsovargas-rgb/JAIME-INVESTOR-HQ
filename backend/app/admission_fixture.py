"""Invented TEST sessions and prices, exclusively an engineering fixture."""
from datetime import date,datetime,timedelta
from zoneinfo import ZoneInfo
from .admission_contracts import fingerprint,candidate_hash
from .dataset_evidence import evidence_record


def fixture_bundle():
    days=[]; current=date(2023,1,2)
    while len(days)<253:
        if current.weekday()<5: days.append(current)
        current+=timedelta(days=1)
    def stamp(day,hour,minute=0):
        return datetime(day.year,day.month,day.day,hour,minute,tzinfo=ZoneInfo('America/New_York')).isoformat()
    start,end=days[0].isoformat(),days[-2].isoformat()
    cutoff='2024-02-01T00:00:00+00:00'
    c={'version':'admission-candidate-v1','domain':'SYNTHETIC_TEST','provider':'SYNTHETIC_TEST',
       'listing_id':'TEST:DAILY','identity_hash':fingerprint('TEST:IDENTITY'),'symbol':'TEST_DAILY','venue':'TEST_VENUE','currency':'USD',
       'start':start,'end':end,'frequency':'1 day','adjustment':'UNADJUSTED','feed':'TEST_FEED','unit':'PRICE_PER_SHARE',
       'universe_hash':fingerprint('TEST:UNIVERSE'),'bars':[{'session':d.isoformat(),'open':'100','high':'102','low':'99','close':'101','volume':'1000'} for d in days[:-1]],
       'sources':[{'id':'TEST:SOURCE','hash':fingerprint('TEST:SOURCE'),'received_at':cutoff}],'source_errors':[],'cutoff':cutoff}
    interval={k:c[k] for k in ('start','end','symbol','venue','currency','identity_hash','listing_id')}
    interval.update(asset_class='COMMON_STOCK',aliases=[])
    sessions=[{'session':d.isoformat(),'open':stamp(d,9,30),'close':stamp(d,16),'next_open':stamp(days[i+1],9,30)} for i,d in enumerate(days[:-1])]
    payloads={'identity':{'intervals':[interval]},'calendar':{'start':start,'end':end,'sessions':sessions,'venue':c['venue'],'timezone':'America/New_York'},
       'actions':{'start':start,'end':end,'status':'NO_EVENTS','events':[],'coverage':['SPLITS','DIVIDENDS']},
       'semantics':dict({k:c[k] for k in ('start','end','unit','currency','feed','adjustment')},price_basis='EXECUTABLE_UNADJUSTED'),
       'knowledge':{'basis':'PER_BAR_PUBLICATION','observations':[{'session':s['session'],'available_at':s['close']} for s in sessions]},
       'universe':{'start':start,'end':end,'universe_hash':c['universe_hash'],'rule':'FIXED_PREDECLARED_SINGLE_ASSET','selected_at':'2022-12-01T00:00:00+00:00','inclusions':[c['listing_id']],'exclusions':[],'membership_coverage':{'start':start,'end':end,'listing_id':c['listing_id'],'events':[],'as_of':cutoff}},
       'rights':{'scope':'SYNTHETIC_ENGINEERING_ONLY'}}
    return c,{'version':'admission-evidence-v1','records':[evidence_record(k,candidate_hash(c),v,cutoff) for k,v in payloads.items()]}
