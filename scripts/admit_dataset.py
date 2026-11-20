"""D3 offline admission and immutable manifests; no downloads, mining or orders."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from sqlalchemy import event

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app.config import Settings
from app.database import create_db_engine, check_database
from app.data_service import DataService
from app.market_service import MarketService
from app.admission_fixture import fixture_bundle
from app.admission_history import load_history_candidate, batch_targets, cutoff_text
from app.admission_market import load_market_candidate
from app.dataset_admission import evaluate
from app.dataset_manifests import ManifestStore
from app.storage_budget import StorageGovernor
from app.b32_review import apply_identity_review, PROTOCOL as RETROSPECTIVE
from app.dataset_admission import PROTOCOL as STRICT


def summary(manifest):
    return dict(manifest_id=manifest['manifest_id'], provider=manifest['provider'],
        listing_id=manifest['listing_id'], domain=manifest['domain'], counts=manifest['counts'],
        readiness=manifest['readiness'], engineering_state=manifest['engineering_state'],
        blocked=[dict(code=c['code'], reason=c['detail']) for c in manifest['checks'] if c['state']=='BLOCKED'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['fixture', 'history', 'market', 'show'])
    parser.add_argument('--batch')
    parser.add_argument('--listing')
    parser.add_argument('--as-of', help='Fecha de conocimiento ISO8601 con zona, no futura.')
    parser.add_argument('--manifest')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--protocol', choices=['strict','retrospective'], default='strict')
    args = parser.parse_args()
    if args.protocol=='retrospective' and args.action!='market':
        parser.error('El protocolo retrospectivo requiere el archivo market revisado.')
    if args.action in ('history', 'market') and args.as_of is None:
        parser.error('--as-of es obligatorio para fijar la fecha de conocimiento.')
    if args.action == 'history' and not args.batch:
        parser.error('--batch es obligatorio.')
    if args.action == 'market' and not args.listing:
        parser.error('--listing es obligatorio.')
    if args.action == 'show' and not args.manifest:
        parser.error('--manifest es obligatorio.')
    cutoff = datetime.fromisoformat(args.as_of) if args.as_of else None
    if cutoff is not None:
        cutoff_text(cutoff)
    engine = create_db_engine(Settings().database_url)
    @event.listens_for(engine, 'connect')
    def query_only(connection, _record):
        connection.execute('PRAGMA query_only=ON')
    try:
        check_database(engine)
        store = ManifestStore(StorageGovernor.for_engine(engine))
        if args.action == 'show':
            print(json.dumps(store.read(args.manifest), ensure_ascii=False, indent=2))
            return
        output = []
        next_offset = None
        def freeze(candidate, evidence=None):
            result = evaluate(candidate, evidence, protocol=RETROSPECTIVE if args.protocol=='retrospective' else STRICT)
            store.publish(result)
            output.append(summary(result))
        if args.action == 'fixture':
            freeze(*fixture_bundle())
        elif args.action == 'history':
            if args.listing:
                targets = [args.listing]
            else:
                targets, total = batch_targets(engine, args.batch, offset=args.offset, limit=args.limit)
                if args.offset + len(targets) < total:
                    next_offset = args.offset + len(targets)
            for listing in targets:
                freeze(load_history_candidate(engine, args.batch, listing, cutoff))
        else:
            candidate=load_market_candidate(MarketService(DataService(engine)), args.listing, cutoff)
            freeze(apply_identity_review(candidate) if args.protocol=='retrospective' else candidate)
        print(json.dumps(dict(items=output, next_offset=next_offset,
            network_requests=0, database_writes=0, manifest_directory=str(store.root)), ensure_ascii=False, indent=2))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
