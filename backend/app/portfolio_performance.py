"""Conservative performance. No interpolation or invented daily observations."""
from datetime import datetime
from decimal import Decimal, localcontext
from app.portfolio_domain import ZERO, ONE, money


def xirr(flows):
    """Decimal bisection; conventional cashflows, >=30 days, bounded root only."""
    if len(flows) < 2 or (flows[-1][0]-flows[0][0]).days < 30:
        return None
    signs = [v > ZERO for _, v in flows if v]
    if sum(a != b for a, b in zip(signs, signs[1:])) != 1:
        return None
    with localcontext() as ctx:
        ctx.prec = 50
        origin = flows[0][0]
        powers = [(Decimal((t-origin).days)/Decimal('365'), v) for t, v in flows]
        def npv(rate):
            return sum((v / ((ONE+rate)**days) for days, v in powers), ZERO)
        lo, hi = Decimal('-.9999'), Decimal('100')
        left, right = npv(lo), npv(hi)
        if left*right > ZERO:
            return None
        for _ in range(220):
            mid = (lo+hi)/2
            value = npv(mid)
            if abs(value) < Decimal('1e-24'):
                return mid*100
            if left*value <= ZERO:
                hi = mid
            else:
                lo, left = mid, value
        return (lo+hi)/2*100


def performance(summary, snapshots, events):
    with localcontext() as ctx:
        ctx.prec = 50
        return _performance(summary, snapshots, events)


def _performance(summary, snapshots, events):
    output = {key: summary[key] for key in ('nav_eur', 'cash_eur', 'market_value_eur', 'realized_pnl_eur', 'unrealized_pnl_eur', 'fx_effect_eur', 'total_pnl_eur', 'cumulative_return_pct', 'valuation_status', 'as_of')}
    output.update(daily_return_pct=None, twr_pct=None, mwr_xirr_pct=None, max_drawdown_pct=None,
        reason='Historia insuficiente: no se fabrican observaciones ni ratios.', observations=len(snapshots))
    current_time = datetime.fromisoformat(summary['as_of'])
    usable = [s for s in snapshots if s['valuation_status'] == 'FRESH' and s['nav_eur'] is not None and datetime.fromisoformat(s['as_of']) <= current_time]
    flows = [(e.occurred_at, e.amount*e.fx) for e in events if e.kind == 'DEPOSIT_VIRTUAL']
    # Without valuations at every external flow boundary we do not approximate TWR.
    if len(flows) != 1 or not usable or summary['valuation_status'] != 'FRESH' or summary['nav_eur'] is None:
        return output
    daily = {}
    for s in usable:
        daily[datetime.fromisoformat(s['as_of']).date()] = s
    previous = [s for d, s in daily.items() if (current_time.date()-d).days == 1]
    if previous:
        start = Decimal(previous[-1]['nav_eur'])
        if start > ZERO:
            output['daily_return_pct'] = str((Decimal(summary['nav_eur'])/start-ONE)*100)
    if len(daily) < 3:
        return output
    series = sorted(daily.values(), key=lambda s: s['as_of'])
    start = Decimal(series[0]['nav_eur'])
    if start <= ZERO or any(Decimal(s['nav_eur']) <= ZERO for s in series):
        return output
    output['twr_pct'] = str((Decimal(series[-1]['nav_eur'])/start-ONE)*100)
    peak, drawdown = start, ZERO
    for row in series:
        value = Decimal(row['nav_eur'])
        peak = max(peak, value)
        drawdown = min(drawdown, (value/peak-ONE)*100)
    output['max_drawdown_pct'] = str(drawdown)
    result = xirr([(t, -v) for t, v in flows]+[(current_time, Decimal(summary['nav_eur']))])
    output['mwr_xirr_pct'] = str(result) if result is not None else None
    output['reason'] = 'TWR/drawdown sobre snapshots diarios existentes, sin interpolación; XIRR requiere 30 días y raíz única convencional.'
    output['period_start'] = series[0]['as_of']
    output['period_end'] = series[-1]['as_of']
    return output
