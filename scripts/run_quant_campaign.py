"""B3.2 fixed ten-trial campaign; private outputs, no downloads or broker orders."""
import argparse
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.database import create_db_engine,check_database
from app.data_service import DataService
from app.market_service import MarketService
from app.admission_market import load_market_candidate
from app.b32_review import reviewed_bundle,apply_identity_review,PROTOCOL,PROTOCOL_SHA256
from app.dataset_admission import evaluate
from app.dataset_manifests import ManifestStore,canonical,publish_no_replace
from app.storage_budget import StorageGovernor
from app.quant_real import planned_configs,admitted_replay
from app.quant_store import TrialRegistry,digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--run-id',default='b32-brkb-20261119-v1')
    args=parser.parse_args()
    import re
    if not re.fullmatch('[A-Za-z0-9_.-]{1,64}',args.run_id): parser.error('run-id no válido')
    engine=create_db_engine(Settings().database_url)
    check_database(engine)
    storage=StorageGovernor.for_engine(engine)
    store=ManifestStore(storage)
    saved=store.read(args.manifest)
    review=reviewed_bundle()
    candidate=apply_identity_review(load_market_candidate(MarketService(DataService(engine)),saved['listing_id'],datetime.fromisoformat(review['as_of'])))
    current=evaluate(candidate,protocol=PROTOCOL)
    if current!=saved or current['readiness']['backtest']!='BACKTEST_READY_EXPLORATORY':
        raise ValueError('CAMPAIGN_REQUIRES_CURRENT_ADMITTED_MANIFEST')
    dataset=dict(kind='MARKET_RETROSPECTIVE',candidate=candidate,manifest_id=args.manifest,protocol_sha256=PROTOCOL_SHA256)
    registry=TrialRegistry(engine)
    configs=planned_configs()
    # Preflight before registration; the registry repeats it on every execution.
    admitted_replay(dataset,configs[0][1],store,registry._now())
    with storage.admission():
        rows=[registry.submit(args.run_id+'.'+name,dataset,cfg) for name,cfg in configs]
        print(json.dumps(dict(registered=len(rows),run_id=args.run_id,calculations_started=False)),flush=True)
        # All ten requests have committed before the first calculation.
        results=[registry.run(row['id']) for row in rows]
        summary=[]
        for (name,_),row in zip(configs,results):
            result=row['result'] or {}
            summary.append(dict(name=name,trial_id=row['id'],state=row['state'],reason=row['reason'],
                result_hash=row['result_hash'],**{k:result.get(k) for k in (
                    'return_fraction','max_drawdown_fraction','commission','slippage_cost','final_cash','final_shares','final_equity')},
                fill_count=len(result.get('fills',[]))))
        by_name={r['name']:r for r in summary}
        support={}
        for variant in ('sma20','sma40','sma60'):
            supported=True
            for cost in ('base','adverse'):
                r,held,cash=(by_name[n+'-'+cost] for n in (variant,'buy_hold','cash'))
                if any(v['state']!='COMPLETED' for v in (r,held,cash)):
                    supported=False;break
                supported &= (Decimal(r['return_fraction'])>max(Decimal(held['return_fraction']),Decimal(cash['return_fraction']))
                    and Decimal(r['max_drawdown_fraction'])<=Decimal(held['max_drawdown_fraction']))
            support[variant]=bool(supported)
        report=dict(version='b32-campaign-v1',run_id=args.run_id,manifest_id=args.manifest,protocol_sha256=PROTOCOL_SHA256,
            state='COMPLETED' if all(r['state']=='COMPLETED' for r in results) else 'INCOMPLETE',
            planned=10,completed=sum(r['state']=='COMPLETED' for r in results),trials=summary,
            exploratory_support=support,statistically_accepted_candidates=0,execution_ready=False,
            point_in_time_claim=False,oos_reserved=False,unit='USD',initial_cash='10000.00',
            warmup_sessions=60,evaluation_sessions=192,accounting_scope='EXPERIMENT_ONLY_NOT_MASTER')
    raw=canonical(report)
    with storage.admission(reserve=2*1024*1024,destination='output'):
        folder=Path(storage.output_root)/'quant-campaigns'/args.run_id
        if folder.resolve()!=folder.absolute(): raise ValueError('OUTPUT_PATH_REDIRECTED')
        folder.mkdir(parents=True,exist_ok=True)
        path=folder/(digest(report)+'.json')
        if not path.exists():
            from uuid import uuid4
            tmp=folder/('.'+uuid4().hex+'.tmp')
            try:
                tmp.write_bytes(raw)
                try: publish_no_replace(tmp,path)
                except FileExistsError: pass
            finally: tmp.unlink(missing_ok=True)
        if path.read_bytes()!=raw: raise ValueError('CAMPAIGN_REPORT_CONFLICT')
    # Only aggregate results, never bars/fill prices/account secrets, leave this CLI.
    print(json.dumps(dict(report=report,path=str(path)),ensure_ascii=False,indent=2))
    engine.dispose()


if __name__=='__main__': main()
