from typing import Literal
from pydantic import AwareDatetime, Field
from app.contracts import Contract


class PortfolioSummary(Contract):
    portfolio_id: Literal['MASTER']
    base_currency: Literal['EUR']
    trading_mode: Literal['PAPER_ONLY']
    orders_enabled: Literal[False]
    as_of: AwareDatetime
    ledger_status: Literal['VERIFIED_APPEND_ONLY']
    ledger_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    events_count: int
    seeded_at: AwareDatetime
    valuation_status: Literal['FRESH', 'STALE', 'NO_DATA', 'ESTIMATED']
    nav_eur: str | None
    cash_eur: str | None
    market_value_eur: str | None
    accruals_eur: str | None
    liabilities_eur: str
    contributed_eur: str
    positions_count: int
    invested_pct: str | None
    realized_pnl_eur: str
    unrealized_pnl_eur: str | None
    income_eur: str
    fees_eur: str
    total_pnl_eur: str | None
    fx_effect_eur: str | None
    cumulative_return_pct: str | None
    cash_accounts: list[dict]
    positions: list[dict]
    provenance: list[dict]
    valuation_method: str
    performance: dict


class PortfolioPage(Contract):
    total: int
    offset: int
    limit: int
    items: list[dict]


class LedgerPage(PortfolioPage):
    portfolio_id: Literal['MASTER']
    ledger_hash: str


class PositionsResponse(Contract):
    as_of: AwareDatetime
    valuation_status: str
    items: list[dict]


class MarketWatchlist(Contract):
    checked_at: AwareDatetime
    watchlists: list[str]
    selected: Literal['CORE']
    items: list[dict]
    pulse: list[dict]
    reason: str
