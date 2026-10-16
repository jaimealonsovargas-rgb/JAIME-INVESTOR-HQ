"""Local idempotent initialization/snapshot; never takes financial values as input."""
from app.config import Settings
from app.database import create_db_engine, check_database
from app.data_service import DataService
from app.portfolio_store import initialize_master
from app.portfolio_service import PortfolioService

engine = create_db_engine(Settings().database_url)
try:
    check_database(engine)
    initialize_master(engine)
    snapshot = PortfolioService(engine, DataService(engine)).snapshot()
    print('MASTER', snapshot['nav_eur'], snapshot['valuation_status'], snapshot['ledger_hash'])
finally:
    engine.dispose()
