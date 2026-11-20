from app.data_catalog import CATALOG
from app.data_service import DataService
from app.data_config import DataSettings


def test_unofficial_candidates_are_not_live_connections_or_rights_grants():
    data=DataService(None,DataSettings(_env_file=None))
    for ident in ('C01','C02'):
        source=CATALOG[ident]
        assert source.data_tier==2 and 'UNOFFICIAL_SOURCE' in source.quality_flags
        assert source.rights.scope=='internal' and not source.rights.redistribution_allowed
        assert not source.rights.local_research_allowed and not source.implemented
        result=data.query(ident)
        assert result.state=='NOT_IMPLEMENTED' and not result.real_connection and not result.observations
