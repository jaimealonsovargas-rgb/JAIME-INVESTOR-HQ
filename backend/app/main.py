from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
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


def create_app(settings: Settings | None = None) -> FastAPI:
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
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
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
    def instruments():
        with Session(engine) as session:
            return InstrumentRegistry(session).list()

    @app.post("/api/orders", response_model=ApiError, responses={403: {"model": ApiError}})
    def blocked_order():
        deny_order_execution()

    return app
