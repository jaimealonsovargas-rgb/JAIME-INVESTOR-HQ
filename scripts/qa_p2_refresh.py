"""Real, bounded P2 recheck using configured DB and quotas. No broker activation."""
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.config import Settings
from app.database import create_db_engine, check_database, DataObservation
from app.data_service import DataService
from app.data_refresh import DataRefresher, BROKER_SOURCES
from app.data_catalog import CATALOG
from app.portfolio_service import PortfolioService


def main():
    destination = ROOT / 'output/p4-data-refresh'
    destination.mkdir(parents=True, exist_ok=True)
    engine = create_db_engine(Settings().database_url)
    check_database(engine)
    data = DataService(engine)
    portfolio = PortfolioService(engine, data)
    before = portfolio.summary()
    rows = []
    report = {'started_at': datetime.now(timezone.utc).isoformat(),
              'method': 'One manual catalog pass, then first scheduler tick and restart check; shared cache/quotas. An eligible uncached failure may receive a second bounded attempt. No brokers or mocks.',
              'results': rows}
    for access, source in CATALOG.items():
        if access in BROKER_SOURCES:
            rows.append({'access_id': access, 'state': 'DISABLED', 'reason': 'No activar brokers en P4.', 'real_connection': False})
        else:
            result = data.query(access)
            row = result.model_dump(mode='json', exclude={'observations'})
            row['observations_count'] = len(result.observations)
            row['payload_hashes'] = sorted({o.payload_hash for o in result.observations})
            row['latest_observed_at'] = max((o.observed_at.isoformat() for o in result.observations), default=None)
            row['fresh_observations'] = sum(not o.stale(data.clock()) for o in result.observations)
            rows.append(row)
        print(access, rows[-1]['state'], flush=True)
        (destination / 'sources-real.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    # Same schedule used in the application's lifespan; cache hits do not create new observations.
    refresh = DataRefresher(data)
    refresh.tick()
    first = refresh.status()
    DataRefresher(data).tick()
    second = DataRefresher(data).status()
    after = portfolio.summary()
    with Session(engine) as session:
        archived = session.scalar(select(func.count()).select_from(DataObservation))
    report.update(finished_at=datetime.now(timezone.utc).isoformat(), quality=data.quality(),
                  archived_observations=archived, refresh=second,
                  restart_preserved_schedule=first == second,
                  master_unchanged=all(before[k] == after[k] for k in ('ledger_hash', 'cash_eur', 'nav_eur', 'positions_count')),
                  ledger_hash=after['ledger_hash'])
    (destination / 'sources-real.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    engine.dispose()
    assert report['restart_preserved_schedule'] and report['master_unchanged']


if __name__ == '__main__':
    main()
