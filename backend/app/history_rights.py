"""Reviewed policy, not user-supplied permissions. API access != archive licence."""
from copy import deepcopy

POLICY = dict(version='history-rights-2026-11-16-v1',provider='IBKR_TWS',
    technical_access='OBSERVED_D1_LIMITED',rights_status='UNVERIFIED_ACCOUNT_AND_USE_SCOPE',
    historical_persistence='DENIED_PENDING_EVIDENCE',algorithmic_research='DENIED_PENDING_SCOPE_CONFIRMATION',
    retention_days=None,retention_status='UNSPECIFIED_BY_VERIFIED_ENTITLEMENT',
    redistribution=False,real_batch_fetch=False,mandatory_cost_status='UNVERIFIED_FOR_D2_USE',
    sources=[
        {'url':'https://gdcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=3089',
         'document':'GFIS 3089, 2026-05-01', 'sections':['2','4','15.E']},
        {'url':'https://ndcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=4569',
         'document':'API supplement 4569, 2026-04-20','sections':['1.2','2','3']}])


def rights(provider):
    if provider=='SYNTHETIC_TEST':
        return dict(version='synthetic-rights-v1',provider=provider,real_batch_fetch=False,
                    historical_persistence='ENGINEERING_FIXTURES_ONLY',algorithmic_research='ENGINEERING_ONLY',
                    retention_status='PRESERVE_SYNTHETIC_EVIDENCE',retention_days=None,redistribution=False)
    if provider!='IBKR_TWS': raise ValueError('UNKNOWN_HISTORY_PROVIDER')
    return deepcopy(POLICY)


def require_ibkr_archive_rights():
    # No CLI/env/JSON switch can grant third-party rights. Replace this gate only
    # after reviewing account/use/feed/cost/retention evidence; not in D2.
    raise ValueError('RIGHTS_UNVERIFIED')


def require_rights(provider):
    if provider=='IBKR_TWS': require_ibkr_archive_rights()
    elif provider!='SYNTHETIC_TEST': raise ValueError('UNKNOWN_HISTORY_PROVIDER')
