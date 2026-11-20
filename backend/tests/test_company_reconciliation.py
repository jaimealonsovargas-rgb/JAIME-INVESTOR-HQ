import pytest
from sqlalchemy import update
from app.company_review import review_model
from app.sec_store import SNAPSHOTS
from test_company_models import accounting, model, imported
from test_sec_financials import service


def cash_body():
    body = accounting()
    tags = body['facts']['us-gaap']
    row = tags['NetCashProvidedByUsedInOperatingActivities']['units']['USD'][0]
    for tag, value in {
        'NetCashProvidedByUsedInInvestingActivities': -20,
        'NetCashProvidedByUsedInFinancingActivities': -15,
        'EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents': -5,
        'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect': 20,
    }.items():
        tags[tag] = {'units': {'USD': [{**row, 'val': value}]}}
    instant = {k:v for k,v in row.items() if k != 'start'}
    tags['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'] = {'units': {'USD': [
        {**instant, 'val': 120}, {**instant, 'end':'2025-06-30', 'val':100}]}}
    return body


def cash(m):
    return next(c for c in review_model(m)['checks'] if c['id'] == 'cash_roll_forward')


def test_cash_reconciles_signed_flows_and_opening_balance():
    result = cash(model(cash_body()))
    assert result['state'] == 'PASS'
    assert result['residual'] == result['reported_residual'] == '0'
    assert len(result['evidence_ids']) == 7


def test_cash_reports_discrepancy_without_tolerance():
    body = cash_body()
    body['facts']['us-gaap']['NetCashProvidedByUsedInInvestingActivities']['units']['USD'][0]['val'] = -21
    result = cash(model(body))
    assert result['state'] == 'FAIL' and result['residual'] == '1'


def test_missing_fx_does_not_become_zero():
    body = cash_body()
    del body['facts']['us-gaap']['EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents']
    assert cash(model(body))['state'] == 'BLOCKED'


def test_balance_review_does_not_round_away_small_residual():
    m = model(accounting())
    rows = {r['metric']:r['fact'] for r in m['annual']['metrics']}
    rows['assets']['value'] = '1000000000000000000000000000001'
    rows['liabilities']['value'] = '1000000000000000000000000000000'
    rows['equity_total']['value'] = '0'
    result = next(c for c in review_model(m)['checks'] if c['id'] == 'balance')
    assert result['state'] == 'FAIL' and result['residual'] == '1'


def test_declared_balance_total_does_not_replace_missing_components():
    body = accounting()
    tags = body['facts']['us-gaap']
    tags['LiabilitiesAndStockholdersEquity'] = tags['Assets']
    del tags['StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest']
    checks = {c['id']:c for c in review_model(model(body))['checks']}
    assert checks['balance_reported_total']['state'] == 'PASS'
    assert checks['balance']['state'] == 'BLOCKED'


@pytest.mark.parametrize('field,value', [('end','2025-06-29'), ('unit','EUR'), ('accession','0000000001-25-000001'), ('concept','CashAndCashEquivalentsAtCarryingValue')])
def test_opening_cash_scope_mismatch_abstains(field, value):
    m = model(cash_body())
    m['evidence'][m['opening_cash_id']][field] = value
    assert cash(m)['state'] == 'BLOCKED'


def test_conflicting_opening_balances_abstain():
    body = cash_body()
    rows = body['facts']['us-gaap']['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents']['units']['USD']
    rows.append({**rows[1], 'val':101})
    assert cash(model(body))['state'] == 'BLOCKED'


def test_saved_original_reparse_preserves_previous_models(service):
    s = imported(service)
    old = s.build('1', 'original-model')
    with s.engine.begin() as c:
        c.execute(update(SNAPSHOTS).values(parser_version='sec-financials-v1'))
    new = s.build('1', 'reparsed-model')
    assert new['payload']['source']['normalization'] == 'SAVED_ORIGINAL'
    assert s.get('1', old['id']) == old
    assert s.build('1', 'same-reparse')['id'] == new['id']
    # Both originals are content-addressed; corrupt specifically the companyfacts one.
    path = service.raw_root / (new['payload']['source']['payload_hash'] + '.json.gz')
    path.write_bytes(b'not gzip')
    with pytest.raises(ValueError, match='ORIGINAL_UNAVAILABLE'):
        s.build('1', 'corrupt-reparse')
