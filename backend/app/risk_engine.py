"""Deterministic PAPER risk review. No broker, market adapter, portfolio or LLM calls."""
from dataclasses import asdict, dataclass
from datetime import timedelta
from decimal import Decimal, localcontext, ROUND_HALF_UP
from app.quant_store import digest

D = Decimal


@dataclass(frozen=True)
class Policy:
    version: str = 'paper-risk-v2'
    cash_reserve: str = '0.10'
    gross_limit: str = '0.80'
    issuer_limit: str = '0.15'
    sector_limit: str = '0.35'
    factor_limit: str = '0.50'
    order_limit: str = '0.05'
    listing_loss_budget: str = '0.005'
    turnover_limit: str = '0.25'
    drawdown_limit: str = '0.10'
    daily_loss_limit: str = '0.03'
    adv_participation: str = '0.005'
    max_spread: str = '0.005'
    cost_buffer: str = '0.002'
    max_open_orders: int = 10
    account_seconds: int = 60
    quote_seconds: int = 30
    liquidity_days: int = 7
    ttl_seconds: int = 60


POLICY = Policy()
POLICY_HASH = digest(asdict(POLICY))


def fresh(stamp, now, duration):
    return stamp <= now < stamp + duration


def buy_downside(proposal, asset, nav, buy_price, reserved_cash, reserved_shares, prior_exit):
    """Mark held shares at bid; use the worse reviewed liquidation price across accepted buys."""
    scenario = proposal.downside
    if scenario is None:
        return None, 'DOWNSIDE_SCENARIO_MISSING'
    if not scenario.stressed_exit <= scenario.invalidation < asset.bid:
        return None, 'DOWNSIDE_SCENARIO_INVALID'
    exit_price = scenario.stressed_exit if prior_exit is None else min(prior_exit, scenario.stressed_exit)
    net_exit = exit_price * (1 - D(POLICY.cost_buffer))
    loss_on_holdings = asset.shares * (asset.bid - net_exit)
    reserved_loss = max(D(0), reserved_cash - reserved_shares * net_exit)
    budget = nav * D(POLICY.listing_loss_budget)
    per_share = buy_price - net_exit
    available = max(D(0), budget - loss_on_holdings - reserved_loss)
    maximum = int(available // per_share)
    trace = dict(evidence_ref=scenario.evidence_ref, invalidation=str(scenario.invalidation),
                 stressed_exit=str(exit_price), budget=str(budget), max_additional_shares=maximum,
                 estimated_listing_loss=str(loss_on_holdings + reserved_loss + proposal.quantity * per_share))
    return trace, 'LISTING_STRESS_LOSS_LIMIT' if proposal.quantity > maximum else None


def assess(inputs, now, expires):
    if now.utcoffset() is None or expires.utcoffset() is None:
        raise ValueError('TIMEZONE_REQUIRED')
    with localcontext() as ctx:
        ctx.prec = 48
        ctx.rounding = ROUND_HALF_UP
        return _assess(inputs, now, expires)


def _assess(inputs, now, expires):
    a, policy = inputs.account, POLICY
    names = {i.listing_id: i for i in inputs.instruments}
    active = [i for i in inputs.instruments if i.shares or i.pending_buy_shares or i.pending_sell_shares
              or any(p.listing_id == i.listing_id for p in inputs.proposals)]
    global_veto = []
    if now >= expires:
        global_veto.append('EVIDENCE_EXPIRED')
    if a.kill_switch:
        global_veto.append('KILL_SWITCH')
    if not a.complete or not a.reconciled:
        global_veto.append('ACCOUNT_UNRECONCILED_OR_INCOMPLETE')
    if not fresh(a.as_of, now, timedelta(seconds=policy.account_seconds)):
        global_veto.append('ACCOUNT_STALE_OR_FUTURE')
    if any(not fresh(i.quote_at, now, timedelta(seconds=policy.quote_seconds)) for i in active):
        global_veto.append('QUOTE_STALE_OR_FUTURE')
    # Price every held share at bid for NAV and at ask for risk. Unfilled sells
    # never release cash or exposure. Existing buys reserve at least their recorded cash.
    nav = a.cash + sum((i.shares * i.bid for i in active), D(0))
    if nav <= 0 or a.high_water_equity < max(a.session_open_equity, nav):
        global_veto.append('INCONSISTENT_ACCOUNT_EQUITY')
    unit = {i.listing_id: i.ask * (1 + D(policy.cost_buffer)) for i in active}
    committed = {i.listing_id: max(i.pending_buy_cash, i.pending_buy_shares * unit[i.listing_id]) for i in active}
    exposure = {i.listing_id: i.shares * i.ask + committed[i.listing_id] for i in active}
    cash = a.cash - sum(committed.values(), D(0))
    available = {i.listing_id: i.shares - i.pending_sell_shares for i in active}
    liquidity_reserved = {i.listing_id: i.pending_buy_shares + i.pending_sell_shares for i in active}
    reserved_buy_shares = {i.listing_id: i.pending_buy_shares for i in active}
    worst_exit = {}
    buying = {i.listing_id for i in active if i.pending_buy_shares}
    selling = {i.listing_id for i in active if i.pending_sell_shares}
    unclassified = {'UNKNOWN', 'UNCLASSIFIED', 'UNMAPPED', 'NA', 'N.A.'}
    missing_groups = any(getattr(i, field).upper() in unclassified for i in active
                         if exposure[i.listing_id] for field in ('issuer', 'sector', 'factor'))
    turnover = a.turnover_today + sum((committed[i.listing_id] + i.pending_sell_shares * i.ask for i in active), D(0))
    count = a.open_orders
    daily_loss = max(D(0), 1 - nav / a.session_open_equity)
    drawdown = max(D(0), 1 - nav / a.high_water_equity)
    quote_ttl = timedelta(seconds=policy.quote_seconds)
    account_until = a.as_of + timedelta(seconds=policy.account_seconds)
    valid_until = min(expires, now + timedelta(seconds=policy.ttl_seconds), account_until,
                      *(i.quote_at + quote_ttl for i in active))
    decisions = []
    for p in inputs.proposals:  # The order in the reviewed, hash-pinned packet is binding.
        asset = names[p.listing_id]
        cost = unit[p.listing_id] * p.quantity
        midpoint = (asset.ask + asset.bid) / 2
        spread = (asset.ask - asset.bid) / midpoint
        share_of_volume = (liquidity_reserved[p.listing_id] + p.quantity) / asset.average_daily_shares
        liquidity_until = asset.liquidity_at + timedelta(days=policy.liquidity_days)
        expiry = min(valid_until, p.expires_at, liquidity_until)
        reasons = list(global_veto)
        downside = None
        if not p.committee_approved:
            reasons.append('COMMITTEE_APPROVAL_MISSING')
        if not p.approved_at <= now < p.expires_at:
            reasons.append('PROPOSAL_STALE_OR_FUTURE')
        if not asset.eligible or not asset.market_open:
            reasons.append('INSTRUMENT_OR_SESSION_INELIGIBLE')
        if not fresh(asset.liquidity_at, now, timedelta(days=policy.liquidity_days)):
            reasons.append('LIQUIDITY_STALE_OR_FUTURE')
        if p.side != 'HOLD':
            if p.listing_id in (selling if p.side == 'BUY' else buying):
                reasons.append('OPPOSING_OPEN_INTENT')
            if spread > D(policy.max_spread) or share_of_volume > D(policy.adv_participation):
                reasons.append('SPREAD_OR_LIQUIDITY_LIMIT')
            if cost > nav * D(policy.order_limit):
                reasons.append('ORDER_SIZE_LIMIT')
            if count >= policy.max_open_orders or turnover + cost > nav * D(policy.turnover_limit):
                reasons.append('ORDER_COUNT_OR_TURNOVER_LIMIT')
        if p.side == 'BUY':
            committed_cash = exposure[p.listing_id] - asset.shares * asset.ask
            downside, loss_veto = buy_downside(p, asset, nav, unit[p.listing_id], committed_cash,
                                               reserved_buy_shares[p.listing_id], worst_exit.get(p.listing_id))
            if loss_veto:
                reasons.append(loss_veto)
            if missing_groups or any(getattr(asset, field).upper() in unclassified for field in ('issuer', 'sector', 'factor')):
                reasons.append('EXPOSURE_CLASSIFICATION_MISSING')
            if daily_loss >= D(policy.daily_loss_limit) or drawdown >= D(policy.drawdown_limit):
                reasons.append('LOSS_OR_DRAWDOWN_LIMIT')
            if cash - cost < nav * D(policy.cash_reserve):
                reasons.append('CASH_RESERVE_LIMIT')
            if sum(exposure.values()) + cost > nav * D(policy.gross_limit):
                reasons.append('GROSS_EXPOSURE_LIMIT')
            for field, limit, reason in [('issuer', policy.issuer_limit, 'ISSUER_LIMIT'),
                                         ('sector', policy.sector_limit, 'SECTOR_LIMIT'), ('factor', policy.factor_limit, 'FACTOR_LIMIT')]:
                group = getattr(asset, field)
                existing = sum((exposure[i.listing_id] for i in active if getattr(i, field) == group), D(0))
                if existing + cost > nav * D(limit):
                    reasons.append(reason)
        elif p.side == 'SELL' and p.quantity > available[p.listing_id]:
            reasons.append('SELL_EXCEEDS_UNRESERVED_SHARES')
        if not reasons and p.side != 'HOLD':
            count += 1
            turnover += cost
            liquidity_reserved[p.listing_id] += p.quantity
            if p.side == 'BUY':
                buying.add(p.listing_id)
                reserved_buy_shares[p.listing_id] += p.quantity
                worst_exit[p.listing_id] = D(downside['stressed_exit'])
                exposure[p.listing_id] += cost
                cash -= cost
            else:
                selling.add(p.listing_id)
                available[p.listing_id] -= p.quantity
        decisions.append(dict(candidate_id=p.candidate_id, listing_id=p.listing_id, requested=p.side,
            quantity=p.quantity, decision='HOLD' if reasons else p.side, veto=bool(reasons),
            reasons=reasons or ['EXPLICIT_HOLD' if p.side == 'HOLD' else 'POLICY_CHECKS_PASSED'],
            expires_at=expiry.isoformat(), committee_ref=p.committee_ref, quote_ref=asset.quote_ref,
            liquidity_ref=asset.liquidity_ref, currency=a.currency, notional_with_buffer=str(cost),
            spread_fraction=str(spread), adv_fraction=str(share_of_volume), downside=downside,
            remaining_cash_after_reservations=str(cash), gross_after_reservations=str(sum(exposure.values()))))
    return decisions
