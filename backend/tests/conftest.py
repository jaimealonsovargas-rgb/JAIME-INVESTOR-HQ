import socket

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest

from app.config import ROOT, Settings
from app.main import create_app


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setenv('DATA_AUTO_REFRESH_ENABLED', 'false')
    monkeypatch.setenv('AUTONOMY_ENABLED', 'false')
    # asyncio en Windows necesita socketpair sobre loopback para su propio loop.
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def local_only(original):
        def connect(sock, address):
            if not isinstance(address, tuple) or address[0] not in {"127.0.0.1", "::1"}:
                raise AssertionError("Las pruebas P0 no pueden conectar a redes externas.")
            return original(sock, address)
        return connect

    monkeypatch.setattr(socket.socket, "connect", local_only(original_connect))
    monkeypatch.setattr(socket.socket, "connect_ex", local_only(original_connect_ex))


@pytest.fixture
def settings(tmp_path, monkeypatch):
    for key in Settings.model_fields:
        default = Settings.model_fields[key].default
        monkeypatch.setenv(key.upper(), "false" if default is False else str(default))
    database_url = "sqlite:///" + (tmp_path / "test.db").as_posix()
    monkeypatch.setenv("DATABASE_URL", database_url)
    return Settings(_env_file=None)


@pytest.fixture
def migrated(settings):
    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    return settings


@pytest.fixture
def client(migrated):
    with TestClient(create_app(migrated), base_url="http://127.0.0.1") as test_client:
        yield test_client
