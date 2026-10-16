"""TEST_ONLY financial fixtures: temporary SQLite; never seed user positions."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import json
import sqlite3

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.config import ROOT
from app.database import create_db_engine
from app.main import create_app
from app.portfolio_domain import PortfolioEvent as E, rebuild, money
from app.portfolio_store import initialize_master, append_event, read_journal
from app.portfolio_service import PortfolioService
from app.portfolio_valuation import value_portfolio
from app.portfolio_performance import performance, xirr
from app.data_contracts import Observation, Rights

NOW = datetime(2026, 10, 16, tzinfo=timezone.utc)


def event(kind, ref, **kwargs):
    return E(kind=kind, source_ref=ref, actor='TEST_ONLY', occurred_at=NOW, **kwargs)


def seed():
    return event('DEPOSIT_VIRTUAL', 'TEST_DEPOSIT', amount='10000')


def quote(value='12', currency='EUR', kind='market_quote', **kwargs):
    return Observation(id='TEST_ONLY', provider='TEST_ONLY', access_id='TEST_ONLY', feed='TEST_FEED', series_id='TEST_INSTRUMENT',
        data_kind=kind, venue='TEST', asset_class='EQUITY', source_ref='https://example.org/TEST_ONLY', payload_hash='a'*64,
        observed_at=NOW, received_at=NOW, period='TEST_ONLY', period_precision='instant', currency=currency,
        unit=kwargs.pop('unit', currency), value=value, stale_after_seconds=60,
        rights=Rights(license='TEST_ONLY', source='https://example.org/TEST_ONLY', checked_at=NOW,
            access_allowed=True, display_allowed=True, storage_allowed=True, redistribution_allowed=True, attribution='TEST_ONLY'), **kwargs)


def buy(ref='b', **kwargs):
    return event('FILL_BUY', ref, instrument='TEST_INSTRUMENT', qty=kwargs.pop('qty', '10'), price=kwargs.pop('price', '10'), **kwargs)


def test_seed_restart_concurrent_idempotency_and_balanced_entries(migrated):
    engine = create_db_engine(migrated.database_url)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(lambda _: initialize_master(engine), range(2))) == 1
    assert initialize_master(engine) is False
    for _ in range(2):
        with TestClient(create_app(migrated), base_url='http://127.0.0.1') as client:
            s = client.get('/api/portfolio/master/summary').json()
            assert (s['nav_eur'], s['cash_eur'], s['market_value_eur'], s['liabilities_eur'], s['positions_count'], s['cumulative_return_pct']) == ('10000.00', '10000.00', '0.00', '0.00', 0, '0')
            assert s['events_count'] == 1 and s['ledger_status'] == 'VERIFIED_APPEND_ONLY'
            assert client.get('/api/portfolio/master/nav/history').json()['total'] == 1
            entries = client.get('/api/portfolio/master/ledger').json()['items'][0]['entries']
            assert sum(D(e['debit']) for e in entries) == sum(D(e['credit']) for e in entries) == 10000
            assert s['performance']['twr_pct'] is None and s['performance']['daily_return_pct'] is None
    engine.dispose()


def test_fifo_partial_sales_fees_and_rebuild():
    events = [seed(), buy('first', qty='10', price='10', fee='2'), buy('second', qty='10', price='20', fee='4'),
        event('FILL_SELL', 'sale', instrument='TEST_INSTRUMENT', qty='15', price='30', fee='3')]
    state = rebuild(events)
    assert state.cash['EUR'] == D('10141')
    assert [l.qty_remaining for l in state.lots] == [0, 5]
    assert state.lots[1].cost_eur == D('102')
    assert state.realized_pnl_eur == D('243')  # 450-3-102-102, buy fees capitalized exactly once
    assert [c['lot'] for c in state.consumptions] == ['first', 'second']
    assert rebuild([E.model_validate_json(e.model_dump_json()) for e in events]) == state
    value = value_portfolio(state, {'TEST_INSTRUMENT': quote('30')}, {}, NOW)
    assert value['nav_eur'] == '10291.00' and value['total_pnl_eur'] == '291.00'
    assert value['unrealized_pnl_eur'] == '48.00'  # NAV never adds P&L twice


def test_fx_cost_basis_cash_and_value_are_reproducible():
    events = [seed(), event('FX_CONVERSION', 'fx', amount='1000', target_currency='USD', target_fx='.8'),
        buy(currency='USD', fx='.8', price='100'), event('FILL_SELL', 'sell', instrument='TEST_INSTRUMENT', currency='USD', fx='.9', qty='5', price='120')]
    state = rebuild(events)
    assert state.cash['EUR'] == 9000 and state.cash['USD'] == 850
    assert state.lots[0].cost_eur == 400 and state.realized_pnl_eur == 140
    result = value_portfolio(state, {'TEST_INSTRUMENT': quote('120', 'USD')}, {'USD': quote('1.25', 'USD', 'fx_reference', unit='USD/EUR')}, NOW)
    assert result['nav_eur'] == '10160.00'
    assert result['unrealized_pnl_eur'] == '80.00'
    assert len(result['provenance']) >= 2
    assert result['positions'][0]['valuation_fx'] == '0.8'


@pytest.mark.parametrize('kind', ['DIVIDEND', 'COUPON'])
def test_income_increases_cash_not_quantity(kind):
    state = rebuild([seed(), buy(), event(kind, 'income', amount='5')])
    assert state.cash['EUR'] == 9905 and state.lots[0].qty_remaining == 10
    assert state.income_eur == 5


def test_coupon_settles_accrual_without_double_income():
    accrual = event('INTEREST_ACCRUAL', 'accrual', amount='8')
    a = rebuild([seed(), accrual])
    b = rebuild([seed(), accrual, event('COUPON', 'coupon', amount='8', settles_accrual=True)])
    assert value_portfolio(a, {}, {}, NOW)['nav_eur'] == value_portfolio(b, {}, {}, NOW)['nav_eur'] == '10008.00'
    assert b.accruals['EUR'] == 0 and b.income_eur == 8
    with pytest.raises(ValueError):
        rebuild([seed(), event('COUPON', 'bad', amount='9', settles_accrual=True)])


def test_split_merger_redemption_no_value_created():
    state = rebuild([seed(), buy(), event('SPLIT', 'split', instrument='TEST_INSTRUMENT', ratio='2'),
        event('MERGER', 'merger', instrument='TEST_INSTRUMENT', target_instrument='TEST_SUCCESSOR', ratio='.5')])
    assert state.lots[0].qty_remaining == 10 and state.lots[0].cost_eur == 100
    assert state.lots[0].instrument == 'TEST_SUCCESSOR'
    redeemed = rebuild([seed(), buy(), event('BOND_REDEMPTION', 'redeem', instrument='TEST_INSTRUMENT', qty='10', price='10')])
    assert redeemed.cash['EUR'] == 10000 and redeemed.lots[0].qty_remaining == 0 and redeemed.realized_pnl_eur == 0


def test_fee_and_reservation_never_overdraw():
    reserve = event('ORDER_RESERVED', 'r', amount='9500')
    state = rebuild([seed(), reserve, buy(qty='10', price='10', reservation_ref='r'), event('FEE', 'fee', amount='5')])
    assert state.cash['EUR'] == 9895 and state.reserved('EUR') == 9400 and state.fees_eur == 5
    with pytest.raises(ValueError):
        rebuild([seed(), reserve, buy(qty='100', price='10')])
    with pytest.raises(ValueError):
        rebuild([seed(), event('FEE', 'fee', amount='10001')])
    with pytest.raises(ValueError):
        rebuild([seed(), buy(), event('FILL_SELL', 'short', instrument='TEST_INSTRUMENT', qty='11', price='10')])


@pytest.mark.parametrize('bad', [0.1, True, 'NaN', 'Infinity', '1e30', '0.00000000000000000000000001'])
def test_no_float_or_invalid_decimal(bad):
    with pytest.raises(ValueError):
        event('DEPOSIT_VIRTUAL', 'bad', amount=bad)


def test_half_even_and_exact_quantity_residual():
    assert money(D('1.005')) == '1.00' and money(D('1.015')) == '1.02'
    events = [seed(), buy(qty='3', price='10', fee='1')]
    for i in range(3):
        events.append(event('FILL_SELL', f'sale{i}', instrument='TEST_INSTRUMENT', qty='1', price='11'))
    state = rebuild(events)
    assert state.lots[0].qty_remaining == state.lots[0].cost_eur == state.lots[0].fee_native == 0
    assert money(state.realized_pnl_eur) == '2.00'


def test_missing_quote_is_null_and_stale_is_explicit():
    state = rebuild([seed(), buy()])
    absent = value_portfolio(state, {}, {}, NOW)
    assert absent['valuation_status'] == 'NO_DATA' and absent['nav_eur'] is None and absent['market_value_eur'] is None
    stale = value_portfolio(state, {'TEST_INSTRUMENT': quote()}, {}, NOW+timedelta(seconds=61))
    assert stale['valuation_status'] == 'STALE' and stale['nav_eur'] == '10020.00'
    denied = quote().model_copy(update={'rights': quote().rights.model_copy(update={'display_allowed':False})})
    assert value_portfolio(state, {'TEST_INSTRUMENT':denied}, {}, NOW)['nav_eur'] is None
    wrong_currency = value_portfolio(state, {'TEST_INSTRUMENT':quote(currency='USD')}, {}, NOW)
    assert wrong_currency['valuation_status'] == 'NO_DATA'


def test_fx_missing_stale_direction_and_estimate():
    state = rebuild([seed(), event('FX_CONVERSION', 'fx', amount='1000', target_currency='USD', target_fx='.8')])
    assert value_portfolio(state, {}, {}, NOW)['cash_eur'] is None
    rate = quote('1.25', 'USD', 'fx_reference', unit='USD/EUR')
    assert value_portfolio(state, {}, {'USD':rate}, NOW+timedelta(minutes=2))['valuation_status'] == 'STALE'
    assert value_portfolio(state, {}, {'USD':rate.model_copy(update={'unit':'EUR/USD'})}, NOW)['nav_eur'] is None
    estimated = rate.model_copy(update={'quality_flags':('ESTIMATED',)})
    assert value_portfolio(state, {}, {'USD':estimated}, NOW)['valuation_status'] == 'ESTIMATED'


def test_journal_immutable_idempotent_and_master_guard(migrated):
    engine = create_db_engine(migrated.database_url)
    initialize_master(engine)
    with pytest.raises(ValueError, match='only'):
        append_event(engine, buy())
    assert append_event(engine, seed(), 'TEST_ONLY')
    assert append_event(engine, seed(), 'TEST_ONLY') is False
    with pytest.raises(ValueError, match='Idempotency'):
        append_event(engine, seed().model_copy(update={'amount':D('20000')}), 'TEST_ONLY')
    for table in ('ledger_events', 'ledger_entries', 'portfolios'):
        for action in (f'DELETE FROM {table}', f'UPDATE {table} SET '+('id=id' if table!='ledger_events' else 'sequence=sequence')):
            with pytest.raises(IntegrityError), engine.begin() as connection:
                connection.execute(text(action))
    with engine.connect() as connection:
        assert read_journal(connection)[1].cash['EUR'] == 10000  # TEST_ONLY deposit never mixes with MASTER
    engine.dispose()


def test_hash_or_posting_corruption_detected(migrated):
    engine = create_db_engine(migrated.database_url)
    initialize_master(engine)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO ledger_entries(event_id,account,currency,debit,credit) VALUES(1,'TEST_TAMPER','EUR','1','0')"))
    with pytest.raises(ValueError, match='postings'), engine.connect() as connection:
        read_journal(connection)
    engine.dispose()


def test_api_readonly_pagination_and_separation(client):
    routes = ['/api/portfolio/master/'+p for p in ('summary','positions','ledger','nav/history','performance')]
    for route in routes:
        assert client.get(route).status_code == 200
        for method in ('post','put','patch','delete'):
            assert getattr(client, method)(route).status_code == 405
    assert client.get('/api/portfolio/master/ledger?limit=0').status_code == 422
    assert client.get('/api/portfolio/master/ledger?offset=1').json()['items'] == []
    assert client.get('/api/portfolio/master/positions').json()['items'] == []
    assert client.get('/api/markets/watchlist').json()['items'] == []
    assert client.post('/api/orders', json={'mode':'LIVE'}).status_code == 403


def test_snapshots_restore_and_populated_downgrade_guard(client, migrated, tmp_path):
    before = client.get('/api/portfolio/master/summary').json()
    client.app.state.portfolio.snapshot()
    with client.app.state.engine.connect() as c:
        with pytest.raises(IntegrityError):
            c.execute(text('DELETE FROM valuation_snapshots'))
    path = str(tmp_path/'test.db')
    with sqlite3.connect(path) as source, sqlite3.connect(tmp_path/'restore.db') as restored:
        source.backup(restored)
        assert restored.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    restored_engine = create_db_engine('sqlite:///'+(tmp_path/'restore.db').as_posix())
    with restored_engine.connect() as c:
        events, state, head = read_journal(c)
        assert state.cash['EUR'] == 10000 and len(events) == 1 and head == before['ledger_hash']
    restored_engine.dispose()
    with pytest.raises(RuntimeError, match='immutable'):
        command.downgrade(Config(str(ROOT/'alembic.ini')), '0002_data')


def test_performance_requires_history_and_excludes_deposit():
    events = [seed()]
    summary = value_portfolio(rebuild(events), {}, {}, NOW)
    assert summary['cumulative_return_pct'] == '0'
    assert performance(summary, [summary], events)['twr_pct'] is None
    rows = [{**summary, 'as_of':(NOW+timedelta(days=i)).isoformat(), 'nav_eur':v} for i,v in enumerate(('10000','11000','9900'))]
    result = performance(rows[-1], rows, events)
    assert D(result['twr_pct']) == -1 and D(result['max_drawdown_pct']) == -10 and D(result['daily_return_pct']) == -10
    assert result['mwr_xirr_pct'] is None
    assert abs(xirr([(NOW,D('-10000')), (NOW+timedelta(days=365),D('11000'))])-D('10')) < D('1e-20')
    assert xirr([(NOW,D('-10000')), (NOW+timedelta(days=365),D('11000')), (NOW+timedelta(days=730),D('-100'))]) is None


def test_no_negative_reconciliation_or_utc_backdating():
    with pytest.raises(ValueError):
        event('RECONCILIATION_ADJUSTMENT','bad', amount='1')
    with pytest.raises(ValueError):
        rebuild([seed(), event('RECONCILIATION_ADJUSTMENT','bad',amount='-10001', evidence='TEST_ONLY')])
    with pytest.raises(ValueError):
        rebuild([seed(), buy().model_copy(update={'occurred_at':NOW-timedelta(seconds=1)})])
    with pytest.raises(ValueError):
        rebuild([seed(), seed()])


def test_price_units_are_not_percent_par_or_yield():
    state = rebuild([seed(), buy()])
    for unit in ('percent of par', 'yield percent', 'index'):
        assert value_portfolio(state, {'TEST_INSTRUMENT':quote(unit=unit)}, {}, NOW)['nav_eur'] is None


def test_p2_cache_alias_capability_rights_and_feed_selection(client, monkeypatch):
    from dataclasses import replace
    from uuid import uuid4
    from sqlalchemy.orm import Session
    from app.contracts import Instrument, ProviderCapability
    from app.database import InstrumentRecord, InstrumentAlias, DataRecord
    from app.data_contracts import DataResult
    from app.data_catalog import CATALOG
    from app.data_service import cache_key
    service = client.app.state.portfolio
    monkeypatch.setattr(client.app.state.data, 'clock', lambda: NOW)
    # Strictly TEST_ONLY cache, no network; never counted as a real connection in delivery.
    source = replace(CATALOG['A18'], rights=quote().rights)
    monkeypatch.setitem(CATALOG, 'A18', source)
    observation = quote('123', 'USD').model_copy(update={'access_id':'A18','provider':source.provider,'feed':source.feed,'venue':source.venue,'series_id':'TEST_ONLY_SYMBOL'})
    instrument = Instrument(id=uuid4(),symbol='TEST_ONLY_SYMBOL',venue=source.venue,currency='USD',asset_class='EQUITY',provider_capabilities=(ProviderCapability(provider=source.provider, feed=source.feed, research=True, valuation=False, checked_at=NOW, license='TEST_ONLY',source='https://example.org/TEST_ONLY',reason='TEST_ONLY'),))
    result = DataResult(access_id='A18',state='AVAILABLE_VERIFIED',reason='TEST_ONLY',real_connection=True,observations=(observation,))
    with Session(service.engine) as s, s.begin():
        s.add(InstrumentRecord(id=str(instrument.id),symbol=instrument.symbol,venue=instrument.venue,currency='USD',asset_class='EQUITY',payload=instrument.model_dump(mode='json')))
        s.flush()
        s.add(InstrumentAlias(id=str(uuid4()),instrument_id=str(instrument.id),provider=source.provider,symbol=instrument.symbol,venue=source.venue,currency='USD',source='https://example.org/TEST_ONLY',verified_at=NOW.isoformat()))
        s.add(DataRecord(key=cache_key(source),payload=result.model_dump(mode='json'),expires_at=(NOW+timedelta(minutes=1)).isoformat(),updated_at=NOW.isoformat()))
    assert service.inputs(NOW)[0] == {}  # research does NOT grant valuation
    assert service.markets()['items'][0]['daily_change_pct'] is None
    with Session(service.engine) as s, s.begin():
        row=s.get(InstrumentRecord,str(instrument.id))
        row.payload=instrument.model_copy(update={'provider_capabilities':(instrument.provider_capabilities[0].model_copy(update={'valuation':True}),)}).model_dump(mode='json')
    assert service.inputs(NOW)[0][str(instrument.id)].value == D('123')
    with Session(service.engine) as s, s.begin():
        row=s.get(DataRecord,cache_key(source))
        row.payload=result.model_copy(update={'observations':(observation.model_copy(update={'feed':'OTHER_FEED'}),)}).model_dump(mode='json')
    assert service.inputs(NOW)[0] == {}  # never silently mix IEX/SIP or other feeds
    monkeypatch.setitem(CATALOG,'A18',replace(source, rights=source.rights.model_copy(update={'redistribution_allowed':False})))
    assert service.markets()['items'] == []


def test_multiple_external_flows_do_not_fabricate_twr():
    events=[seed(),event('DEPOSIT_VIRTUAL','second',amount='100')]
    summary=value_portfolio(rebuild(events),{},{},NOW)
    assert summary['total_pnl_eur']=='0.00' and summary['cumulative_return_pct'] is None
    assert performance(summary,[summary]*4,events)['twr_pct'] is None


def test_integrity_failure_api_is_unavailable_not_plausible_nav(client):
    with client.app.state.engine.begin() as connection:
        connection.execute(text("INSERT INTO ledger_entries(event_id,account,currency,debit,credit) VALUES(1,'TEST_TAMPER','EUR','1','0')"))
    response=client.get('/api/portfolio/master/summary')
    assert response.status_code==503 and response.json()['code']=='LEDGER_INTEGRITY'


def test_foreign_accrual_fx_is_not_lost_when_coupon_settles():
    events=[seed(),event('INTEREST_ACCRUAL','interest',amount='10',currency='USD',fx='.8')]
    rate=quote('1.25','USD','fx_reference',unit='USD/EUR')
    before=value_portfolio(rebuild(events),{}, {'USD':rate}, NOW)
    assert before['nav_eur']=='10008.00' and before['fx_effect_eur']=='0.00'
    events.append(event('COUPON','coupon',amount='10',currency='USD',fx='1',settles_accrual=True))
    after=value_portfolio(rebuild(events),{}, {'USD':rate.model_copy(update={'value':D('1')})}, NOW)
    assert after['nav_eur']=='10010.00' and after['fx_effect_eur']=='2.00' and after['income_eur']=='8.00'


def test_external_demo_balance_never_enters_master(client):
    engine=client.app.state.engine
    append_event(engine,event('DEPOSIT_VIRTUAL','TEST_BROKER_DEMO',amount='100000'),portfolio='ALPACA_PAPER')
    summary=client.get('/api/portfolio/master/summary').json()
    assert summary['nav_eur']=='10000.00' and summary['events_count']==1
