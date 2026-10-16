"""P3 deterministic domain. Decimal strings at every persistence/API boundary.

Accounting journal is balanced per native currency (FX uses clearing accounts).
EUR cost basis is tracked separately, at the historical FX of each lot.
No execution, networking, or public mutation interface lives in this module.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from typing import Literal

from pydantic import AwareDatetime, Field, field_validator, model_validator
from app.contracts import Contract

ZERO = Decimal('0')
ONE = Decimal('1')
EventKind = Literal['DEPOSIT_VIRTUAL', 'ORDER_RESERVED', 'FILL_BUY', 'FILL_SELL',
    'FEE', 'FX_CONVERSION', 'DIVIDEND', 'COUPON', 'INTEREST_ACCRUAL',
    'BOND_REDEMPTION', 'SPLIT', 'MERGER', 'RECONCILIATION_ADJUSTMENT']


def decimal_value(value):
    if isinstance(value, (float, bool)):
        raise ValueError('Financial values must be decimal strings, never float/bool.')
    value = Decimal(value)
    if not value.is_finite() or abs(value) > Decimal('1e24') or value.as_tuple().exponent < -24:
        raise ValueError('Non-finite or out-of-range financial value.')
    return value


def money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    with localcontext() as ctx:
        ctx.prec = 50
        return format(value.quantize(Decimal('.01'), rounding=ROUND_HALF_EVEN), 'f')


class PortfolioEvent(Contract):
    kind: EventKind
    source_ref: str = Field(min_length=1, max_length=200)
    actor: str = Field(min_length=1, max_length=100)
    occurred_at: AwareDatetime
    currency: str = Field(default='EUR', pattern=r'^[A-Z]{3}$')
    instrument: str | None = None
    amount: Decimal = ZERO
    qty: Decimal = ZERO
    price: Decimal = ZERO
    fee: Decimal = ZERO
    fx: Decimal = ONE  # EUR per one native currency unit; immutable historical rate
    target_currency: str | None = Field(default=None, pattern=r'^[A-Z]{3}$')
    target_fx: Decimal = ONE
    target_instrument: str | None = None
    ratio: Decimal = ONE
    reservation_ref: str | None = None
    settles_accrual: bool = False
    evidence: str | None = None

    @field_validator('amount', 'qty', 'price', 'fee', 'fx', 'target_fx', 'ratio', mode='before')
    @classmethod
    def decimals_only(cls, value):
        return decimal_value(value)

    @model_validator(mode='after')
    def valid(self):
        if self.occurred_at.utcoffset() != timedelta(0):
            raise ValueError('UTC required.')
        if self.fx <= ZERO or self.target_fx <= ZERO or self.ratio <= ZERO or self.fee < ZERO:
            raise ValueError('Invalid FX, ratio or fee.')
        if self.currency == 'EUR' and self.fx != ONE:
            raise ValueError('EUR/EUR is exactly one.')
        if self.target_currency == 'EUR' and self.target_fx != ONE:
            raise ValueError('EUR/EUR is exactly one.')
        if self.kind in ('FILL_BUY', 'FILL_SELL', 'BOND_REDEMPTION'):
            if not self.instrument or self.qty <= ZERO or self.price <= ZERO:
                raise ValueError('Instrument, positive quantity and price required.')
        if self.kind in ('SPLIT', 'MERGER') and not self.instrument:
            raise ValueError('Corporate action requires instrument.')
        if self.kind == 'MERGER' and (not self.target_instrument or self.target_instrument == self.instrument):
            raise ValueError('Stock-for-stock merger requires a distinct successor.')
        if self.kind in ('DEPOSIT_VIRTUAL', 'ORDER_RESERVED', 'FEE', 'FX_CONVERSION', 'DIVIDEND', 'COUPON', 'INTEREST_ACCRUAL') and self.amount <= ZERO:
            raise ValueError('Positive amount required.')
        if self.kind == 'FX_CONVERSION' and (not self.target_currency or self.target_currency == self.currency):
            raise ValueError('Two distinct FX currencies required.')
        if self.kind == 'RECONCILIATION_ADJUSTMENT' and (self.amount == ZERO or not self.evidence):
            raise ValueError('Adjustment requires nonzero amount and audit evidence.')
        if self.fee and self.kind not in ('FILL_BUY', 'FILL_SELL', 'BOND_REDEMPTION'):
            raise ValueError('Embedded fee only allowed on fills; use FEE once otherwise.')
        return self


@dataclass
class Lot:
    source_ref: str
    instrument: str
    currency: str
    acquired_at: str
    qty_original: Decimal
    qty_remaining: Decimal
    cost_native: Decimal
    cost_eur: Decimal
    purchase_fx: Decimal
    fee_native: Decimal


@dataclass
class PortfolioState:
    cash: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    cash_basis_eur: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    accruals: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))
    reservations: dict[str, tuple[str, Decimal]] = field(default_factory=dict)
    lots: list[Lot] = field(default_factory=list)
    postings: dict[str, list[dict]] = field(default_factory=dict)
    consumptions: list[dict] = field(default_factory=list)
    contributed_eur: Decimal = ZERO
    realized_pnl_eur: Decimal = ZERO
    income_eur: Decimal = ZERO
    fees_eur: Decimal = ZERO
    realized_fx_eur: Decimal = ZERO
    cash_realized_fx_eur: Decimal = ZERO
    external_flows: list[tuple] = field(default_factory=list)

    def reserved(self, currency):
        return sum((v for c, v in self.reservations.values() if c == currency), ZERO)


def rebuild(events: list[PortfolioEvent]) -> PortfolioState:
    """Full replay; identical source key cannot be applied twice, even in fixtures."""
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return _rebuild(events)


def _rebuild(events):
    state = PortfolioState()
    seen = set()
    previous = None
    for e in events:
        if e.source_ref in seen or (previous and e.occurred_at < previous):
            raise ValueError('Duplicate source or nonchronological history.')
        seen.add(e.source_ref)
        previous = e.occurred_at
        postings = []

        def post(debit, credit, amount, currency=e.currency):
            if amount < ZERO:
                debit, credit, amount = credit, debit, -amount
            if amount:
                postings.extend([dict(account=debit, currency=currency, debit=str(amount), credit='0'),
                                 dict(account=credit, currency=currency, debit='0', credit=str(amount))])

        def spend(amount):
            if state.cash[e.currency] - state.reserved(e.currency) < amount:
                raise ValueError('Insufficient unreserved cash; no borrowing.')
            basis = state.cash_basis_eur[e.currency] if amount == state.cash[e.currency] else state.cash_basis_eur[e.currency] * amount / state.cash[e.currency]
            state.cash_basis_eur[e.currency] -= basis
            state.cash_realized_fx_eur += amount * e.fx - basis
            state.cash[e.currency] -= amount

        def receive(amount, currency=e.currency, fx=e.fx):
            state.cash[currency] += amount
            state.cash_basis_eur[currency] += amount * fx

        if e.kind == 'DEPOSIT_VIRTUAL':
            receive(e.amount)
            state.contributed_eur += e.amount * e.fx
            state.external_flows.append((e.occurred_at, e.amount * e.fx))
            post('CASH', 'VIRTUAL_CAPITAL', e.amount)
        elif e.kind == 'ORDER_RESERVED':
            if state.cash[e.currency] - state.reserved(e.currency) < e.amount:
                raise ValueError('Reservation exceeds cash.')
            state.reservations[e.source_ref] = (e.currency, e.amount)
            post('RESERVED_CASH', 'CASH', e.amount)
        elif e.kind == 'FILL_BUY':
            total = e.qty * e.price + e.fee
            if e.reservation_ref:
                currency, reserved = state.reservations.get(e.reservation_ref, ('', ZERO))
                if currency != e.currency or total > reserved:
                    raise ValueError('Unknown or insufficient reservation.')
                state.reservations[e.reservation_ref] = (currency, reserved-total)
                post('CASH', 'RESERVED_CASH', total)
            if any(l.instrument == e.instrument and l.currency != e.currency for l in state.lots):
                raise ValueError('Instrument currency cannot change implicitly.')
            spend(total)
            state.lots.append(Lot(e.source_ref, e.instrument, e.currency, e.occurred_at.isoformat(),
                e.qty, e.qty, total, total * e.fx, e.fx, e.fee))
            post('INVENTORY:' + e.instrument, 'CASH', total)
        elif e.kind in ('FILL_SELL', 'BOND_REDEMPTION'):
            lots = [l for l in state.lots if l.instrument == e.instrument and l.currency == e.currency and l.qty_remaining > ZERO]
            if sum((l.qty_remaining for l in lots), ZERO) < e.qty:
                raise ValueError('Sale exceeds long inventory.')
            remaining, cost, cost_eur = e.qty, ZERO, ZERO
            for lot in lots:
                if remaining == ZERO:
                    break
                take = min(remaining, lot.qty_remaining)
                # On final consumption use exact residual, never accumulate rounding dust.
                fraction = take / lot.qty_remaining
                native = lot.cost_native if take == lot.qty_remaining else lot.cost_native * fraction
                eur = lot.cost_eur if take == lot.qty_remaining else lot.cost_eur * fraction
                fee_part = lot.fee_native if take == lot.qty_remaining else lot.fee_native * fraction
                lot.qty_remaining -= take
                lot.cost_native -= native
                lot.cost_eur -= eur
                lot.fee_native -= fee_part
                remaining -= take
                cost += native
                cost_eur += eur
                state.consumptions.append(dict(sale=e.source_ref, lot=lot.source_ref, qty=str(take), cost_native=str(native), cost_eur=str(eur), sale_fx=str(e.fx)))
            proceeds = e.qty * e.price - e.fee
            if proceeds < ZERO:
                raise ValueError('Fee exceeds proceeds.')
            receive(proceeds)
            state.realized_pnl_eur += proceeds * e.fx - cost_eur
            state.realized_fx_eur += cost * e.fx - cost_eur
            post('CASH', 'INVENTORY:' + e.instrument, cost)
            post('CASH', 'REALIZED_PNL', proceeds - cost)
        elif e.kind == 'FEE':
            spend(e.amount)
            state.fees_eur += e.amount * e.fx
            post('EXPENSE_FEES', 'CASH', e.amount)
        elif e.kind == 'FX_CONVERSION':
            spend(e.amount)
            target = e.amount * e.fx / e.target_fx
            receive(target, e.target_currency, e.target_fx)
            post('FX_CLEARING', 'CASH', e.amount)
            post('CASH', 'FX_CLEARING', target, e.target_currency)
        elif e.kind == 'INTEREST_ACCRUAL':
            state.accruals[e.currency] += e.amount
            state.income_eur += e.amount * e.fx
            post('ACCRUED_INCOME', 'INCOME', e.amount)
        elif e.kind in ('DIVIDEND', 'COUPON'):
            if e.settles_accrual:
                if state.accruals[e.currency] < e.amount:
                    raise ValueError('Coupon exceeds accrued income.')
                state.accruals[e.currency] -= e.amount
                post('CASH', 'ACCRUED_INCOME', e.amount)
            else:
                state.income_eur += e.amount * e.fx
                post('CASH', 'INCOME', e.amount)
            receive(e.amount)
        elif e.kind in ('SPLIT', 'MERGER'):
            lots = [l for l in state.lots if l.instrument == e.instrument and l.qty_remaining > ZERO]
            if not lots or any(l.currency != e.currency for l in lots):
                raise ValueError('Corporate action has no compatible inventory.')
            for lot in lots:
                lot.qty_original *= e.ratio
                lot.qty_remaining *= e.ratio
                if e.kind == 'MERGER':
                    post('INVENTORY:' + e.target_instrument, 'INVENTORY:' + e.instrument, lot.cost_native)
                    lot.instrument = e.target_instrument
            # Split is a zero-value quantity journal; original event carries the ratio.
        elif e.kind == 'RECONCILIATION_ADJUSTMENT':
            if e.amount < ZERO:
                spend(-e.amount)
            else:
                receive(e.amount)
            state.income_eur += e.amount * e.fx
            post('CASH', 'RECONCILIATION_PNL', e.amount)
        for currency in {p['currency'] for p in postings}:
            if sum((Decimal(p['debit']) - Decimal(p['credit']) for p in postings if p['currency'] == currency), ZERO) != ZERO:
                raise ValueError('Unbalanced journal.')
        state.postings[e.source_ref] = postings
    return state
