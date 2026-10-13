from typing import Protocol
from uuid import UUID

from app.contracts import Instrument, ProviderStatus, Quote
from app.security import deny_order_execution, validate_paper_endpoint


class DataUnavailable(RuntimeError):
    pass


class MarketDataProvider(Protocol):
    def status(self) -> ProviderStatus: ...
    def instruments(self) -> list[Instrument]: ...
    def quote(self, instrument_id: UUID) -> Quote: ...


class UnavailableProvider:
    def __init__(self, name: str):
        self.name = name

    def status(self) -> ProviderStatus:
        return ProviderStatus(provider=self.name, reason="Adaptador no implementado en P0; acceso no comprobado.")

    def instruments(self) -> list[Instrument]:
        raise DataUnavailable("NO DISPONIBLE: catálogo externo no conectado.")

    def quote(self, instrument_id: UUID) -> Quote:
        raise DataUnavailable("NO DISPONIBLE: no existe un feed conectado.")


class DisabledPaperBroker:
    """Interfaz separada de los datos. No contiene transporte HTTP ni credenciales."""

    def __init__(self, provider: str, base_url: str):
        self.base_url = validate_paper_endpoint(provider, base_url)

    def submit_order(self) -> None:
        deny_order_execution()


def provider_statuses() -> list[ProviderStatus]:
    return [UnavailableProvider(name).status() for name in ("ALPACA_PAPER", "T212_DEMO", "TWELVE_DATA")]
