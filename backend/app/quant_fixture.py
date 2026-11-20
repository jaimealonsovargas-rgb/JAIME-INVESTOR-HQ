"""Six fabricated sessions, never market observations. Shared by CLI and tests."""
from datetime import datetime, timedelta, timezone


def fixture():
    bars = []
    for i, (opened, closed) in enumerate(zip(('10','10','12','14','8','7'), ('10','12','14','8','7','11'))):
        start = datetime(2000, 1, 3, 9, tzinfo=timezone.utc) + timedelta(days=i)
        bars.append(dict(opens_at=start.isoformat(), closes_at=(start+timedelta(hours=7)).isoformat(),
                         available_at=(start+timedelta(hours=7, seconds=1)).isoformat(), open=opened, close=closed))
    return dict(kind='SYNTHETIC_TEST', instrument='TEST_ONLY', currency='TEST_CCU',
                calendar='EXPLICIT_SYNTHETIC_SESSIONS', adjustments='NO_CORPORATE_ACTIONS_SYNTHETIC', bars=bars)


def config(family='SMA_LONG_CASH'):
    return dict(genome=dict(family=family, lookback=2 if family == 'SMA_LONG_CASH' else None,
                           mechanism='Persistencia de tendencia; control sintético sin inferencia financiera.',
                           falsification='El resultado debe coincidir con la cuenta manual y respetar la cronología.'),
                costs=dict(fixed_per_fill='1', commission_bps='0', slippage_bps='0'), initial_cash='1000')
