from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import Settings
from app.contracts import ApiError, Health, Instrument, ProviderStatus
from app.database import SCHEMA_VERSION, InstrumentRegistry, check_database, create_db_engine
from app.providers import provider_statuses
from app.security import ExecutionUnavailable, deny_order_execution
from app.data_config import DataSettings
from app.data_service import DataService
from app.data_catalog import CATALOG
from app.data_contracts import DataResult


def create_app(settings: Settings | None = None, data_settings: DataSettings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = create_db_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            check_database(engine)
        except (SQLAlchemyError, RuntimeError):
            engine.dispose()
            raise RuntimeError("Base no preparada: ejecutar python scripts/manage.py migrate.") from None
        try:
            yield
        finally:
            engine.dispose()

    # El contrato OpenAPI es local; no cargar Swagger/ReDoc desde un CDN externo.
    app = FastAPI(title="JAIME INVESTOR HQ · P0", version="0.0.1", lifespan=lifespan,
                  docs_url=None, redoc_url=None)
    app.state.engine = engine
    app.state.data = DataService(engine, data_settings)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:5174", "http://localhost:5174"],
        allow_methods=["GET"], allow_headers=["Accept"], allow_credentials=False,
    )

    @app.exception_handler(ExecutionUnavailable)
    async def execution_blocked(_request: Request, _exc: ExecutionUnavailable):
        return JSONResponse(status_code=403, content=ApiError(
            code="P0_EXECUTION_DISABLED", message="NO DISPONIBLE: todas las órdenes están bloqueadas en P0.",
        ).model_dump())

    @app.exception_handler(SQLAlchemyError)
    async def database_unavailable(_request: Request, _exc: SQLAlchemyError):
        return JSONResponse(status_code=503, content=ApiError(
            code="DATABASE_UNAVAILABLE", message="NO DISPONIBLE: base de datos local.",
        ).model_dump())

    @app.get("/health", response_model=Health, responses={503: {"model": ApiError}})
    def health():
        try:
            check_database(engine)
        except (SQLAlchemyError, RuntimeError):
            return JSONResponse(status_code=503, content=ApiError(
                code="DATABASE_UNAVAILABLE", message="NO DISPONIBLE: base de datos o migración.",
            ).model_dump())
        return Health(schema_version=SCHEMA_VERSION, checked_at=datetime.now(timezone.utc))

    @app.get("/api/providers/status", response_model=list[ProviderStatus])
    def providers():
        return provider_statuses()

    @app.get("/api/instruments", response_model=list[Instrument], responses={503: {"model": ApiError}})
    def instruments(q: str | None = Query(default=None,max_length=120), offset: int = Query(default=0,ge=0), limit: int = Query(default=1000,ge=1,le=1000)):
        with Session(engine) as session:
            return InstrumentRegistry(session).list(q,offset,limit)

    @app.get('/api/data/quality')
    def data_quality():
        return app.state.data.quality()

    @app.get('/api/data/sources/{access_id}', response_model=DataResult)
    def data_source(access_id: str):
        if access_id not in CATALOG:
            return JSONResponse(status_code=404,content=ApiError(code='UNKNOWN_SOURCE',message='Fuente no registrada.').model_dump())
        return app.state.data.query(access_id)

    @app.post("/api/orders", response_model=ApiError, responses={403: {"model": ApiError}})
    def blocked_order():
        deny_order_execution()

    return app
