from pathlib import Path

from sqlalchemy import JSON, String, UniqueConstraint, create_engine, event, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.contracts import Instrument

SCHEMA_VERSION = "0001_instruments"


class Base(DeclarativeBase):
    pass


class InstrumentRecord(Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("symbol", "venue", "currency", name="uq_instrument_market"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(120))
    venue: Mapped[str] = mapped_column(String(120))
    currency: Mapped[str] = mapped_column(String(3))
    payload: Mapped[dict] = mapped_column(JSON)


def create_db_engine(database_url: str) -> Engine:
    path = Path(make_url(database_url).database)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    return engine


def check_database(engine: Engine) -> None:
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        if revision != SCHEMA_VERSION:
            raise RuntimeError("Migración pendiente.")
        connection.execute(select(InstrumentRecord.id).limit(1))


class InstrumentRegistry:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Instrument]:
        rows = self.session.scalars(select(InstrumentRecord).order_by(InstrumentRecord.symbol))
        return [Instrument.model_validate(row.payload) for row in rows]

    def add(self, instrument: Instrument) -> None:
        self.session.add(InstrumentRecord(
            id=str(instrument.id), symbol=instrument.symbol, venue=instrument.venue,
            currency=instrument.currency, payload=instrument.model_dump(mode="json"),
        ))
        self.session.flush()
