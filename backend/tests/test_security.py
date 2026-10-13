import pytest
from pydantic import ValidationError

from app.config import Settings
from app.providers import DisabledPaperBroker
from app.security import ExecutionUnavailable, PAPER_BASE_URLS, PaperOnlyViolation, validate_paper_endpoint


@pytest.mark.parametrize("value", [True, "true", "1", "TRUE", "yes", 1, "on"])
def test_live_flag_cannot_enable_execution(settings, monkeypatch, value):
    monkeypatch.setenv("LIVE_TRADING_ENABLED", str(value))
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_example_config_is_valid(settings):
    from app.config import ROOT
    assert Settings(_env_file=ROOT / ".env.example").live_trading_enabled is False


@pytest.mark.parametrize("key,value", [
    ("ALPACA_ENVIRONMENT", "live"), ("TRADING212_ENVIRONMENT", "live"),
    ("ALPACA_BASE_URL", "https://api.alpaca.markets"),
    ("TRADING212_BASE_URL", "https://live.trading212.com/api/v0"),
    ("DATABASE_URL", "postgresql://localhost/test"),
    ("DATABASE_URL", "sqlite:///file:test?uri=true"),
    ("DATABASE_URL", "sqlite:///:memory:"),
    ("DATABASE_URL", "sqlite://///server/share/test.db"),
])
def test_unsafe_configuration_is_rejected(settings, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("url", [
    "https://api.alpaca.markets", "https://live.trading212.com/api/v0",
    "http://paper-api.alpaca.markets", "https://paper-api.alpaca.markets.evil.example",
    "https://paper-api.alpaca.markets@evil.example", "https://evil.example@paper-api.alpaca.markets",
    "https://paper-api.alpaca.markets:443", "https://paper-api.alpaca.markets?redirect=live",
    "https://paper-api.alpaca.markets#fragment", "https://paper-api.alpaca.markets/../live",
    "https://paper-api.alpaca.markets/", "https://127.0.0.1", " https://paper-api.alpaca.markets",
])
def test_exact_allowlist_rejects_live_and_url_bypasses(url):
    with pytest.raises(PaperOnlyViolation):
        validate_paper_endpoint("ALPACA_PAPER", url)
    with pytest.raises(PaperOnlyViolation):
        DisabledPaperBroker("ALPACA_PAPER", url)


def test_unknown_provider_rejected():
    with pytest.raises(PaperOnlyViolation):
        validate_paper_endpoint("LIVE", "https://paper-api.alpaca.markets")


@pytest.mark.parametrize("provider,url", PAPER_BASE_URLS.items())
def test_even_valid_paper_brokers_cannot_submit(provider, url):
    broker = DisabledPaperBroker(provider, url)
    with pytest.raises(ExecutionUnavailable):
        broker.submit_order()


@pytest.mark.parametrize("body", [{"mode": "live"}, {"mode": "paper"}, {"risk_approved": True, "kill_switch": False}, {}])
def test_all_order_requests_blocked(client, body):
    response = client.post("/api/orders", json=body)
    assert response.status_code == 403
    assert response.json()["code"] == "P0_EXECUTION_DISABLED"


def test_no_secret_fields_or_order_transport(client, monkeypatch):
    marker = "TEST_ONLY_SECRET_SENTINEL"
    monkeypatch.setenv("ALPACA_API_KEY", marker)
    monkeypatch.setenv("TRADING212_API_SECRET", marker)
    assert marker not in repr(Settings(_env_file=None))
    for url in ["/health", "/api/providers/status", "/api/instruments", "/openapi.json"]:
        assert marker not in client.get(url).text
    assert client.put("/api/orders").status_code == 405
    assert client.post("/api/live/orders").status_code == 404
