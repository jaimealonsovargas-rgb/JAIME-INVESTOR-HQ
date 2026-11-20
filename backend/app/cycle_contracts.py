"""A single bounded SEC agenda. No caller-supplied URLs, code, universes or trading."""
from datetime import datetime, timedelta, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config import ROOT

AGENDA = 'sec-company-review-v1'
PILOT_CIKS = ('0000320193', '0000789019', '0000104169')
TERMINAL = ('SUCCEEDED', 'PARTIAL', 'BLOCKED', 'CANCELLED', 'TIMED_OUT')


class CycleSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT/'.env', extra='ignore', hide_input_in_errors=True)
    jaime_cycle_token: SecretStr | None = None

    def token(self):
        value = self.jaime_cycle_token.get_secret_value() if self.jaime_cycle_token else ''
        return value if len(value) >= 32 else None


class Budget(BaseModel):
    model_config = ConfigDict(extra='forbid')
    max_sec_tasks: Literal[6] = 6
    max_models: Literal[3] = 3
    max_llm_calls: Literal[0] = 0
    max_cost_eur: Literal[0] = 0
    timeout_seconds: Literal[1200] = 1200


def window(now):
    now = now.astimezone(timezone.utc)
    start = now.replace(hour=(now.hour//6)*6, minute=0, second=0, microsecond=0)
    return start, start+timedelta(hours=6)


def event_for(start):
    return AGENDA+':'+start.strftime('%Y%m%dT%H%M%SZ')


class CycleRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    schema_version: Literal[1]
    agenda: Literal['sec-company-review-v1']
    objective: Literal['SEC_COMPANY_REVIEW']
    mode: Literal['shadow']
    event_id: str = Field(min_length=1, max_length=100)
    correlation_id: str = Field(pattern=r'^[A-Za-z0-9_:-]{1,100}$')
    window_start: datetime
    window_end: datetime
    budget: Budget

    @model_validator(mode='after')
    def valid_window(self):
        if self.window_start.utcoffset() is None or self.window_end.utcoffset() is None:
            raise ValueError('UTC_WINDOW_REQUIRED')
        self.window_start = self.window_start.astimezone(timezone.utc)
        self.window_end = self.window_end.astimezone(timezone.utc)
        start, end = window(self.window_start)
        if (self.window_start, self.window_end) != (start, end) or self.event_id != event_for(start):
            raise ValueError('INVALID_SCHEDULE_WINDOW')
        return self
