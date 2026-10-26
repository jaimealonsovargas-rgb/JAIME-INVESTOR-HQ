"""First authorized autonomous route. No arbitrary objectives, tools or URLs."""
from typing import Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config import ROOT

POLICY_ID = 'daily-descriptive-v1'
ROLES = ('data_quality', 'momentum_trend', 'volatility_regime')
TERMINAL = frozenset({'SUCCEEDED', 'ABSTAINED', 'FAILED', 'BLOCKED', 'CANCELLED'})


class AutonomySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore', frozen=True)
    autonomy_enabled: bool = True
    autonomy_interval_seconds: int = Field(default=86400, ge=3600, le=604800)
    autonomy_startup_delay_seconds: int = Field(default=30, ge=1, le=300)
    autonomy_source: Literal['A21'] = 'A21'


class Control(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['pause', 'resume']


class UTCContract(BaseModel):
    @field_validator('created_at', 'due_at', 'deadline_at', 'started_at', 'finished_at', check_fields=False)
    @classmethod
    def utc_timestamp(cls, value):
        if value is not None:
            parsed = datetime.fromisoformat(value)
            if parsed.utcoffset() != timedelta(0):
                raise ValueError('UTC_REQUIRED')
        return value


class AutonomyEvent(UTCContract):
    model_config = ConfigDict(extra='forbid')
    id: str
    schema_version: Literal['autonomy-event.v1'] = 'autonomy-event.v1'
    trigger_type: Literal['SCHEDULED_RESEARCH'] = 'SCHEDULED_RESEARCH'
    created_at: str
    due_at: str
    policy_id: Literal['daily-descriptive-v1'] = POLICY_ID
    idempotency_key: str
    source_access_id: Literal['A21'] = 'A21'
    reason_code: Literal['SCHEDULED_DESCRIPTIVE_REVIEW'] = 'SCHEDULED_DESCRIPTIVE_REVIEW'


class ResearchTask(UTCContract):
    model_config = ConfigDict(extra='forbid')
    id: str
    schema_version: Literal['research-task.v1'] = 'research-task.v1'
    event_id: str
    created_at: str
    deadline_at: str
    source_access_id: Literal['A21'] = 'A21'
    reason_code: Literal['SCHEDULED_DESCRIPTIVE_REVIEW'] = 'SCHEDULED_DESCRIPTIVE_REVIEW'
    objective: Literal['DESCRIPTIVE_RESEARCH'] = 'DESCRIPTIVE_RESEARCH'
    state: Literal['QUEUED', 'RUNNING', 'SUCCEEDED', 'ABSTAINED', 'FAILED', 'BLOCKED', 'CANCELLED'] = 'QUEUED'
    phase: Literal['NEW', 'FETCHING', 'PREPARED', 'JOBS'] = 'NEW'
    role_ids: list[str] = Field(default_factory=lambda: list(ROLES))
    subject: dict | None = None
    case_id: str | None = None
    run_key: str
    started_at: str | None = None
    finished_at: str | None = None
    result: dict | None = None
    budget: dict = Field(default_factory=lambda: {'llm_calls_max': 0, 'deadline_seconds': 90, 'fetches_max': 1, 'attempts_max': 1})

    @field_validator('role_ids')
    @classmethod
    def descriptive_roles_only(cls, value):
        if tuple(value) != ROLES:
            raise ValueError('AUTONOMY_ROLES_DENIED')
        return value

    @field_validator('budget')
    @classmethod
    def fixed_bounded_budget(cls, value):
        if value != {'llm_calls_max': 0, 'deadline_seconds': 90, 'fetches_max': 1, 'attempts_max': 1}:
            raise ValueError('AUTONOMY_BUDGET_DENIED')
        return value
