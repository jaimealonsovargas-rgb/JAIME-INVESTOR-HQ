"""Catalogue identities are evidence, not executable instruments or past universes."""
from typing import Literal
from pydantic import Field, model_validator
from app.contracts import Contract


class CatalogueRow(Contract):
    provider: Literal['SEC', 'ALPACA']
    provider_key: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=500)
    symbol: str = Field(min_length=1, max_length=120)
    venue: str = Field(min_length=1, max_length=120)
    cik: str | None = Field(default=None, pattern=r'^[0-9]{10}$')
    currency: str | None = Field(default=None, pattern=r'^[A-Z]{3}$')
    category: Literal['UNCLASSIFIED', 'US_EQUITY'] = 'UNCLASSIFIED'
    provider_status: str | None = None
    provider_tradable: bool | None = None

    @model_validator(mode='after')
    def issuer(self):
        if self.provider == 'SEC' and (not self.cik or int(self.cik) == 0):
            raise ValueError('SEC_CIK_REQUIRED')
        return self


class CatalogueSync(Contract):
    provider: Literal['SEC', 'ALPACA'] = 'SEC'


def parse_catalogue(provider, body):
    """Validate the whole snapshot before changing current identity assertions."""
    if provider == 'SEC':
        if not isinstance(body, dict) or not isinstance(body.get('fields'), list):
            raise ValueError('CATALOGUE_SHAPE')
        fields = body['fields']
        if len(set(fields)) != len(fields) or not {'cik', 'name', 'ticker', 'exchange'} <= set(fields):
            raise ValueError('CATALOGUE_FIELDS')
        raw = body.get('data')
    elif provider == 'ALPACA':
        raw = body
    else:
        raise ValueError('UNKNOWN_CATALOGUE')
    if not isinstance(raw, list) or not 1 <= len(raw) <= 100000:
        raise ValueError('CATALOGUE_SIZE')
    rows = []
    for item in raw:
        if provider == 'SEC':
            if not isinstance(item, list) or len(item) != len(fields):
                raise ValueError('CATALOGUE_ROW')
            value = dict(zip(fields, item))
            cik = str(value['cik'])
            if not cik.isascii() or not cik.isdigit() or not 1 <= len(cik) <= 10:
                raise ValueError('CATALOGUE_CIK')
            symbol, name = value['ticker'], value['name']
            venue = value['exchange'] or 'UNKNOWN'
            if not all(isinstance(v, str) for v in (symbol, name, venue)):
                raise ValueError('CATALOGUE_TEXT')
            symbol, name, venue = symbol.strip().upper(), name.strip(), venue.strip().upper()
            row = CatalogueRow(provider=provider, provider_key=f'{cik.zfill(10)}:{symbol}:{venue}',
                               cik=cik.zfill(10), symbol=symbol, name=name, venue=venue)
        else:
            from uuid import UUID
            if not isinstance(item, dict) or item.get('class') != 'us_equity':
                raise ValueError('CATALOGUE_ASSET_CLASS')
            if item.get('status') not in ('active', 'inactive') or type(item.get('tradable')) is not bool:
                raise ValueError('CATALOGUE_STATUS')
            row = CatalogueRow(provider=provider, provider_key=str(UUID(item['id'])),
                               symbol=item['symbol'], name=item['name'], venue=item['exchange'],
                               category='US_EQUITY', provider_status=item['status'], provider_tradable=item['tradable'])
        if any(ord(c) < 32 for text in (row.name, row.symbol, row.venue) for c in text):
            raise ValueError('CATALOGUE_CONTROL_CHAR')
        rows.append(row)
    keys = {}
    for row in rows:
        if row.provider_key in keys and keys[row.provider_key] != row:
            raise ValueError('CATALOGUE_CONTRADICTORY_ID')
        keys[row.provider_key] = row
    return list(keys.values())
