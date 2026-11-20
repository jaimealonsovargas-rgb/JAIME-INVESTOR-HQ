"""D2 collection contracts; claims of historical identity/admission stay pending."""
from datetime import date, timedelta
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

Id = Annotated[str,Field(min_length=1,max_length=128,pattern=r'^[A-Za-z0-9_.:-]+$')]
Hash = Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]


class Contract(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True,hide_input_in_errors=True)
    conId: Annotated[StrictInt,Field(gt=0)]
    symbol: Annotated[str,Field(min_length=1,max_length=40,pattern=r'^[A-Za-z0-9 ._-]+$')]
    secType: Literal['STK']='STK'
    exchange: Literal['SMART']='SMART'
    primaryExchange: Annotated[str,Field(min_length=1,max_length=24,pattern=r'^[A-Za-z0-9._-]+$')]
    currency: Annotated[str,Field(pattern=r'^[A-Z]{3}$')]


class Target(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True)
    listing_id: Id
    identity_hash: Hash
    contract: Contract


class BatchRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True,hide_input_in_errors=True)
    provider: Literal['IBKR_TWS','SYNTHETIC_TEST']
    targets: Annotated[tuple[Target,...],Field(min_length=1,max_length=5000)]
    start: date
    end: date
    frequency: Literal['1 day']='1 day'
    adjustment: Literal['SPLIT_ADJUSTED_NOT_DIVIDENDS']='SPLIT_ADJUSTED_NOT_DIVIDENDS'
    what_to_show: Literal['TRADES']='TRADES'
    use_rth: Literal[True]=True
    revision: Id='v1'

    @model_validator(mode='after')
    def coherent(self):
        if not self.start<=self.end or (self.end-self.start).days>3660:
            raise ValueError('INVALID_HISTORY_RANGE')
        if len({t.listing_id for t in self.targets})!=len(self.targets):
            raise ValueError('DUPLICATE_TARGET')
        if len({t.contract.conId for t in self.targets})!=len(self.targets):
            raise ValueError('DUPLICATE_CONTRACT')
        for target in self.targets:
            if self.provider=='SYNTHETIC_TEST' and not (target.listing_id.startswith('TEST_') and target.contract.symbol.startswith('TEST_')):
                raise ValueError('SYNTHETIC_NAMESPACE_REQUIRED')
            if self.provider=='IBKR_TWS' and (target.listing_id.startswith('TEST_') or target.contract.symbol.startswith('TEST_')):
                raise ValueError('SYNTHETIC_TARGET_IN_REAL_REQUEST')
        if len(self.targets)*(((self.end-self.start).days//31)+1)>20000:
            raise ValueError('BATCH_UNIT_BUDGET')
        return self

    def units(self):
        for target in self.targets:
            cursor=self.start
            while cursor<=self.end:
                end=min(self.end,cursor+timedelta(days=30))
                yield dict(provider=self.provider,**target.model_dump(mode='json'),start=cursor.isoformat(),end=end.isoformat(),
                    frequency=self.frequency,adjustment=self.adjustment,what_to_show=self.what_to_show,
                    use_rth=self.use_rth,revision=self.revision)
                cursor=end+timedelta(days=1)
