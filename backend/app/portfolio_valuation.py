"""Valuation has no execution capability. Missing inputs propagate as null."""
from datetime import datetime, timedelta
from decimal import Decimal, localcontext

from app.portfolio_domain import ZERO, ONE, PortfolioState, money


def permitted(observation):
    r = observation.rights
    return all((r.access_allowed, r.display_allowed, r.storage_allowed, r.redistribution_allowed))


def freshness(o, now):
    if not permitted(o) or o.value is None or o.value <= ZERO or o.observed_at > now or o.received_at > now:
        return 'NO_DATA'
    if o.stale(now) or now-o.observed_at > timedelta(seconds=o.stale_after_seconds):
        return 'STALE'
    if any('ESTIMAT' in f or 'PROJECTION' in f for f in o.quality_flags):
        return 'ESTIMATED'
    return 'FRESH'


def combine(statuses):
    return next((s for s in ('NO_DATA', 'STALE', 'ESTIMATED') if s in statuses), 'FRESH')


def value_portfolio(state: PortfolioState, quotes, fx_rates, now: datetime, labels=None):
    with localcontext() as ctx:
        ctx.prec = 50
        return _value(state, quotes, fx_rates, now, labels or {})


def _value(state, quotes, fx_rates, now, labels):
    statuses, provenance = [], []

    def fx(currency):
        if currency == 'EUR':
            return ONE, 'FRESH'
        observation = fx_rates.get(currency)
        # Exact semantic whitelist. USD/EUR means USD per EUR, so invert for EUR valuation.
        if observation is None or observation.data_kind != 'fx_reference' or observation.unit != currency+'/EUR':
            return None, 'NO_DATA'
        quality = freshness(observation, now)
        if quality == 'NO_DATA':
            return None, quality
        provenance.append(dict(role='fx', currency=currency, conversion='EUR per unit = 1 / observation.value', observation=observation.model_dump(mode='json')))
        return ONE / observation.value, quality

    cash_total, cash_fx, accrual_total = ZERO, ZERO, ZERO
    cash_rows = []
    for currency in set(state.cash) | set(state.accruals):
        amount, accrued = state.cash[currency], state.accruals[currency]
        rate, status = fx(currency) if amount or accrued else (ONE, 'FRESH')
        statuses.append(status)
        cash_rows.append(dict(currency=currency, amount=str(amount), reserved=str(state.reserved(currency)), value_eur=money(amount*rate) if rate is not None else None, valuation_status=status))
        if rate is None:
            cash_total = cash_fx = accrual_total = None
        else:
            if cash_total is not None:
                cash_total += amount*rate
                cash_fx += amount*rate-state.cash_basis_eur[currency]
                accrual_total += accrued*rate
    positions, market_total, unrealized, position_fx = [], ZERO, ZERO, ZERO
    for instrument in sorted({l.instrument for l in state.lots if l.qty_remaining > ZERO}):
        lots = [l for l in state.lots if l.instrument == instrument and l.qty_remaining > ZERO]
        currency = lots[0].currency
        qty = sum((l.qty_remaining for l in lots), ZERO)
        cost = sum((l.cost_eur for l in lots), ZERO)
        native_cost = sum((l.cost_native for l in lots), ZERO)
        quote = quotes.get(instrument)
        status = freshness(quote, now) if quote and quote.data_kind == 'market_quote' and quote.currency == currency else 'NO_DATA'
        rate, fx_status = fx(currency)
        status = combine([status, fx_status])
        statuses.append(status)
        value = pnl = effect = None
        if status != 'NO_DATA':
            value = qty * quote.value * rate
            pnl = value - cost
            effect = native_cost * rate-cost
            provenance.append(dict(role='quote', instrument=instrument, observation=quote.model_dump(mode='json')))
        positions.append(dict(instrument=instrument, symbol=labels.get(instrument, instrument), currency=currency,
            qty=str(qty), cost_basis_eur=money(cost), cost_basis_native=str(native_cost), unit_cost_native=str(native_cost/qty),
            market_value_eur=money(value), unrealized_pnl_eur=money(pnl), pnl_pct=str(pnl/cost*100) if pnl is not None and cost else None,
            price=str(quote.value) if quote and status != 'NO_DATA' else None, valuation_fx=str(rate) if rate is not None else None,
            fx_effect_eur=money(effect), valuation_status=status,
            provenance=quote.model_dump(mode='json') if quote and status != 'NO_DATA' else None,
            lots=[dict(source_ref=l.source_ref, acquired_at=l.acquired_at, qty_remaining=str(l.qty_remaining), cost_eur=str(l.cost_eur), purchase_fx=str(l.purchase_fx), fee_native=str(l.fee_native)) for l in lots]))
        if value is None:
            market_total = unrealized = position_fx = None
        elif market_total is not None:
            market_total += value
            unrealized += pnl
            position_fx += effect
    nav = cash_total + market_total + accrual_total if all(v is not None for v in (cash_total, market_total, accrual_total)) else None
    status = combine(statuses)
    for position in positions:
        position['weight_pct'] = str(Decimal(position['market_value_eur'])/nav*100) if nav and position['market_value_eur'] is not None else None
    total_pnl = nav-state.contributed_eur if nav is not None else None
    # Exact cumulative return is known with one initial flow; multiple flows require boundary NAVs.
    cumulative = total_pnl/state.contributed_eur*100 if total_pnl is not None and state.contributed_eur > ZERO and len(state.external_flows) == 1 else None
    return dict(portfolio_id='MASTER', base_currency='EUR', trading_mode='PAPER_ONLY', orders_enabled=False,
        as_of=now.isoformat(), ledger_status='VERIFIED_APPEND_ONLY', valuation_status=status,
        cash_eur=money(cash_total), market_value_eur=money(market_total), accruals_eur=money(accrual_total), liabilities_eur='0.00',
        nav_eur=money(nav), contributed_eur=money(state.contributed_eur), positions_count=len(positions),
        invested_pct=str(market_total/nav*100) if nav and market_total is not None else None,
        realized_pnl_eur=money(state.realized_pnl_eur + state.cash_realized_fx_eur), unrealized_pnl_eur=money(unrealized),
        income_eur=money(state.income_eur), fees_eur=money(state.fees_eur), total_pnl_eur=money(total_pnl),
        fx_effect_eur=money(cash_fx+position_fx+state.realized_fx_eur+state.cash_realized_fx_eur) if cash_fx is not None and position_fx is not None else None,
        cumulative_return_pct=str(cumulative) if cumulative is not None else None, cash_accounts=cash_rows,
        positions=positions, provenance=provenance,
        valuation_method='FIFO; purchase fees capitalized; native-currency journal; EUR base; HALF_EVEN display to cents; no short or liabilities in V1')
