"""Offline adapter checks against disposable fixture archives only."""
from datetime import timedelta

import pytest
from sqlalchemy import insert, select, update

from app.admission_market import load_market_candidate
from app.market_store import RECEIPTS
from test_market_data import market, catalogue, history, drain


def complete(service, key='history-test'):
    ident = catalogue(service)
    service.http.real = True  # Synthetic fixture marks archive provenance for parser checks.
    history(service, ident, key)
    drain(service, key)
    return ident


def test_archive_candidate_and_read_only(market):
    ident = complete(market)
    calls = list(market.http.calls)
    result = load_market_candidate(market, ident, market.data.clock())
    assert result['source_errors'] == []
    assert result['version'] == 'admission-candidate-v1'
    assert result['bars'][0] == dict(session='2024-01-02', open='10', high='13', low='9', close='12', volume='100')
    assert len(result['sources']) == 4
    assert len(result['identity_hash']) == len(result['universe_hash']) == 64
    assert market.http.calls == calls
    assert load_market_candidate(market, ident, market.data.clock()) == result


def test_no_history_and_unknown_listing(market):
    ident = catalogue(market)
    result = load_market_candidate(market, ident, market.data.clock())
    assert result['source_errors'] == ['NO_HISTORY'] and result['bars'] == []
    assert result['start'] == result['end'] == market.data.clock().date().isoformat()
    with pytest.raises(KeyError):
        load_market_candidate(market, 'missing', market.data.clock())


def test_cutoff_and_latest_incomplete_do_not_fall_back(market):
    ident = complete(market)
    market.test_clock[0] += timedelta(seconds=1)
    history(market, ident, 'newer')
    result = load_market_candidate(market, ident, market.data.clock())
    assert 'IMPORT_INCOMPLETE' in result['source_errors'] and not result['bars']
    with pytest.raises(ValueError, match='INVALID_KNOWLEDGE_CUTOFF'):
        load_market_candidate(market, ident, market.data.clock().replace(tzinfo=None))
    with pytest.raises(ValueError, match='INVALID_KNOWLEDGE_CUTOFF'):
        load_market_candidate(market, ident, market.data.clock() + timedelta(seconds=1))


def test_raw_tamper_is_explicit(market):
    ident = complete(market)
    result = load_market_candidate(market, ident, market.data.clock())
    path = market.raw_root / (result['sources'][0]['hash'] + '.json.gz')
    path.write_bytes(b'corrupt fixture')
    result = load_market_candidate(market, ident, market.data.clock())
    assert result['source_errors'] == ['ORIGINAL_INTEGRITY_FAILED'] and not result['bars']


def test_disabled_and_future_receipt_block(market):
    ident = complete(market)
    cutoff = market.data.clock()
    with market.data.engine.begin() as connection:
        receipt = connection.execute(select(RECEIPTS).where(RECEIPTS.c.job_id == 'history-test')).mappings().first()
        connection.execute(update(RECEIPTS).where(RECEIPTS.c.id == receipt['id']).values(
            received_at=(cutoff + timedelta(days=1)).isoformat()))
    market.data.settings.alpaca_market_enabled = False
    result = load_market_candidate(market, ident, cutoff)
    assert 'SOURCE_DISABLED' in result['source_errors']
    assert 'HISTORY_AFTER_CUTOFF' in result['source_errors'] and result['bars'] == []


def test_receipt_bound_detects_overflow(market):
    ident = complete(market)
    with market.data.engine.begin() as connection:
        source = dict(connection.execute(select(RECEIPTS).where(
            RECEIPTS.c.job_id == 'history-test')).mappings().first())
        connection.execute(insert(RECEIPTS), [{**source, 'id': f'{i:064x}'} for i in range(100, 138)])
    result = load_market_candidate(market, ident, market.data.clock())
    assert 'DIAGNOSTIC_LIMIT' in result['source_errors'] and result['bars'] == []
