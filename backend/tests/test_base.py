from datetime import datetime, timezone
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import ROOT
from app.contracts import Instrument, ProviderCapability, Quote
from app.database import InstrumentRegistry, create_db_engine
from app.main import create_app
from app.providers import DataUnavailable, UnavailableProvider


def test_health_and_empty_registry(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["trading_mode"] == "PAPER_ONLY"
    assert data["orders_enabled"] is False
    assert data["database"] == "ok"
    assert data["schema_version"] == "0003_portfolio"
    assert datetime.fromisoformat(data["checked_at"]).tzinfo is not None
    assert client.get("/api/instruments").json() == []


def test_providers_are_unverified_not_fake(client):
    result = client.get("/api/providers/status").json()
    assert len(result) == 3
    assert all(p["status"] == "NO DISPONIBLE" and p["checked_at"] is None for p in result)
    provider = UnavailableProvider("TEST_FIXTURE")
    with pytest.raises(DataUnavailable):
        provider.quote(uuid4())
    with pytest.raises(DataUnavailable):
        provider.instruments()


def test_cors_and_host_restrictions(client):
    response = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    response = client.get("/health", headers={"Origin": "https://example.org"})
    assert "access-control-allow-origin" not in response.headers
    assert client.get("/health", headers={"Host": "attacker.example"}).status_code == 400
    assert client.options("/api/orders", headers={
        "Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST",
    }).status_code == 400


def test_requires_explicit_migration(settings):
    with pytest.raises(RuntimeError, match="migrate"):
        with TestClient(create_app(settings), base_url="http://127.0.0.1"):
            pass


def test_health_checks_current_database(client):
    with client.app.state.engine.begin() as connection:
        connection.execute(text("DROP TABLE instruments"))
    assert client.get("/health").status_code == 503
    response = client.get("/api/instruments")
    assert response.status_code == 503
    assert response.json()["code"] == "DATABASE_UNAVAILABLE"
    assert "SELECT" not in response.text


def test_wal_foreign_keys_migration_reversible(migrated):
    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")  # idempotente
    engine = create_db_engine(migrated.database_url)
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1
    engine.dispose()
    command.downgrade(config, "base")
    engine = create_db_engine(migrated.database_url)
    assert "instruments" not in inspect(engine).get_table_names()
    engine.dispose()
    command.upgrade(config, "head")
    command.check(config)  # sin drift entre modelos y migración


def test_registry_persists_exact_contract_and_unique_market(migrated):
    # Instrumento ficticio SOLO como fixture, nunca cargado en la aplicación.
    instrument = Instrument(id=uuid4(), symbol="TEST_ONLY", venue="TEST", currency="EUR", asset_class="BOND_ETF")
    engine = create_db_engine(migrated.database_url)
    with Session(engine) as session, session.begin():
        InstrumentRegistry(session).add(instrument)
    engine.dispose()
    engine = create_db_engine(migrated.database_url)
    with Session(engine) as session:
        assert InstrumentRegistry(session).list() == [instrument]
        with pytest.raises(IntegrityError):
            InstrumentRegistry(session).add(instrument.model_copy(update={"id": uuid4()}))
        session.rollback()
    engine.dispose()
    with TestClient(create_app(migrated), base_url="http://127.0.0.1") as client:
        assert client.get("/api/instruments").json()[0]["asset_class"] == "BOND_ETF"


def test_capabilities_require_evidence():
    with pytest.raises(ValidationError):
        ProviderCapability(provider="TEST", research=True, reason="fixture")
    capability = ProviderCapability(provider="TEST", research=True, reason="fixture", license="TEST_ONLY", checked_at=datetime.now(timezone.utc))
    assert capability.research and not capability.broker_paper


def test_decimal_and_quote_provenance():
    quote = Quote(instrument_id=uuid4(), price="0.1234567890123456789", provider="TEST_ONLY", as_of=datetime.now(timezone.utc), currency="EUR", delay_seconds=900, quality_flags=("TEST_ONLY",))
    assert quote.model_dump(mode="json")["price"] == "0.1234567890123456789"
    with pytest.raises(ValidationError):
        Quote.model_validate({**quote.model_dump(), "as_of": datetime(2026, 1, 1)})


def test_api_schema_has_typed_contracts(client):
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {"/health", "/api/providers/status", "/api/instruments", "/api/orders", "/api/data/quality", "/api/data/sources/{access_id}", "/api/hq/overview", '/api/markets/watchlist', *('/api/portfolio/master/'+p for p in ('summary','positions','ledger','nav/history','performance'))}
    assert schema["paths"]["/api/orders"]["post"]["responses"]["403"]
