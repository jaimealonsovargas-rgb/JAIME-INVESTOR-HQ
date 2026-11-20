import re
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.sec_normalize import METRICS, cik_text


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ciks: list[str] | None = Field(default=None, min_length=1, max_length=100)

    @field_validator('ciks')
    @classmethod
    def valid_ciks(cls, value):
        if value is None:
            return value
        result = [cik_text(v) for v in value]
        if len(set(result)) != len(result):
            raise ValueError('DUPLICATE_ISSUER')
        return result


class ControlRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['pause', 'resume', 'cancel']


def write_access(request):
    if request.headers.get('x-hq-universe') != '1' or request.headers.get('origin') not in (
            None, 'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:5174', 'http://localhost:5174'):
        raise HTTPException(403, 'UNIVERSE_ORIGIN_DENIED')


def router(service):
    api = APIRouter(prefix='/api/universe')

    def temporal(as_of):
        if as_of is None:
            return service.data.clock()
        if as_of.utcoffset() is None:
            raise HTTPException(422, 'AS_OF_TIMEZONE_REQUIRED')
        return as_of.astimezone(timezone.utc)

    def readable(cik):
        try:
            cik = cik_text(cik)
        except ValueError:
            raise HTTPException(422, 'INVALID_CIK') from None
        if service.access() in ('DISABLED', 'RIGHTS_RESTRICTED'):
            raise HTTPException(403, 'SOURCE_UNAVAILABLE')
        return cik

    @api.get('/financials/summary')
    def summary():
        return service.summary()

    @api.post('/financials/jobs', status_code=202)
    def enqueue(body: ImportRequest, request: Request):
        write_access(request)
        key = request.headers.get('idempotency-key', '')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{8,128}', key):
            raise HTTPException(400, 'IDEMPOTENCY_KEY_REQUIRED')
        try:
            return service.enqueue(key, body.ciks)
        except ValueError as error:
            raise HTTPException(409, str(error)) from None

    @api.get('/financials/jobs/{key}')
    def job(key: str):
        try:
            return service.store.job(key)
        except KeyError:
            raise HTTPException(404, 'IMPORT_NOT_FOUND') from None

    @api.post('/financials/jobs/{key}/control')
    def control(key: str, body: ControlRequest, request: Request):
        write_access(request)
        try:
            return service.store.control(key, body.action, service.data.clock())
        except KeyError:
            raise HTTPException(404, 'IMPORT_NOT_FOUND') from None
        except ValueError as error:
            raise HTTPException(409, str(error)) from None

    @api.get('/issuers/{cik}/financials')
    def financials(cik: str, as_of: datetime | None = None):
        return service.store.financials(readable(cik), temporal(as_of))

    @api.get('/issuers/{cik}/documents')
    def documents(cik: str, as_of: datetime | None = None, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100)):
        return service.store.documents(readable(cik), temporal(as_of), offset, limit)

    @api.get('/issuers/{cik}/facts')
    def facts(cik: str, metric: str, as_of: datetime | None = None, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100)):
        if metric not in METRICS:
            raise HTTPException(422, 'UNKNOWN_METRIC')
        return service.store.fact_history(readable(cik), metric, temporal(as_of), offset, limit)

    return api
