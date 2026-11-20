"""Archive the explicitly pinned contract probe; recheck SEC/Alpaca, never merge rows."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from sqlalchemy import event
from sqlalchemy.engine import make_url
from app.config import Settings
from app.database import create_db_engine
from app.instrument_evidence import PILOT, identity_evidence
from app.ibkr_contract_evidence import REVIEW_PATH, MAX_REPORT_BYTES, aware, validate_report, read_report
from app.sec_http import archive_raw
from app.storage_budget import StorageGovernor, MIB


def main():
    parser = argparse.ArgumentParser(description='Archivar revisión IBKR fijada, sin red ni cambios en SQLite.')
    parser.add_argument('--source', required=True, help='Informe privado existente bajo output/.')
    args = parser.parse_args()
    source = Path(args.source).resolve(strict=True)
    if not source.is_relative_to((ROOT/'output').resolve()):
        parser.error('El informe debe estar en output/.')
    with source.open('rb') as stream:
        raw = stream.read(MAX_REPORT_BYTES + 1)
    review = json.loads(REVIEW_PATH.read_text(encoding='utf-8'))
    _, bindings = validate_report(raw, review, PILOT)
    cutoff = datetime.now(timezone.utc)
    if aware(review['reviewed_at']) > cutoff:
        raise ValueError('FUTURE_CONTRACT_REVIEW')
    engine = create_db_engine(Settings().database_url)
    @event.listens_for(engine, 'connect')
    def read_only(connection, _):
        connection.execute('PRAGMA query_only=ON')
    data_root = Path(make_url(str(engine.url)).database).resolve().parent
    try:
        with StorageGovernor(data_root, ROOT/'output').admission(reserve=MIB, destination='data'):
            with engine.connect() as connection:
                connection.exec_driver_sql('BEGIN')
                for spec in PILOT['items']:
                    identity = identity_evidence(connection, data_root/'sec', spec['market_listing_id'], cutoff)
                    if identity['state'] != 'DOCUMENTED' or identity['instrument_id'] != bindings[spec['symbol']][0]['instrument_id']:
                        raise ValueError('SEC_ALPACA_LINK_REQUIRES_REVIEW')
                folder = data_root/'ibkr/contracts/raw'
                digest = archive_raw(folder, raw)
                if read_report(folder, digest) != raw:
                    raise ValueError('ARCHIVE_VERIFICATION_FAILED')
        print(json.dumps(dict(state='REVIEW_ARCHIVED', sha256=digest, contracts=len(bindings),
                              network_requests=0, database_writes=0)))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
