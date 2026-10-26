"""Deterministic route from one audited P2 feed to existing ordinary jobs."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.data_catalog import CATALOG
from app.data_rights import readable
from app.database import InstrumentAlias, InstrumentRecord


class ResearchRouter:
    def __init__(self, research):
        self.research = research

    def prepare(self, task):
        # Not a general HTTP tool: no broker, URL, LLM or event-provided instructions.
        if task['objective'] != 'DESCRIPTIVE_RESEARCH' or task['source_access_id'] != 'A21':
            return None, {'quality_state': 'ABSTAINED', 'reason': 'ROUTE_DENIED'}
        data = self.research.data
        source = CATALOG['A21']
        if not readable(source.rights, local_research=True):
            return None, {'quality_state': 'ABSTAINED', 'reason': 'RIGHTS_RESTRICTED'}
        # Avoid waiting indefinitely behind unrelated P2 refreshes. RLock permits
        # the nested query; one attempt, no retry storm when the data lane is busy.
        if not data.lock.acquire(timeout=5):
            return None, {'quality_state': 'ABSTAINED', 'reason': 'DATA_LANE_BUSY'}
        try:
            response = data.query('A21')  # P2 owns transport, quota, parsing and rights.
        finally:
            data.lock.release()
        receipt = dict(access_id='A21', provider=source.provider, state=response.state,
                       checked_at=response.checked_at.isoformat() if response.checked_at else None,
                       latency_ms=response.latency_ms, real_connection=response.real_connection,
                       cache_hit=response.cache_hit, observation_count=len(response.observations))
        if not response.usable or not response.real_connection:
            return None, {'quality_state': 'ABSTAINED', 'reason': response.state, 'source_receipt': receipt}
        with Session(data.engine) as session:
            for observation in sorted(response.observations, key=lambda o: (o.series_id, o.observed_at), reverse=True):
                if observation.stale(data.clock()) or not readable(observation.rights, local_research=True):
                    continue
                statement = select(InstrumentRecord).join(InstrumentAlias, InstrumentAlias.instrument_id == InstrumentRecord.id).where(
                    InstrumentAlias.provider == observation.provider, InstrumentAlias.symbol == observation.series_id,
                    InstrumentAlias.venue == observation.venue, InstrumentAlias.currency == (observation.currency or ''))
                record = session.scalar(statement)
                if record:
                    return record.payload, {'source_receipt': receipt}
        return None, {'quality_state': 'ABSTAINED', 'reason': 'NO_VERIFIED_INSTRUMENT', 'source_receipt': receipt}

    def enqueue(self, task):
        subject = task['subject']
        case = self.research.store.create_case(subject,
            'Revisión descriptiva programada: calidad, trayectoria y variabilidad de la serie autorizada. Sin recomendaciones ni órdenes.',
            task['run_key'], 'descriptive_research',
            origin={'autonomy_task_id': task['id'], 'source_access_ids': ['A21'], 'trigger_type': 'SCHEDULED_RESEARCH'})
        jobs = self.research.run(case['id'], task['run_key'], priority=1, refresh=False, depth='ordinary', summary=False)
        return case['id'], jobs
