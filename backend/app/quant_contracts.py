"""B3.1 engineering contracts. No provider dataset or execution approval here."""
from datetime import timedelta
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, hide_input_in_errors=True)


Amount = Annotated[Decimal, Field(ge=0, le=1_000_000_000, max_digits=18, decimal_places=6)]


class Costs(Contract):
    fixed_per_fill: Amount
    commission_bps: Annotated[Decimal, Field(ge=0, le=100, decimal_places=4)]
    slippage_bps: Annotated[Decimal, Field(ge=0, le=100, decimal_places=4)]
    fee_rounding: Literal['CENT_HALF_UP'] = 'CENT_HALF_UP'
    slippage_includes_spread: Literal[True] = True

    @field_validator('fixed_per_fill', 'commission_bps', 'slippage_bps', mode='before')
    @classmethod
    def decimal_text(cls, value):
        if not isinstance(value, (str, Decimal)):
            raise ValueError('DECIMAL_TEXT_REQUIRED')
        return value


class StrategyGenome(Contract):
    version: Literal['daily-trend-v1'] = 'daily-trend-v1'
    family: Literal['SMA_LONG_CASH', 'CASH', 'BUY_HOLD']
    lookback: Annotated[StrictInt, Field(ge=2, le=252)] | None = None
    mechanism: Annotated[str, Field(min_length=10, max_length=500)]
    falsification: Annotated[str, Field(min_length=10, max_length=500)]
    sizing: Literal['WHOLE_SHARES_ALL_IN_NO_LEVERAGE'] = 'WHOLE_SHARES_ALL_IN_NO_LEVERAGE'
    timing: Literal['CLOSE_SIGNAL_NEXT_OPEN'] = 'CLOSE_SIGNAL_NEXT_OPEN'
    protocol: Literal['SYNTHETIC_ENGINE_CHECK'] = 'SYNTHETIC_ENGINE_CHECK'

    @model_validator(mode='after')
    def parameters(self):
        if (self.family == 'SMA_LONG_CASH') != (self.lookback is not None):
            raise ValueError('LOOKBACK_FAMILY_MISMATCH')
        return self


class Bar(Contract):
    opens_at: AwareDatetime
    closes_at: AwareDatetime
    available_at: AwareDatetime
    open: Annotated[Decimal, Field(gt=0, le=1_000_000, max_digits=13, decimal_places=6)]
    close: Annotated[Decimal, Field(gt=0, le=1_000_000, max_digits=13, decimal_places=6)]

    @field_validator('open', 'close', mode='before')
    @classmethod
    def decimal_text(cls, value):
        return Costs.decimal_text(value)

    @model_validator(mode='after')
    def chronology(self):
        if not self.opens_at < self.closes_at <= self.available_at:
            raise ValueError('BAR_CHRONOLOGY')
        return self


class SyntheticDataset(Contract):
    version: Literal['synthetic-bars-v1'] = 'synthetic-bars-v1'
    kind: Literal['SYNTHETIC_TEST']
    instrument: Literal['TEST_ONLY']
    currency: Literal['TEST_CCU']
    calendar: Literal['EXPLICIT_SYNTHETIC_SESSIONS']
    adjustments: Literal['NO_CORPORATE_ACTIONS_SYNTHETIC']
    bars: Annotated[tuple[Bar, ...], Field(min_length=3, max_length=2048)]

    @model_validator(mode='after')
    def chronology(self):
        for previous, current in zip(self.bars, self.bars[1:]):
            if previous.available_at >= current.opens_at or current.opens_at - previous.opens_at < timedelta(hours=20):
                raise ValueError('DAILY_CHRONOLOGY')
        return self


class ExperimentConfig(Contract):
    genome: StrategyGenome
    costs: Costs
    initial_cash: Annotated[Decimal, Field(gt=0, le=1_000_000_000, decimal_places=2)]
    unit: Literal['TEST_CCU'] = 'TEST_CCU'
    seed: Literal[0] = 0  # No randomness in the reference engine.

    @field_validator('initial_cash', mode='before')
    @classmethod
    def decimal_text(cls, value):
        return Costs.decimal_text(value)
