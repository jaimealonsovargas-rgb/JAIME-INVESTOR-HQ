from app.database import create_db_engine
from app.research_store import ResearchStore


def test_activity_distinguishes_active_work_and_historical_delivery(migrated):
    store=ResearchStore(create_db_engine(migrated.database_url));store.initialize()
    assert store.role_activity()['data_quality']['last_delivery'] is None
    case=store.create_case({'id':'TEST','symbol':'TEST','asset_class':'CRYPTO'},'TEST_ONLY','test-case')
    store.enqueue(case['id'],'test-run',10,False,'ordinary')
    role=store.role_activity()['data_quality']
    assert role['state']=='QUEUED' and role['current_job']['case_id']==case['id']
    job=store.claim('fetch')
    assert store.role_activity()['data_quality']['state']=='RUNNING'
    store.finish(job,'SUCCEEDED',result={'quality':{'state':'ABSTAINED'},'claims':[{'evidence_ids':['E1','E1']}],
        'features':{'items':[{'evidence_ids':['E1','E2']}]},
        'opinion':{'overview':'PRIVATE_CONTENT_NOT_FOR_ACTIVITY'}})
    role=store.role_activity()['data_quality']
    assert role['state']=='IDLE' and role['current_job'] is None
    assert role['last_delivery']['evidence_count']==2
    assert role['last_delivery']['quality_state']=='ABSTAINED'
    assert 'PRIVATE_CONTENT' not in str(role)
