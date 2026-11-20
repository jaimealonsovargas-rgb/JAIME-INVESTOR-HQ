import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict
from app.sec_api import write_access


class BuildRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    as_of: datetime | None = None


def router(service):
    api = APIRouter(prefix='/api/universe')

    def call(fn, *args):
        try:
            return fn(*args)
        except PermissionError:
            raise HTTPException(403, 'SOURCE_UNAVAILABLE') from None
        except KeyError:
            raise HTTPException(404, 'MODEL_NOT_FOUND') from None
        except ValueError as error:
            raise HTTPException(409, str(error)) from None

    @api.get('/models/recent')
    def recent():
        return call(service.recent)

    @api.get('/issuers/{cik}/model-updates')
    def updates(cik: str):
        from sqlalchemy import select
        from app.company_updates import EVENTS
        from app.sec_normalize import cik_text
        def read():
            service.readable()
            with service.engine.connect() as c:
                return [dict(r) for r in c.execute(select(EVENTS).where(EVENTS.c.cik == cik_text(cik))
                    .order_by(EVENTS.c.received_at.desc()).limit(20)).mappings()]
        return call(read)

    @api.get('/issuers/{cik}/models')
    def versions(cik: str, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)):
        return call(service.versions, cik, offset, limit)

    @api.post('/issuers/{cik}/models')
    def build(cik: str, body: BuildRequest, request: Request):
        write_access(request)
        key = request.headers.get('idempotency-key', '')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{8,128}', key):
            raise HTTPException(400, 'IDEMPOTENCY_KEY_REQUIRED')
        return call(service.build, cik, key, body.as_of)

    @api.get('/issuers/{cik}/models/{ident}')
    def detail(cik: str, ident: str):
        return call(service.get, cik, ident)

    return api
