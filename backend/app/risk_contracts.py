"""Versioned B5 input contract for a reviewed long-only PAPER batch."""
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field, StrictBool, StrictInt, model_validator


def decimal_text(value):
    if not isinstance(value, (str, Decimal)):
        raise ValueError('DECIMAL_TEXT_REQUIRED')
    return value


Number = Annotated[Decimal, BeforeValidator(decimal_text), Field(ge=0, max_digits=22, decimal_places=8, allow_inf_nan=False)]
Positive = Annotated[Number, Field(gt=0)]
Quantity = Annotated[StrictInt, Field(ge=0, le=1_000_000_000)]
Ref = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
Name = Annotated[str, Field(min_length=1, max_length=96, pattern=r'^[a-zA-Z0-9_.:-]+$')]
Currency = Annotated[str, Field(pattern=r'^[A-Z]{3}$')]


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, hide_input_in_errors=True)


class PaperAccount(Contract):
    domain: Literal['ALPACA_PAPER']
    account_ref: Ref
    snapshot_ref: Ref
    currency: Currency
    as_of: AwareDatetime
    reconciled: StrictBool
    complete: StrictBool
    kill_switch: StrictBool
    cash: Number  # Settled cash before reserving outstanding buys.
    session_open_equity: Positive
    high_water_equity: Positive
    turnover_today: Number
    open_orders: Annotated[StrictInt, Field(ge=0, le=10000)]


class Instrument(Contract):
    listing_id: Name
    issuer: Name
    currency: Currency
    sector: Name
    factor: Name
    eligible: StrictBool
    market_open: StrictBool
    quote_ref: Ref
    quote_at: AwareDatetime
    bid: Positive
    ask: Positive
    liquidity_ref: Ref
    liquidity_at: AwareDatetime
    average_daily_shares: Positive
    shares: Quantity
    pending_buy_shares: Quantity
    pending_buy_cash: Number
    pending_sell_shares: Quantity

    @model_validator(mode='after')
    def coherent(self):
        if (self.ask < self.bid or self.pending_sell_shares > self.shares or
                bool(self.pending_buy_shares) != bool(self.pending_buy_cash)):
            raise ValueError('INCONSISTENT_INSTRUMENT_SNAPSHOT')
        return self


class DownsideScenario(Contract):
    evidence_ref: Ref
    invalidation: Positive
    stressed_exit: Number


class Proposal(Contract):
    candidate_id: Name
    listing_id: Name
    side: Literal['BUY', 'SELL', 'HOLD']
    quantity: Quantity
    committee_ref: Ref
    committee_approved: StrictBool
    approved_at: AwareDatetime
    expires_at: AwareDatetime
    downside: DownsideScenario | None = None

    @model_validator(mode='after')
    def coherent(self):
        if (self.side == 'HOLD') != (self.quantity == 0) or self.approved_at >= self.expires_at:
            raise ValueError('INVALID_PROPOSAL')
        return self


class RiskInputs(Contract):
    version: Literal['paper-risk-inputs-v1']
    dossier_id: Ref
    account: PaperAccount
    instruments: Annotated[tuple[Instrument, ...], Field(min_length=1, max_length=256)]
    proposals: Annotated[tuple[Proposal, ...], Field(min_length=1, max_length=32)]

    @model_validator(mode='after')
    def coherent(self):
        listings = {a.listing_id for a in self.instruments}
        pairs = {(p.candidate_id, p.listing_id) for p in self.proposals}
        pending_sides = sum(bool(a.pending_buy_shares) + bool(a.pending_sell_shares) for a in self.instruments)
        if (len(listings) != len(self.instruments) or len(pairs) != len(self.proposals)
                or pending_sides > self.account.open_orders
                or bool(pending_sides) != bool(self.account.open_orders)
                or any(a.currency != self.account.currency for a in self.instruments)
                or any(p.listing_id not in listings for p in self.proposals)):
            raise ValueError('INCOHERENT_RISK_PACKET')
        return self
