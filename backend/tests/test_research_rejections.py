"""A rejected candidate is an audit artifact, never a successful opinion."""
import asyncio
from app.database import create_db_engine
from app.local_llm import LocalLLMFailure
from app.research_service import ResearchService
from app.research_store import ResearchStore


def test_failure_metrics_and_candidate_quarantine_survive_reopen(migrated):
    engine=create_db_engine(migrated.database_url)
    service=ResearchService(engine,None,None)
    service.store.initialize()
    case=service.store.create_case({'id':'TEST_ONLY','symbol':'TEST_ONLY','asset_class':'FX'},
                                   'Fixture de persistencia, no mercado.','fixture-quarantine')
    jobs=service.store.enqueue(case['id'],'run-quarantine',10,False,'deep')
    for job in jobs[:4]:service.store.finish(job,'SUCCEEDED')
    job=service.store.claim('llm')
    assert job['role_id']=='bull_advocate'
    candidate={'arguments':[{'mechanism':'TEST_ONLY rejected candidate'}]}
    async def fail(current):
        current['_candidate_result']=candidate
        raise LocalLLMFailure('WIRE_STRING_BUDGET',{'finish_reason':'stop','usage':{'completion_tokens':18}})
    service.perform=fail
    asyncio.run(service.execute(job))
    engine.dispose()
    reopened=create_db_engine(migrated.database_url)
    store=ResearchStore(reopened)
    stored=store.get('agent_jobs',job['id'])
    assert stored['state']=='FAILED' and stored['error']=='WIRE_STRING_BUDGET'
    assert stored['attempts']==1 and stored['llm_metrics']['usage']['completion_tokens']==18
    assert '_candidate_result' not in stored
    assert not store.list('agent_results',case['id']) and not store.list('research_claims',case['id'])
    audit=next(a for a in store.list('audit_events') if a['event']=='REJECTED_CANDIDATE')
    assert audit['candidate']==candidate and audit['job_id']==job['id']
    reopened.dispose()
