"""B3.1 exact arithmetic, temporal causality, durable trials and MASTER isolation."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import json
import threading

import pytest
from pydantic import ValidationError
from sqlalchemy import select, text, update, func

from app.database import create_db_engine
from app.quant_contracts import SyntheticDataset, ExperimentConfig
from app.quant_engine import run_reference
from app.quant_fixture import fixture, config
from app.quant_store import TrialRegistry, TRIALS, DATASETS, EVENTS, digest


def calculate(data=None, cfg=None):
    return run_reference(SyntheticDataset.model_validate(data or fixture()),
                         ExperimentConfig.model_validate(cfg or config()))


@pytest.fixture
def registry(migrated):
    engine = create_db_engine(migrated.database_url)
    store = TrialRegistry(engine)
    yield store
    engine.dispose()


def test_manual_trend_and_controls():
    result = calculate()
    # Day 2 close 12 > SMA(10,12)=11; BUY day 3 open12:83 shares,fee1,cash3.
    # Day 4 close8 < SMA(14,8)=11; SELL day5 open8:664 minus1,final cash666.
    assert [(f['side'], f['quantity'], f['price'], f['cash_after']) for f in result['fills']] == [
        ('BUY', 83, '12', '3.00'), ('SELL', 83, '8', '666.00')]
    assert [Decimal(p['equity']) for p in result['curve']] == [1000,1000,1165,667,666,666]
    assert Decimal(result['commission']) == 2
    assert Decimal(result['final_equity']) == 666
    assert Decimal(result['net_pnl']) == -334
    assert Decimal(result['return_fraction']) == Decimal('-.334')
    cash = calculate(cfg=config('CASH'))
    assert not cash['fills'] and Decimal(cash['final_equity']) == 1000
    held = calculate(cfg=config('BUY_HOLD'))
    assert held['final_shares'] == 99 and Decimal(held['final_cash']) == 9
    assert Decimal(held['final_equity']) == 1098 and len(held['fills']) == 1
    assert held['terminal_valuation'] == 'LAST_CLOSE_MARK_NO_LIQUIDATION'
    assert not result['execution_ready'] and result['acceptance'] == 'ENGINEERING_ONLY'


def test_costs_slippage_and_rounding_manual():
    cfg = config()
    cfg['costs'].update(commission_bps='100', slippage_bps='100')
    result = calculate(cfg=cfg)
    # BUY 81*12.12 =981.72, fee10.82, cash7.46. SELL81*7.92=641.52,fee7.42.
    assert result['fills'][0]['quantity'] == 81
    assert Decimal(result['fills'][0]['price']) == Decimal('12.12')
    assert Decimal(result['fills'][0]['cash_after']) == Decimal('7.46')
    assert Decimal(result['final_equity']) == Decimal('641.56')
    assert Decimal(result['commission']) == Decimal('18.24')
    assert Decimal(result['slippage_cost']) == Decimal('16.20')


def test_rounding_does_not_discard_an_affordable_share():
    cfg = config('BUY_HOLD')
    cfg.update(initial_cash='10.00')
    cfg['costs'].update(fixed_per_fill='0', commission_bps='1')
    result = calculate(cfg=cfg)
    assert result['fills'][0]['quantity'] == 1  # fee .001 rounds to .00
    assert Decimal(result['fills'][0]['cash_after']) == 0


def test_future_close_changes_cannot_change_past_fills_or_same_day_signal():
    data = fixture()
    original = calculate(data)
    data['bars'][2]['close'] = '500'
    changed = calculate(data)
    assert changed['fills'][0] == original['fills'][0]
    assert changed['decisions'][:3] == original['decisions'][:3]
    data = fixture()
    data['bars'][-1]['close'] = '900'
    assert calculate(data)['fills'] == original['fills']
    for fill in original['fills']:
        assert datetime.fromisoformat(fill['known_at']) < datetime.fromisoformat(fill['at'])


def test_decimal_context_and_repetition_do_not_change_result():
    result = calculate()
    with localcontext() as context:
        context.prec = 7
        context.rounding = 'ROUND_DOWN'
        assert calculate() == result


def test_all_in_cost_affordability_and_no_forced_final_fill():
    cfg = config('BUY_HOLD')
    cfg['initial_cash'] = '1'
    result = calculate(cfg=cfg)
    assert not result['fills'] and Decimal(result['final_cash']) == 1
    assert result['decisions'][0]['outcome'] == 'INSUFFICIENT_CASH_FOR_ONE_SHARE'


@pytest.mark.parametrize('mutation', ['duplicate','naive','early','late','negative','float','nan','real','extra'])
def test_bad_market_contracts_are_rejected(mutation):
    data = fixture()
    if mutation == 'duplicate': data['bars'][1] = deepcopy(data['bars'][0])
    if mutation == 'naive': data['bars'][0]['opens_at'] = '2000-01-03T09:00:00'
    if mutation == 'early': data['bars'][0]['available_at'] = data['bars'][0]['opens_at']
    if mutation == 'late': data['bars'][0]['available_at'] = data['bars'][1]['opens_at']
    if mutation == 'negative': data['bars'][0]['open'] = '-1'
    if mutation == 'float': data['bars'][0]['open'] = 10.1
    if mutation == 'nan': data['bars'][0]['open'] = 'NaN'
    if mutation == 'real': data['kind'] = 'MARKET_DATA'
    if mutation == 'extra': data['url'] = 'https://provider.invalid'
    with pytest.raises(ValidationError):
        SyntheticDataset.model_validate(data)


@pytest.mark.parametrize('field,value', [('family','CUSTOM_PYTHON'), ('lookback',True), ('lookback',253), ('code','print(1)')])
def test_genome_allowlist(field,value):
    cfg = config()
    cfg['genome'][field] = value
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(cfg)


def test_registered_before_engine_and_shared_snapshot(registry, monkeypatch):
    from app import quant_store
    original = quant_store.run_reference
    def observed(dataset, cfg):
        # A new connection sees a committed claim, original inputs and registration.
        row = registry.get('trend')
        assert row['state'] == 'RUNNING' and row['result'] is None
        assert registry.events('trend')[0]['reason'] == 'REGISTERED_BEFORE_VALIDATION'
        return original(dataset, cfg)
    monkeypatch.setattr(quant_store, 'run_reference', observed)
    row = registry.submit('trend', fixture(), config())
    assert row['state'] == 'QUEUED' and row['result'] is None
    final = registry.run('trend')
    assert final['state'] == 'COMPLETED' and final['result_hash'] == digest(final['result'])
    assert registry.submit('trend', fixture(), config()) == final
    assert TrialRegistry(registry.engine).run('trend') == final
    registry.submit('cash', fixture(), config('CASH'))
    with registry.engine.connect() as c:
        assert c.scalar(select(func.count()).select_from(DATASETS)) == 1
    changed = config(); changed['initial_cash'] = '999'
    with pytest.raises(ValueError, match='IDEMPOTENCY_CONFLICT'):
        registry.submit('trend', fixture(), changed)


def test_concurrent_submit_and_execution_are_single_claim(registry, monkeypatch):
    from app import quant_store
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: registry.submit('single', fixture(), config()), range(8)))
    entered, release = threading.Event(), threading.Event()
    original = quant_store.run_reference
    calls = []
    def wait_for_release(*args):
        calls.append(1); entered.set()
        assert release.wait(10)
        return original(*args)
    monkeypatch.setattr(quant_store, 'run_reference', wait_for_release)
    with ThreadPoolExecutor(max_workers=2) as pool:
        worker = pool.submit(registry.run, 'single')
        assert entered.wait(10)
        assert registry.run('single')['state'] == 'RUNNING'
        release.set()
        assert worker.result()['state'] == 'COMPLETED'
    assert len(calls) == 1 and len(registry.events('single')) == 3


@pytest.mark.parametrize('kind,reason', [('real','REAL_DATA_NOT_ENABLED_B3_1'),
    ('genome','INVALID_EXPERIMENT_CONTRACT'), ('bars','INSUFFICIENT_SYNTHETIC_BARS')])
def test_rejected_trials_are_preserved(registry,kind,reason):
    data, cfg = fixture(), config()
    if kind == 'real': data['kind'] = 'OFFICIAL_MARKET_DATA'
    if kind == 'genome': cfg['genome']['family'] = 'EXECUTE_SHELL'
    if kind == 'bars': cfg['genome']['lookback'] = 20
    registry.submit('rejected',data,cfg)
    result = registry.run('rejected')
    assert result['state'] == 'REJECTED' and result['reason'] == reason
    assert result['result'] is None and result['attempt'] == 1
    assert registry.run('rejected') == result
    assert [e['state'] for e in registry.events('rejected')] == ['QUEUED','RUNNING','REJECTED']


def test_engine_exception_preserves_failure_without_exception_content(registry,monkeypatch):
    registry.submit('broken',fixture(),config())
    def broken(*args): raise RuntimeError('SECRET_SENTINEL')
    monkeypatch.setattr('app.quant_store.run_reference',broken)
    result = registry.run('broken')
    assert result['state'] == 'FAILED' and result['reason'] == 'REFERENCE_ENGINE_ERROR'
    assert 'SECRET_SENTINEL' not in json.dumps(result)
    assert registry.run('broken') == result


def test_restart_after_crash_recovers_same_trial_and_records_interruption(registry,monkeypatch):
    from app import quant_store
    time = [datetime(2026,11,11,tzinfo=timezone.utc)]
    registry.clock = lambda: time[0]
    registry.submit('interrupted',fixture(),config())
    original = quant_store.run_reference
    def crash(*args): raise SystemExit('simulated process exit')
    monkeypatch.setattr(quant_store,'run_reference',crash)
    with pytest.raises(SystemExit): registry.run('interrupted')
    assert registry.get('interrupted')['state'] == 'RUNNING'
    time[0] += timedelta(seconds=61)
    monkeypatch.setattr(quant_store,'run_reference',original)
    restarted = TrialRegistry(registry.engine, clock=lambda: time[0])
    row = restarted.run('interrupted')
    assert row['state'] == 'COMPLETED' and row['attempt'] == 2
    assert row['result'] == calculate()
    assert [e['state'] for e in restarted.events('interrupted')] == ['QUEUED','RUNNING','INTERRUPTED','RUNNING','COMPLETED']


def test_expired_worker_cannot_overwrite_recovered_result(registry,monkeypatch):
    from app import quant_store
    time = [datetime(2026,11,11,tzinfo=timezone.utc)]
    registry.clock = lambda: time[0]
    registry.submit('fenced',fixture(),config())
    original = quant_store.run_reference
    entered, release = threading.Event(), threading.Event()
    calls = []
    def paused(*args):
        calls.append(1)
        if len(calls) == 1:
            entered.set(); assert release.wait(10)
            raise RuntimeError('stale worker must not replace completed result')
        return original(*args)
    monkeypatch.setattr(quant_store,'run_reference',paused)
    with ThreadPoolExecutor(max_workers=2) as pool:
        old = pool.submit(registry.run,'fenced')
        assert entered.wait(10)
        time[0] += timedelta(seconds=61)
        final = registry.run('fenced')
        release.set()
        assert old.result() == final
    assert final['state'] == 'COMPLETED' and final['attempt'] == 2


def test_crash_loop_is_bounded(registry,monkeypatch):
    time = [datetime(2026,11,11,tzinfo=timezone.utc)]
    registry.clock = lambda: time[0]
    registry.submit('crash-loop',fixture(),config())
    def crash(*args): raise SystemExit()
    monkeypatch.setattr('app.quant_store.run_reference',crash)
    for _ in range(3):
        with pytest.raises(SystemExit): registry.run('crash-loop')
        time[0] += timedelta(seconds=61)
    final = registry.run('crash-loop')
    assert final['state'] == 'FAILED' and final['reason'] == 'RECOVERY_LIMIT'


@pytest.mark.parametrize('tamper', ['data','config','code'])
def test_input_and_code_integrity_fail_closed(registry,monkeypatch,tamper):
    row = registry.submit('integrity',fixture(),config())
    with registry.engine.begin() as c:
        if tamper == 'data': c.execute(update(DATASETS).values(payload=fixture() | {'instrument':'CHANGED'}))
        if tamper == 'config': c.execute(update(TRIALS).values(config=config('CASH')))
    if tamper == 'code': monkeypatch.setattr('app.quant_store.code_hash',lambda: '0'*64)
    final = registry.run(row['id'])
    assert final['state'] == 'REJECTED'
    assert final['reason'] == ('ENGINE_VERSION_CHANGED' if tamper == 'code' else 'INPUT_HASH_MISMATCH')


def test_master_and_orders_untouched(client):
    engine = client.app.state.engine
    tables = ('portfolios','ledger_events','ledger_entries','valuation_snapshots')
    def snapshot():
        with engine.connect() as c:
            return {name: [tuple(row) for row in c.execute(text('SELECT * FROM '+name))] for name in tables}
    before = snapshot()
    store = TrialRegistry(engine)
    for family in ('SMA_LONG_CASH','CASH','BUY_HOLD'):
        store.submit(family,fixture(),config(family))
        assert store.run(family)['state'] == 'COMPLETED'
    assert snapshot() == before
    assert client.post('/api/orders',json={'mode':'paper','risk_approved':True}).status_code == 403
    assert client.get('/api/portfolio/master/summary').json()['nav_eur'] == '10000.00'


def test_populated_registry_cannot_be_dropped(registry):
    from alembic import command
    from alembic.config import Config
    from app.config import ROOT
    registry.submit('preserve',fixture(),config())
    with pytest.raises(RuntimeError,match='Preservar'):
        command.downgrade(Config(str(ROOT/'alembic.ini')),'0013_shadow_cycles')
    assert registry.get('preserve')['state'] == 'QUEUED'
