"""Explicit local B3.1 command; no market requests, scheduling or broker writes."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from sqlalchemy.engine import make_url
from app.config import Settings
from app.database import create_db_engine, check_database
from app.quant_fixture import fixture, config
from app.quant_store import TrialRegistry
from app.storage_budget import StorageGovernor, MIB


def main():
    parser = argparse.ArgumentParser(description='B3.1: tres controles sintéticos, sin campañas de mercado.')
    parser.add_argument('--prefix', default='b31-synthetic-v1', help='ID estable para repetir sin duplicar ensayos.')
    args = parser.parse_args()
    engine = create_db_engine(Settings().database_url)
    try:
        check_database(engine)
        registry = TrialRegistry(engine)
        data_root = Path(make_url(str(engine.url)).database).parent
        with StorageGovernor(data_root, ROOT/'output').admission(reserve=8*MIB, destination='data'):
            results = []
            for family in ('SMA_LONG_CASH', 'CASH', 'BUY_HOLD'):
                ident = args.prefix+'-'+family.lower()
                registry.submit(ident, fixture(), config(family))
                row = registry.run(ident)
                results.append(dict(id=ident, state=row['state'], reason=row['reason'],
                                    result_hash=row['result_hash'], result=row['result']))
        print(json.dumps(dict(kind='SYNTHETIC_TEST', execution_ready=False, trials=results), indent=2))
        if any(row['state'] != 'COMPLETED' for row in results):
            raise SystemExit(1)
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
