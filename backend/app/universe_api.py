import re
from datetime import datetime
from fastapi import APIRouter, Query, Request, HTTPException
from app.universe_contracts import CatalogueSync
from app.storage_budget import StorageBlocked


def router(service):
    api = APIRouter(prefix='/api/universe')

    @api.get('/summary')
    def summary():
        return service.summary()

    @api.get('/listings')
    def listings(q: str = Query('', max_length=120), provider: str | None = Query(None, pattern='^(SEC|ALPACA|ZSE)$'),
                 state: str | None = Query(None, pattern='^(IDENTIFIED|CONFLICT|INCOMPLETE|NOT_OBSERVED)$'),
                 offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
        return service.store.search(q, provider, state, offset, limit)

    @api.get('/listings/{ident}')
    def detail(ident: str, as_of: datetime | None = None):
        if as_of is not None and as_of.utcoffset() is None:
            raise HTTPException(422, 'AS_OF_TIMEZONE_REQUIRED')
        try:
            listing = service.store.detail(ident, as_of)
            if listing['provider'] == 'ZSE':
                from app.universe_zse import close_detail
                listing['historical_close'] = close_detail(service.data, listing, as_of)
                listing['readiness'][0]['reason'] = 'Cobertura limitada a cierres históricos de la acción ordinaria.'
            return listing
        except KeyError:
            raise HTTPException(404, 'LISTING_NOT_KNOWN') from None

    @api.get('/imports/{key}')
    def job(key: str):
        try:
            return service.store.get_import(key)
        except KeyError:
            raise HTTPException(404, 'IMPORT_NOT_FOUND') from None

    @api.post('/sync')
    def sync(body: CatalogueSync, request: Request):
        if request.headers.get('x-hq-universe') != '1' or request.headers.get('origin') not in (
                None, 'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:5174', 'http://localhost:5174'):
            raise HTTPException(403, 'UNIVERSE_ORIGIN_DENIED')
        key = request.headers.get('idempotency-key', '')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{8,128}', key):
            raise HTTPException(400, 'IDEMPOTENCY_KEY_REQUIRED')
        try:
            return service.sync(key, body.provider)
        except StorageBlocked:
            raise
        except ValueError:
            raise HTTPException(409, 'IMPORT_REQUEST_CONFLICT') from None

    return api
