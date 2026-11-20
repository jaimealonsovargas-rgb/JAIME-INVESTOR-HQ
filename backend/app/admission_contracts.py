"""Bounded, strict inputs for the offline D3 admission evaluator."""
import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def instant(value):
    if not isinstance(value, str) or len(value)>40:
        raise ValueError('INVALID_TIMESTAMP')
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('TIMEZONE_REQUIRED')
    return parsed.astimezone(timezone.utc).isoformat()


class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid', strict=True, hide_input_in_errors=True)


Name=Annotated[str,Field(min_length=1,max_length=128,pattern=r'^[A-Za-z0-9_.: -]+$')]
Hash=Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]
Number=Annotated[str,Field(min_length=1,max_length=40,pattern=r'^-?[0-9]{1,20}(\.[0-9]{1,12})?$')]


def day(value):
    if not isinstance(value,str) or len(value)!=10 or date.fromisoformat(value).isoformat()!=value or not 1900<=date.fromisoformat(value).year<=2100:
        raise ValueError('INVALID_DATE')
    return value


class Bar(Strict):
    session: str
    open: Number
    high: Number
    low: Number
    close: Number
    volume: Number
    _day=field_validator('session')(day)


class Source(Strict):
    id: Name
    hash: Hash
    received_at: str
    _time=field_validator('received_at')(instant)


class Candidate(Strict):
    version: Literal['admission-candidate-v1']
    domain: Literal['SYNTHETIC_TEST','MARKET_DATA']
    provider: Literal['SYNTHETIC_TEST','IBKR_TWS','ALPACA']
    listing_id: Name
    identity_hash: Hash
    symbol: Name
    venue: Name
    currency: Annotated[str,Field(pattern=r'^[A-Z]{3}$')]|None
    start: str
    end: str
    frequency: Literal['1 day']
    adjustment: Name
    feed: Name
    unit: Literal['PRICE_PER_SHARE']
    universe_hash: Hash
    bars: Annotated[list[Bar],Field(max_length=5000)]
    sources: Annotated[list[Source],Field(max_length=250)]
    source_errors: Annotated[list[Name],Field(max_length=250)]
    cutoff: str
    _days=field_validator('start','end')(day)
    _time=field_validator('cutoff')(instant)

    @model_validator(mode='after')
    def interval(self):
        if not self.start<=self.end or (date.fromisoformat(self.end)-date.fromisoformat(self.start)).days>20000:
            raise ValueError('INVALID_PERIOD')
        return self


def validate_candidate(value):
    return Candidate.model_validate(value).model_dump()


def candidate_hash(value):
    return fingerprint(validate_candidate(value))
