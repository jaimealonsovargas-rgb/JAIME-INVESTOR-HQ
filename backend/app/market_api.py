"""Local read-only market workflow; no arbitrary URLs, feeds or trading actions."""
import re
from datetime import date
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.sec_api import write_access


class MarketRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['connection', 'catalogue', 'snapshot', 'history']
    listing_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    start: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    end: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    adjustment: Literal['raw', 'split', 'all'] | None = None

    @model_validator(mode='after')
    def scope(self):
        if (self.kind in ('snapshot', 'history')) != bool(self.listing_id):
            raise ValueError('LISTING_SCOPE_INVALID')
        if self.kind == 'history':
            if self.start is None or self.end is None:
                raise ValueError('HISTORY_DATES_REQUIRED')
            date.fromisoformat(self.start)
            date.fromisoformat(self.end)
            self.adjustment = self.adjustment or 'raw'
        elif any(v is not None for v in (self.start, self.end, self.adjustment)):
            raise ValueError('HISTORY_FIELDS_FORBIDDEN')
        return self


class Control(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['cancel', 'resume']


def router(service):
    api = APIRouter(prefix='/api/universe')

    @api.get('/market/summary')
    def summary():
        return service.summary()

    @api.post('/market/jobs', status_code=202)
    def enqueue(body: MarketRequest, request: Request):
        write_access(request)
        key = request.headers.get('idempotency-key', '')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{8,128}', key):
            raise HTTPException(400, 'IDEMPOTENCY_KEY_REQUIRED')
        try:
            return service.enqueue(key, body.model_dump(exclude_none=True))
        except KeyError:
            raise HTTPException(404, 'LISTING_NOT_KNOWN') from None
        except ValueError as error:
            raise HTTPException(409, str(error)) from None

    @api.get('/market/jobs/{key}')
    def job(key: str):
        try:
            return service.store.job(key)
        except KeyError:
            raise HTTPException(404, 'IMPORT_NOT_FOUND') from None

    @api.post('/market/jobs/{key}/control')
    def control(key: str, body: Control, request: Request):
        write_access(request)
        if body.action == 'resume' and service.access() != 'READY_TO_FETCH':
            raise HTTPException(409, service.access())
        try:
            return service.store.control(key, body.action, service.data.clock())
        except KeyError:
            raise HTTPException(404, 'IMPORT_NOT_FOUND') from None
        except ValueError as error:
            raise HTTPException(409, str(error)) from None

    @api.get('/listings/{ident}/market')
    def detail(ident: str, adjustment: Literal['raw', 'split', 'all'] = Query('raw')):
        if service.access() == 'DISABLED':
            raise HTTPException(403, 'SOURCE_DISABLED')
        try:
            return service.detail(ident, adjustment)
        except KeyError:
            raise HTTPException(404, 'LISTING_NOT_KNOWN') from None

    return api
