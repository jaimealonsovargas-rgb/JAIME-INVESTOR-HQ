from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import pytest
from sqlalchemy import select, func
from app.company_model import build_model
from app.company_review import review_model
from app.company_service import CompanyService, MODELS, REQUESTS
from app.sec_normalize import parse_companyfacts
from test_sec_financials import service, companyfacts, drain, CIK, ACCN

SOURCE=dict(snapshot_id='test-only',receipt_id='test-receipt',payload_hash='test-hash',received_at='2026-09-04T00:00:00+00:00')


def accounting():
    body=companyfacts(value=100)
    concepts=body['facts']['us-gaap']
    for tag, value, duration in [
        ('RevenueFromContractWithCustomerExcludingAssessedTax',200,True),
        ('NetIncomeLoss',20,True),('OperatingIncomeLoss',40,True),
        ('Assets',100,False),('Liabilities',60,False),
        ('StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',40,False),
        ('AssetsCurrent',50,False),('LiabilitiesCurrent',25,False),
        ('NetCashProvidedByUsedInOperatingActivities',60,True),
        ('PaymentsToAcquirePropertyPlantAndEquipment',10,True)]:
        row=dict(end='2026-06-30',val=value,accn=ACCN,filed='2026-09-01',form='10-K',fy=2026,fp='FY')
        if duration: row['start']='2025-07-01'
        previous={**row,'end':'2025-06-30','val':value/2}
        if duration: previous['start']='2024-07-01'
        concepts[tag]={'units':{'USD':[row,previous]}}
    return body


def model(body=None):
    return build_model(CIK,parse_companyfacts(body or accounting(),CIK)[0],SOURCE)


def test_hand_calculated_ratios_cash_proxy_and_same_filing_growth():
    m=model(); rows={r['id']:r for r in m['metrics']}
    assert Decimal(rows['operating_margin']['value'])==20
    assert Decimal(rows['parent_net_margin']['value'])==10
    assert Decimal(rows['current_ratio']['value'])==2
    assert Decimal(rows['cfo_less_ppe']['value'])==50
    assert m['earnings']['changes'][0]['value']=='100'
    assert {f['accession'] for f in m['evidence'].values()}=={ACCN}
    review=review_model(m)
    assert next(c for c in review['checks'] if c['id']=='balance')['state']=='PASS'
    assert review['state']=='PARTIAL'  # cash reconciliation has missing inputs
    assert m['valuation']['target_price'] is None and not m['execution_ready']


@pytest.mark.parametrize('base',[0,-100])
def test_zero_and_negative_growth_bases_keep_delta_not_percentage(base):
    body=accounting(); body['facts']['us-gaap']['RevenueFromContractWithCustomerExcludingAssessedTax']['units']['USD'][1]['val']=base
    r=model(body)['earnings']['changes'][0]
    assert r['value'] is None and Decimal(r['delta'])==200-base


def test_missing_does_not_become_zero_and_parent_equity_cannot_reconcile_total_balance():
    body=accounting()
    del body['facts']['us-gaap']['StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest']
    del body['facts']['us-gaap']['PaymentsToAcquirePropertyPlantAndEquipment']
    m=model(body)
    assert next(r for r in m['metrics'] if r['id']=='cfo_less_ppe')['value'] is None
    assert next(c for c in review_model(m)['checks'] if c['id']=='balance')['state']=='BLOCKED'


def test_concept_change_or_incompatible_period_blocks_growth():
    body=accounting(); tags=body['facts']['us-gaap']
    old=tags['RevenueFromContractWithCustomerExcludingAssessedTax']['units']['USD'].pop()
    tags['Revenues']={'units':{'USD':[old]}}
    assert model(body)['earnings']['changes'][0]['value'] is None
    body=accounting()
    for item in body['facts']['us-gaap'].values():
        for f in item['units']['USD']:
            if f.get('start')=='2024-07-01': f['start']='2024-08-01'
    assert model(body)['earnings']['changes'][0]['delta'] is None


def test_other_filing_comparatives_are_never_silently_substituted():
    body=accounting()
    for item in body['facts']['us-gaap'].values():
        for f in item['units']['USD']:
            if f['end']=='2025-06-30': f['accn']='0000000001-25-000001'
    assert model(body)['comparative'] is None


def test_independent_reviewer_rejects_tampered_arithmetic_and_balance():
    m=model(); m['metrics'][0]['value']='999'
    assert review_model(m)['state']=='FAILED'
    body=accounting();body['facts']['us-gaap']['Assets']['units']['USD'][0]['val']=101
    assert next(c for c in review_model(model(body))['checks'] if c['id']=='balance')['residual']=='1'


def test_negative_capex_is_not_assumed_a_valid_payment():
    body=accounting();body['facts']['us-gaap']['PaymentsToAcquirePropertyPlantAndEquipment']['units']['USD'][0]['val']=-10
    assert next(r for r in model(body)['metrics'] if r['id']=='cfo_less_ppe')['state']=='BLOCKED'


def imported(service):
    original=service.http.fetch
    service.http.fetch=lambda cik,kind: json.dumps(accounting()).encode() if kind=='companyfacts' else original(cik,kind)
    service.enqueue('test-accounting-first',[CIK]); drain(service)
    return CompanyService(service)


def test_durable_idempotency_versions_and_no_writes_to_other_tables(service):
    s=imported(service)
    def counts():
        with s.engine.connect() as c:
            return {name:c.execute(select(func.count()).select_from(table)).scalar_one() for name,table in MODELS.metadata.tables.items() if not name.startswith('company_')}
    before=counts()
    first=s.build(CIK,'model-first-request')
    again=s.build(CIK,'model-first-request')
    same=s.build(CIK,'another-request-key')
    assert first==again==same
    assert CompanyService(service).get(CIK,first['id'])==first
    assert s.versions(CIK)['total']==1 and counts()==before
    with pytest.raises(ValueError,match='IDEMPOTENCY_CONFLICT'):s.build('2','model-first-request')


def test_receipt_and_publication_cutoffs_and_future_rejection(service):
    s=imported(service)
    with pytest.raises(ValueError,match='NO_FINANCIAL_DATA'):
        s.build(CIK,'before-receipt-key',datetime(2026,1,1,tzinfo=timezone.utc))
    with pytest.raises(ValueError,match='INVALID_KNOWLEDGE_CUTOFF'):
        s.build(CIK,'future-model-key',service.data.clock()+timedelta(days=1))
    with pytest.raises(ValueError,match='INVALID_KNOWLEDGE_CUTOFF'):
        s.build(CIK,'naive-model-key',datetime(2026,9,1))
    facts,source=s.source(s.engine.connect(),CIK,service.data.clock())
    assert all(datetime.fromisoformat(f['published_bound'])<=service.data.clock() for f in facts)


def test_changed_report_creates_new_version_preserving_old(service):
    s=imported(service); first=s.build(CIK,'model-before-change')
    revised=accounting(); revised['facts']['us-gaap']['NetIncomeLoss']['units']['USD'][0]['val']=22
    original=service.http.fetch
    service.http.fetch=lambda cik,kind: json.dumps(revised).encode() if kind=='companyfacts' else original(cik,kind)
    service.enqueue('test-accounting-revised',[CIK]);drain(service)
    second=s.build(CIK,'model-after-change')
    assert second['version']==2 and second['previous_id']==first['id']
    assert second['payload']['update']['reason']=='REPORTED_VALUES_CHANGED'
    assert second['payload']['update']['changes'][0]['before']['value']=='20'
    assert s.get(CIK,first['id'])==first
    assert s.build(CIK,'cutoff-before-change',datetime.fromisoformat(first['as_of']))['id']==first['id']


def test_disabled_source_prevents_model_reads_and_writes(service):
    s=imported(service); m=s.build(CIK,'before-disable-key')
    service.data.settings=service.data.settings.model_copy(update={'data_public_enabled':False})
    with pytest.raises(PermissionError):s.get(CIK,m['id'])
    with pytest.raises(PermissionError):s.build(CIK,'after-disable-key')


def test_http_auth_scope_input_and_orders(client):
    path='/api/universe/issuers/0000000001/models'
    assert client.post(path,json={}).status_code==403
    headers={'X-HQ-Universe':'1','Idempotency-Key':'test-api-model-request'}
    assert client.post(path,json={},headers={**headers,'Origin':'https://evil.invalid'}).status_code==403
    assert client.post(path,json={'code':'print(1)'},headers=headers).status_code==422
    assert client.get(path).json()['total']==0
    assert client.post('/api/orders',json={}).status_code==403
