"""Contratos P2: observaciones, nunca posiciones ni precios de ejecución."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from pydantic import AwareDatetime, Field, model_validator
from app.contracts import Contract

DataKind = Literal['market_quote', 'fundamental_fact', 'macro_series', 'fx_reference', 'yield_curve', 'instrument_metadata', 'news_metadata']
DataState = Literal['AVAILABLE_VERIFIED', 'DELAYED', 'STALE', 'NO_DATA', 'NO_CREDENTIALS', 'CONFIG_REQUIRED', 'AUTH_FAILED', 'RATE_LIMITED', 'RIGHTS_RESTRICTED', 'OFFLINE', 'TIMEOUT', 'INVALID_PAYLOAD', 'ERROR', 'NOT_IMPLEMENTED', 'PLAN_REQUIRED', 'DISABLED', 'NOT_VERIFIED']

class Rights(Contract):
    license: str
    source: str
    checked_at: AwareDatetime | None = None
    access_allowed: bool = False
    display_allowed: bool = False
    storage_allowed: bool = False
    redistribution_allowed: bool = False
    scope: Literal['open', 'personal', 'internal', 'restricted'] = 'restricted'
    attribution: str

    @model_validator(mode='after')
    def proof(self):
        if any((self.access_allowed, self.display_allowed, self.storage_allowed, self.redistribution_allowed)) and (not self.checked_at or not self.source.startswith('https://')):
            raise ValueError('Derechos sin prueba documental.')
        return self

class Observation(Contract):
    id: str
    provider: str
    access_id: str
    feed: str
    series_id: str
    data_kind: DataKind
    venue: str
    country: str | None = None
    asset_class: str
    source_ref: str
    payload_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    observed_at: AwareDatetime
    received_at: AwareDatetime
    published_at: AwareDatetime | None = None
    period: str
    period_precision: Literal['instant', 'day', 'month', 'quarter', 'year']
    currency: str | None = Field(default=None, pattern=r'^[A-Z0-9]{3,12}$')
    unit: str = Field(min_length=1)
    value: Decimal | None = Field(default=None, allow_inf_nan=False)
    bid: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    ask: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    metadata: dict[str, str] = {}
    delay_seconds: int | None = Field(default=None, ge=0)
    stale_after_seconds: int = Field(gt=0)
    quality_flags: tuple[str, ...] = ()
    rights: Rights
    execution_eligible: Literal[False] = False

    @model_validator(mode='after')
    def semantics(self):
        if any(t.utcoffset() != timedelta(0) for t in (self.observed_at, self.received_at, *([self.published_at] if self.published_at else []))):
            raise ValueError('Fechas exclusivamente UTC.')
        if self.observed_at > self.received_at + timedelta(minutes=5):
            raise ValueError('Fecha observada futura.')
        if self.data_kind == 'market_quote' and (self.value is None or self.value <= 0 or not self.currency):
            raise ValueError('Cotización inválida.')
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError('Bid superior a ask.')
        if self.data_kind not in ('news_metadata', 'instrument_metadata') and self.value is None:
            raise ValueError('Ausencia no equivale a cero.')
        return self

    def stale(self, now: datetime) -> bool:
        # Series y EOD conservan su periodo histórico; no se convierten en realtime.
        return (now - self.received_at).total_seconds() > self.stale_after_seconds

class DataResult(Contract):
    access_id: str
    state: DataState
    reason: str
    checked_at: AwareDatetime | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    http_status: int | None = None
    real_connection: bool = False
    usable: bool = False
    cache_hit: bool = False
    normalized_count: int = Field(default=0,ge=0)
    observations: tuple[Observation, ...] = ()

class SourceQuality(Contract):
    access_id: str
    provider: str
    name: str
    implemented: bool
    data_kind: DataKind
    asset_class: str
    country: str | None
    market: str
    feed: str
    docs: str
    rights: Rights
    quota_note: str
    quota_used: int = Field(ge=0)
    next_allowed_at: AwareDatetime | None
    state: DataState
    reason: str
    checked_at: AwareDatetime | None
    latency_ms: int | None = Field(default=None,ge=0)
    http_status: int | None = None
    real_connection: bool
    usable: bool
    cache_hit: bool
    normalized_count: int = Field(ge=0)

class QualityReport(Contract):
    checked_at: AwareDatetime
    counts: dict[str,int]
    sources: tuple[SourceQuality,...]

    @model_validator(mode='after')
    def no_inflated_counts(self):
        expected={'candidate_providers':len({s.provider for s in self.sources}),
          'candidate_access_modes':len(self.sources),'implemented_adapters':sum(s.implemented for s in self.sources),
          'implemented_providers':len({s.provider for s in self.sources if s.implemented}),
          'verified_connections':sum(s.real_connection for s in self.sources),'verified_providers':len({s.provider for s in self.sources if s.real_connection}),
          'usable_sources':sum(s.usable for s in self.sources),'usable_providers':len({s.provider for s in self.sources if s.usable}),
          'no_credentials':sum(s.state=='NO_CREDENTIALS' for s in self.sources),'rights_restricted':sum(s.state=='RIGHTS_RESTRICTED' for s in self.sources)}
        if self.counts!=expected or len({s.access_id for s in self.sources})!=len(self.sources) or any(s.usable and (not s.real_connection or not s.rights.display_allowed) for s in self.sources):
            raise ValueError('Contadores, derechos o prueba real inconsistentes.')
        return self
