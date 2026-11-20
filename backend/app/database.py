from pathlib import Path

from sqlalchemy import JSON, String, UniqueConstraint, ForeignKey, Integer, create_engine, event, select, text, or_, func
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.contracts import Instrument

SCHEMA_VERSION = "0015_history_batches"


class Base(DeclarativeBase):
    pass


from app.portfolio_schema import register as register_portfolio_schema
register_portfolio_schema(Base.metadata)
from app.research_schema import register as register_research_schema
register_research_schema(Base.metadata)
from app.autonomy_schema import register as register_autonomy_schema
register_autonomy_schema(Base.metadata)
from app.universe_schema import register as register_universe_schema
register_universe_schema(Base.metadata)
from app.sec_schema import register as register_sec_schema
register_sec_schema(Base.metadata)
from app.market_schema import register as register_market_schema
register_market_schema(Base.metadata)
from app.company_schema import register as register_company_schema
register_company_schema(Base.metadata)
from app.cycle_schema import register as register_cycle_schema
register_cycle_schema(Base.metadata)
from app.quant_schema import register as register_quant_schema
register_quant_schema(Base.metadata)
from app.history_schema import register as register_history_schema
register_history_schema(Base.metadata)


class InstrumentRecord(Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("symbol", "venue", "currency", "asset_class", name="uq_instrument_identity"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(120))
    venue: Mapped[str] = mapped_column(String(120))
    currency: Mapped[str] = mapped_column(String(12))
    asset_class: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON)


class InstrumentAlias(Base):
    __tablename__ = 'instrument_aliases'
    __table_args__ = (UniqueConstraint('provider', 'symbol', 'venue', 'currency', name='uq_alias_identity'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey('instruments.id'))
    provider: Mapped[str] = mapped_column(String(100))
    symbol: Mapped[str] = mapped_column(String(120))
    venue: Mapped[str] = mapped_column(String(120))
    currency: Mapped[str] = mapped_column(String(12))
    source: Mapped[str] = mapped_column(String(500))
    verified_at: Mapped[str] = mapped_column(String(40))
    expires_at: Mapped[str | None] = mapped_column(String(40))


class DataRecord(Base):
    __tablename__ = 'data_records'
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    expires_at: Mapped[str] = mapped_column(String(40))
    updated_at: Mapped[str] = mapped_column(String(40))


class DataQuota(Base):
    __tablename__ = 'data_quotas'
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    window_start: Mapped[str] = mapped_column(String(40))
    used: Mapped[int] = mapped_column(Integer)
    blocked_until: Mapped[str | None] = mapped_column(String(40))
    failures: Mapped[int] = mapped_column(Integer, default=0)


class DataObservation(Base):
    """Authorized observations survive cache replacement; revisions remain separate."""
    __tablename__ = 'data_observations'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    access_id: Mapped[str] = mapped_column(String(8), index=True)
    source_identity: Mapped[str] = mapped_column(String(120))
    observed_at: Mapped[str] = mapped_column(String(40), index=True)
    received_at: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON)


class DataDownload(Base):
    """Immutable receipt: original bytes hash, retrieval time and revision IDs."""
    __tablename__ = 'data_downloads'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_identity: Mapped[str] = mapped_column(String(120), index=True)
    received_at: Mapped[str] = mapped_column(String(40))
    payload_hash: Mapped[str] = mapped_column(String(64))
    observation_ids: Mapped[list] = mapped_column(JSON)


class DataRefresh(Base):
    __tablename__ = 'data_refresh'
    access_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    next_due_at: Mapped[str] = mapped_column(String(40))
    attempted_at: Mapped[str | None] = mapped_column(String(40))
    succeeded_at: Mapped[str | None] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(32))
    failures: Mapped[int] = mapped_column(Integer, default=0)


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

    def list(self, query: str | None = None, offset: int = 0, limit: int = 1000) -> list[Instrument]:
        statement = select(InstrumentRecord)
        if query:
            needle = '%' + query.upper().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
            columns = [InstrumentRecord.symbol, InstrumentRecord.venue, InstrumentRecord.currency]
            columns += [func.json_extract(InstrumentRecord.payload, '$.' + key) for key in ('isin', 'cusip', 'figi', 'country')]
            statement = statement.where(or_(*(func.upper(column).like(needle, escape='\\') for column in columns)))
        rows = self.session.scalars(statement.order_by(InstrumentRecord.symbol, InstrumentRecord.id).offset(offset).limit(limit))
        return [Instrument.model_validate(row.payload) for row in rows]

    def get(self, instrument_id: str) -> Instrument | None:
        row = self.session.get(InstrumentRecord, instrument_id)
        return Instrument.model_validate(row.payload) if row else None

    def add(self, instrument: Instrument) -> None:
        self.session.add(InstrumentRecord(
            id=str(instrument.id), symbol=instrument.symbol, venue=instrument.venue,
            currency=instrument.currency or '', asset_class=instrument.asset_class, payload=instrument.model_dump(mode="json"),
        ))
        self.session.flush()
