from datetime import datetime, timezone
from app.research_workflows import research_workflows

NOW=datetime(2026,11,4,tzinfo=timezone.utc)


def dossier():
    return dict(id='test', active_run_key='run', runs=['run'], thesis_version=1,
        quality={'state':'VERIFIED_DATA'}, jobs=[{'state':'SUCCEEDED'}],
        evidence=[dict(id='ev', available=True, rights_ok=True, freshness='FRESH', url='https://example.invalid',
            content={'data_kind':'news_metadata','metadata':{'title':'Test', 'event_at':'2026-11-05T12:00:00+00:00','event_confirmed':'true'}})],
        results=[{'claims':[dict(verified=True, claim_type='FACT', text='Observación', evidence_ids=['ev'])]}])


def test_workflows_do_not_invent_thesis_trade_or_future_date():
    d=dossier();r=research_workflows(d,NOW)
    assert r['morning_note']['state']=='AVAILABLE'
    assert r['thesis_tracker']['state']=='NO_THESIS' and r['thesis_tracker']['action'] is None
    assert len(r['catalyst_calendar']['events'])==1
    assert r['morning_note']['trade_ideas']==[]
    del d['evidence'][0]['content']['metadata']['event_confirmed']
    assert research_workflows(d,NOW)['catalyst_calendar']['state']=='NO_CONFIRMED_EVENTS'


def test_expired_or_revoked_evidence_withholds_all_derivatives():
    for field,value in [('freshness','STALE'),('rights_ok',False),('available',False)]:
        d=dossier();d['evidence'][0][field]=value
        r=research_workflows(d,NOW)
        assert r['morning_note']['observations']==[] and r['catalyst_calendar']['events']==[]


def test_failed_job_and_naive_event_date_abstain():
    d=dossier();d['jobs'][0]['state']='FAILED'
    assert research_workflows(d,NOW)['morning_note']['state']=='ABSTAINED'
    d=dossier();d['evidence'][0]['content']['metadata']['event_at']='2026-11-05T12:00:00'
    assert research_workflows(d,NOW)['catalyst_calendar']['events']==[]
