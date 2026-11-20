"""Synthetic accounting / queue evidence. No external network or personal DB."""
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
import httpx
import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.database import Base, DataQuota, InstrumentRegistry
from app.data_config import DataSettings
from app.data_service import DataService
from app.data_http import FetchError
from app.sec_http import SecHttp, source_url, MAX_BYTES
from app.sec_normalize import parse_companyfacts, parse_submissions, annual_view, document_url
from app.sec_service import SecService
from app.sec_store import FACTS, SNAPSHOTS, RECEIPTS, TASKS
from app.universe_service import UniverseService

NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
CIK = '0000000001'
ACCN = '0000000001-26-000001'


def companyfacts(value=123, accn=ACCN, filed='2026-09-01', fiscal_end='2026-06-30'):
    facts = {}
    start = str(int(fiscal_end[:4]) - 1) + fiscal_end[4:]
    for concept in ('RevenueFromContractWithCustomerExcludingAssessedTax', 'NetIncomeLoss', 'Assets',
                    'StockholdersEquity', 'CashAndCashEquivalentsAtCarryingValue', 'NetCashProvidedByUsedInOperatingActivities'):
        row = dict(end=fiscal_end, val=value, accn=accn, filed=filed, form='10-K', fy=2026, fp='FY')
        if concept in ('RevenueFromContractWithCustomerExcludingAssessedTax', 'NetIncomeLoss', 'NetCashProvidedByUsedInOperatingActivities'):
            row['start'] = start
        facts[concept] = {'units': {'USD': [row]}}
    return dict(cik=1, entityName='TEST ONLY', facts={'us-gaap': facts})


def submissions():
    recent = dict(accessionNumber=[ACCN], filingDate=['2026-09-01'], reportDate=['2026-06-30'],
                  form=['10-K'], primaryDocument=['test.htm'], acceptanceDateTime=['2026-09-01T13:00:00Z'])
    return dict(cik=1, name='TEST ONLY', fiscalYearEnd='0630', sic='1234', sicDescription='TEST',
                filings=dict(recent=recent, files=[dict(name='CIK0000000001-submissions-001.json', filingFrom='2010-01-01', filingTo='2020-01-01')]))


@pytest.fixture
def service(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'sec.db'))
    Base.metadata.create_all(engine)
    clock = [NOW]
    settings = DataSettings(_env_file=None, sec_contact='TEST ONLY test@example.invalid', data_auto_refresh_enabled=False)
    data = DataService(engine, settings, clock=lambda: clock[0])
    catalogue = UniverseService(data, SimpleNamespace(fetch_sec=lambda: json.dumps(dict(fields=['cik', 'name', 'ticker', 'exchange'],
        data=[[1, 'TEST ONLY', 'TEST', 'Nasdaq']])).encode()))
    catalogue.sync('test-catalogue')
    clock[0] += timedelta(seconds=2)
    calls = []
    def fetch(cik, kind):
        calls.append((cik, kind))
        return json.dumps(companyfacts() if kind == 'companyfacts' else submissions()).encode()
    result = SecService(data, SimpleNamespace(fetch=fetch), tmp_path / 'raw')
    result.clock = clock
    result.calls = calls
    return result


def drain(service):
    for _ in range(8):
        service.step()
        service.clock[0] += timedelta(seconds=2)


def test_normalization_preserves_alternatives_units_fiscal_context_and_precision():
    body = companyfacts()
    row = body['facts']['us-gaap']['RevenueFromContractWithCustomerExcludingAssessedTax']['units']['USD'][0]
    row['val'] = Decimal('123.1234567890123456789')
    row['fy'] = 2027  # Filing context is not the year of a comparative period.
    facts, meta = parse_companyfacts(body, CIK)
    view = annual_view(facts)
    assert view['end'] == '2026-06-30' and view['core_available'] == 6 and view['core_total'] == 6
    assert view['metrics'][0]['fact']['value'] == '123.1234567890123456789'
    assert view['metrics'][0]['fact']['filing_fiscal_year'] == 2027
    assert meta['mapped_metrics'] == 6
    body['facts']['us-gaap']['Assets']['units']['EUR'] = body['facts']['us-gaap']['Assets']['units']['USD']
    facts, _ = parse_companyfacts(body, CIK)
    assert {f['unit'] for f in facts} == {'USD', 'EUR'}


def test_annual_view_never_fills_gaps_from_another_filing_or_fiscal_period():
    older, _ = parse_companyfacts(companyfacts(accn='0000000001-25-000001', filed='2025-09-01', fiscal_end='2025-06-30'), CIK)
    body = companyfacts()
    del body['facts']['us-gaap']['Assets']
    recent, _ = parse_companyfacts(body, CIK)
    view = annual_view(older + recent)
    assert view['core_available'] == 5 and view['state'] == 'PARTIAL'
    assert next(m for m in view['metrics'] if m['metric'] == 'assets')['fact'] is None
    assert all(m['fact']['accession'] == ACCN for m in view['metrics'] if m['fact'])


def test_conflicting_values_and_reporting_currencies_are_not_arbitrarily_chosen():
    body = companyfacts()
    assets = body['facts']['us-gaap']['Assets']['units']['USD']
    assets.append({**assets[0], 'val': 321})
    facts, _ = parse_companyfacts(body, CIK)
    view = annual_view(facts)
    assert next(m for m in view['metrics'] if m['metric'] == 'assets')['state'] == 'CONFLICT'
    revenue = body['facts']['us-gaap']['RevenueFromContractWithCustomerExcludingAssessedTax']['units']
    revenue['EUR'] = revenue['USD']
    facts, _ = parse_companyfacts(body, CIK)
    assert annual_view(facts)['state'] == 'AMBIGUOUS_CURRENCY'
    assert annual_view(facts)['currency'] is None


def test_submissions_validate_parallel_arrays_and_keep_document_provenance():
    body = submissions()
    docs, profile = parse_submissions(body, CIK)
    assert docs[0]['url'] == 'https://www.sec.gov/Archives/edgar/data/1/000000000126000001/test.htm'
    assert docs[0]['accepted_at'] == '2026-09-01T13:00:00+00:00'
    assert not profile['complete_history'] and profile['older_files']
    assert document_url(CIK, ACCN, '../../evil').endswith(ACCN + '-index.html')
    body['filings']['recent']['form'] = []
    with pytest.raises(ValueError, match='INVALID_FILINGS'):
        parse_submissions(body, CIK)
    with pytest.raises(ValueError, match='ISSUER_MISMATCH'):
        parse_companyfacts(companyfacts(), '0000000002')
    body = companyfacts(float('nan'))
    with pytest.raises(ValueError, match='INVALID_NUMBER'):
        parse_companyfacts(body, CIK)


def test_real_shape_bank_volume_and_malformed_legacy_period_are_quarantined():
    body = submissions()
    recent = body['filings']['recent']
    for key, values in recent.items():
        recent[key] = values * 27000
    recent['form'] = ['10-K'] + ['424B2'] * 26999
    docs, profile = parse_submissions(body, CIK)
    assert len(docs) == 1 and profile['recent_filing_count'] == 27000
    body = companyfacts()
    row = body['facts']['us-gaap']['NetIncomeLoss']['units']['USD'][0]
    del row['start']
    facts, _ = parse_companyfacts(body, CIK)
    quarantined = next(f for f in facts if f['metric'] == 'net_income')
    assert quarantined['quality_flags'] == ['PERIOD_TYPE_MISMATCH']
    assert annual_view(facts)['core_available'] == 5


def test_queue_receipts_and_immutable_snapshots_survive_repeated_imports(service):
    first = service.enqueue('test-first', [CIK])
    assert first['total'] == 2
    assert service.enqueue('test-first', [CIK])['id'] == first['id']
    drain(service)
    assert service.store.job('test-first')['state'] == 'SUCCEEDED'
    before = service.store.financials(CIK, service.clock[0])
    assert before['annual']['core_available'] == 6 and before['documents']['total'] == 1
    service.enqueue('test-second', [CIK])
    drain(service)
    summary = service.summary()
    assert summary['counts']['snapshots'] == 2 and summary['counts']['receipts'] == 4
    with service.data.engine.connect() as c:
        assert c.execute(select(func.count()).select_from(FACTS)).scalar_one() == 6
    with Session(service.data.engine) as s:
        assert InstrumentRegistry(s).list() == []
    assert len(list(service.raw_root.glob('*.json.gz'))) == 2
    assert 'test@example' not in json.dumps(summary)


def test_asof_hides_future_downloads_and_publications_including_document_metadata(service):
    service.enqueue('test-old', [CIK])
    drain(service)
    old_at = service.clock[0]
    service.clock[0] += timedelta(days=1)
    revised = companyfacts(456, accn='0000000001-26-000002', filed='2026-10-01')
    revised['facts']['us-gaap']['Assets']['units']['USD'] += companyfacts()['facts']['us-gaap']['Assets']['units']['USD']
    service.http.fetch = lambda cik, kind: json.dumps(revised if kind == 'companyfacts' else submissions()).encode()
    service.enqueue('test-revised', [CIK])
    drain(service)
    current = service.store.financials(CIK, service.clock[0])
    old = service.store.financials(CIK, old_at)
    assert old['annual']['metrics'][0]['fact']['value'] == '123'
    assert current['annual']['metrics'][0]['fact']['value'] == '456'
    assert current['coverage']['changed_value_groups'] == 1
    assert service.store.financials(CIK, NOW - timedelta(days=1))['annual'] is None
    future = companyfacts(999, filed='2027-01-01')
    service.http.fetch = lambda cik, kind: json.dumps(future if kind == 'companyfacts' else submissions()).encode()
    service.enqueue('test-future', [CIK]); drain(service)
    assert service.store.financials(CIK, service.clock[0])['annual'] is None


def test_interrupted_task_resumes_with_fencing_and_single_active_batch(service):
    service.enqueue('test-recovery', [CIK])
    task = service.store.claim(service.clock[0])
    assert service.store.claim(service.clock[0])['kind'] == 'companyfacts'
    with pytest.raises(ValueError, match='IMPORT_ALREADY_ACTIVE'):
        service.enqueue('test-parallel', [CIK])
    service.clock[0] += timedelta(minutes=4)
    recovered = service.store.claim(service.clock[0])
    assert recovered['id'] == task['id'] and recovered['token'] != task['token']
    rows, metadata = parse_submissions(submissions(), CIK)
    assert service.store.accept(task, rows, metadata, 'x' * 64, source_url(CIK, task['kind']), service.clock[0], service.clock[0]) is False
    service.clock[0] += timedelta(minutes=4)
    drain(service)
    assert service.store.job('test-recovery')['state'] == 'SUCCEEDED'


def test_pause_resume_cancel_and_unidentified_issuer(service):
    with pytest.raises(ValueError, match='ISSUER_NOT_IDENTIFIED'):
        service.enqueue('test-unknown', ['0000000002'])
    service.enqueue('test-controls', [CIK])
    service.store.control('test-controls', 'pause', service.clock[0])
    assert service.step() is False and service.calls == []
    service.store.control('test-controls', 'resume', service.clock[0])
    task = service.store.claim(service.clock[0])
    service.store.control('test-controls', 'cancel', service.clock[0])
    rows, meta = parse_submissions(submissions(), CIK)
    assert not service.store.accept(task, rows, meta, 'x'*64, source_url(CIK, 'submissions'), service.clock[0], service.clock[0])
    assert service.store.job('test-controls')['state'] == 'CANCELLED'


def test_shared_throttle_does_not_consume_attempts_and_retry_after_is_durable(service):
    service.enqueue('test-throttle', [CIK])
    assert service.step()
    assert not service.step()
    with service.data.engine.connect() as c:
        task = c.execute(select(TASKS).where(TASKS.c.kind == 'companyfacts')).mappings().one()
        assert task['attempts'] == 0 and task['state'] == 'WAITING'
    service.clock[0] += timedelta(seconds=2)
    def limited(*_):
        raise FetchError('RATE_LIMITED', 429, 120)
    service.http.fetch = limited
    assert service.step()
    with Session(service.data.engine) as s:
        assert datetime.fromisoformat(s.get(DataQuota, 'SEC').blocked_until) >= service.clock[0] + timedelta(seconds=120)
    service.clock[0] += timedelta(seconds=60)
    assert not service.step()


def test_invalid_response_is_terminal_and_previous_snapshot_is_retained(service):
    service.enqueue('test-good', [CIK]); drain(service)
    original = service.summary()['counts']['snapshots']
    service.http.fetch = lambda *_: b'{"cik": 2}'
    service.enqueue('test-bad', [CIK]); drain(service)
    assert service.store.job('test-bad')['state'] == 'PARTIAL'
    assert service.summary()['counts']['snapshots'] == original
    assert service.store.financials(CIK, service.clock[0])['annual']['core_available'] == 6


def test_network_failures_exhaust_three_attempts_and_can_be_retried(service):
    def offline(*_):
        raise FetchError('OFFLINE')
    service.http.fetch = offline
    service.enqueue('test-network', [CIK])
    for _ in range(7):
        service.step(); service.clock[0] += timedelta(minutes=1)
    assert service.store.job('test-network')['counts']['FAILED'] == 2
    assert service.store.job('test-network')['state'] == 'PARTIAL'
    service.store.control('test-network', 'resume', service.clock[0])
    assert service.store.job('test-network')['counts']['PENDING'] == 2


def test_provider_rejection_pauses_remaining_issuers_without_repeated_requests(service):
    def denied(*_):
        raise FetchError('RIGHTS_RESTRICTED', 403)
    service.http.fetch = denied
    service.enqueue('test-denied', [CIK])
    service.step()
    assert service.store.job('test-denied')['state'] == 'PAUSED'
    service.clock[0] += timedelta(minutes=3)
    assert not service.step()
    assert service.store.job('test-denied')['counts']['PENDING'] == 1


def test_ifrs_mappings_preserve_reporting_currency_and_parent_scope():
    body = companyfacts()
    mapping = {'RevenueFromContractWithCustomerExcludingAssessedTax':'Revenue', 'NetIncomeLoss':'ProfitLossAttributableToOwnersOfParent',
        'Assets':'Assets', 'StockholdersEquity':'EquityAttributableToOwnersOfParent', 'CashAndCashEquivalentsAtCarryingValue':'CashAndCashEquivalents',
        'NetCashProvidedByUsedInOperatingActivities':'CashFlowsFromUsedInOperatingActivities'}
    body['facts'] = {'ifrs-full': {mapping[k]: {'units': {'EUR': [{**r, 'form':'20-F'} for r in value['units']['USD']]}}
                                  for k, value in body['facts']['us-gaap'].items()}}
    facts, _ = parse_companyfacts(body, CIK)
    view = annual_view(facts)
    assert view['currency'] == 'EUR' and view['form'] == '20-F' and view['core_available'] == 6
    assert all(m['fact']['taxonomy'] == 'ifrs-full' for m in view['metrics'] if m['fact'])


def test_fixed_sec_transport_rejects_paths_redirects_and_oversized_payloads():
    requests = []
    def redirect(request):
        requests.append(request)
        return httpx.Response(302, headers={'Location': 'https://evil.invalid'})
    http = SecHttp(DataSettings(_env_file=None, sec_contact='TEST test@example.invalid'),
        httpx.MockTransport(redirect), resolver=lambda _: None)
    with pytest.raises(ValueError):
        http.fetch('../secret', 'submissions')
    with pytest.raises(ValueError):
        http.fetch(CIK, 'orders')
    with pytest.raises(FetchError):
        http.fetch(CIK, 'submissions')
    assert len(requests) == 1 and requests[0].method == 'GET'
    assert str(requests[0].url) == source_url(CIK, 'submissions')
    http.transport = httpx.MockTransport(lambda _: httpx.Response(200, content=b'x' * (MAX_BYTES + 1)))
    with pytest.raises(FetchError) as error:
        http.fetch(CIK, 'companyfacts')
    assert error.value.state == 'INVALID_PAYLOAD'


def test_api_rejects_cross_origin_bad_limits_arbitrary_endpoints_and_orders(client):
    api = '/api/universe'
    assert client.get(api + '/financials/summary').status_code == 200
    headers = {'X-HQ-Universe': '1', 'Origin': 'https://evil.invalid', 'Idempotency-Key': 'test-api'}
    assert client.post(api + '/financials/jobs', headers=headers, json={}).status_code == 403
    headers['Origin'] = 'http://127.0.0.1:5173'
    assert client.post(api + '/financials/jobs', headers=headers, json={'ciks': ['../secret']}).status_code == 422
    assert client.post(api + '/financials/jobs', headers=headers, json={'url': 'https://evil.invalid'}).status_code == 422
    assert client.get(api + '/issuers/' + CIK + '/financials?as_of=2026-01-01').status_code == 422
    assert client.get(api + '/issuers/' + CIK + '/documents?limit=101').status_code == 422
    assert client.get(api + '/issuers/' + CIK + '/facts?metric=madeup').status_code == 422
    assert client.post('/api/orders').status_code == 403
