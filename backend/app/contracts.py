from datetime import date
from decimal import Decimal
from enum import StrEnum
import re
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AccountScope(StrEnum):
    MASTER = "MASTER"
    ALPACA_PAPER = "ALPACA_PAPER"
    T212_DEMO = "T212_DEMO"


class AssetClass(StrEnum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    REIT = "REIT"
    SOVEREIGN_BOND = "SOVEREIGN_BOND"
    CORPORATE_BOND = "CORPORATE_BOND"
    BOND_ETF = "BOND_ETF"
    CASH = "CASH"
    FX = "FX"
    MONEY_MARKET = "MONEY_MARKET"
    COMMODITY_ETP = "COMMODITY_ETP"
    OPTION = "OPTION"
    FUTURE = "FUTURE"
    PRIVATE_EQUITY = "PRIVATE_EQUITY"
    PRIVATE_CREDIT = "PRIVATE_CREDIT"
    REAL_ESTATE = "REAL_ESTATE"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    STRUCTURED = "STRUCTURED"
    CRYPTO = "CRYPTO"
    INDEX = "INDEX"
    MACRO_SERIES = "MACRO_SERIES"


class ProviderCapability(Contract):
    provider: str = Field(min_length=1)
    research: bool = False
    valuation: bool = False
    internal_paper: bool = False
    broker_paper: bool = False
    checked_at: AwareDatetime | None = None
    license: str | None = None
    reason: str = Field(min_length=1)
    source: str | None = None
    feed: str | None = None
    expires_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def evidence_required(self):
        if any((self.research, self.valuation, self.internal_paper, self.broker_paper)):
            if self.checked_at is None or not self.license:
                raise ValueError("Una capacidad habilitada requiere fecha y licencia verificadas.")
            if self.feed and (not self.source or not self.source.startswith('https://')):
                raise ValueError('Capacidad de feed sin fuente documental.')
        if self.expires_at and (not self.checked_at or self.expires_at <= self.checked_at):
            raise ValueError('Caducidad inválida.')
        return self

    def active(self, now):
        return self.checked_at is not None and self.checked_at <= now and (self.expires_at is None or now < self.expires_at)


class BondTerms(Contract):
    face_value: Decimal = Field(gt=0, allow_inf_nan=False)
    coupon_rate: Decimal = Field(ge=0, allow_inf_nan=False)
    maturity: date
    payments_per_year: int = Field(ge=0)
    day_count: str = Field(min_length=1)
    source: str = Field(min_length=1)


class Instrument(Contract):
    id: UUID
    symbol: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    currency: str | None = Field(default=None, pattern=r"^[A-Z0-9]{3,12}$")
    country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    asset_class: AssetClass
    isin: str | None = None
    cusip: str | None = None
    figi: str | None = None
    bond_terms: BondTerms | None = None
    provider_capabilities: tuple[ProviderCapability, ...] = ()
    source: str | None = None
    verified_at: AwareDatetime | None = None

    @model_validator(mode='after')
    def currency_semantics(self):
        if self.currency is None and self.asset_class not in (AssetClass.MACRO_SERIES, AssetClass.INDEX):
            raise ValueError('Divisa necesaria para instrumento monetario.')
        if self.currency and self.asset_class != AssetClass.CRYPTO and not re.fullmatch('[A-Z]{3}',self.currency):
            raise ValueError('Divisa monetaria de tres letras.')
        return self


class Quote(Contract):
    instrument_id: UUID
    price: Decimal = Field(gt=0, allow_inf_nan=False)
    provider: str = Field(min_length=1)
    as_of: AwareDatetime
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    delay_seconds: int = Field(ge=0)
    quality_flags: tuple[str, ...]


class ProviderStatus(Contract):
    provider: str
    status: Literal["NO DISPONIBLE"] = "NO DISPONIBLE"
    reason: str
    checked_at: AwareDatetime | None = None


class Health(Contract):
    status: Literal["ok"] = "ok"
    phase: Literal["P0"] = "P0"
    trading_mode: Literal["PAPER_ONLY"] = "PAPER_ONLY"
    orders_enabled: Literal[False] = False
    database: Literal["ok"] = "ok"
    schema_version: str
    checked_at: AwareDatetime


class ApiError(Contract):
    code: str
    message: str
