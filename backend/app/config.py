from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore",
        frozen=True, hide_input_in_errors=True,
    )

    live_trading_enabled: Literal[False] = False
    alpaca_environment: Literal["paper"] = "paper"
    trading212_environment: Literal["demo"] = "demo"
    alpaca_base_url: Literal["https://paper-api.alpaca.markets"] = "https://paper-api.alpaca.markets"
    trading212_base_url: Literal["https://demo.trading212.com/api/v0"] = "https://demo.trading212.com/api/v0"
    database_url: str = "sqlite:///./data/jaime_hq.db"

    @field_validator("live_trading_enabled", mode="before")
    @classmethod
    def reject_live(cls, value):
        if value is False or value == "false":
            return False
        raise ValueError("LIVE trading está prohibido; solo se admite false.")

    @field_validator("database_url")
    @classmethod
    def local_sqlite_only(cls, value: str) -> str:
        try:
            url = make_url(value)
        except ArgumentError:
            raise ValueError("DATABASE_URL no válida.") from None
        if (url.drivername != "sqlite" or url.host or url.username or url.password
                or url.query or not url.database or url.database == ":memory:"):
            raise ValueError("Solo se permite SQLite local persistente sin parámetros URI.")
        path = Path(url.database)
        if str(path).startswith(("\\\\", "//")):
            raise ValueError("No se permiten bases de datos de red.")
        if not path.is_absolute():
            path = ROOT / path
        return "sqlite:///" + path.resolve().as_posix()
