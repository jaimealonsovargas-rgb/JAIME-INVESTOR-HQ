"""Reproduce the pilot identity/history diagnosis using only saved evidence. No HTTP."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
from sqlalchemy import event

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.database import create_db_engine
from app.data_service import DataService
from app.market_service import MarketService
from app.dataset_assessment import assess_market,POLICY
from app.instrument_evidence import PILOT


def main():
    parser=argparse.ArgumentParser(description='Diagnóstico local de identidad y admisibilidad del piloto B2.3.')
    parser.add_argument('--as-of',required=True,help='Fecha de conocimiento ISO 8601 con zona horaria.')
    parser.add_argument('--output',required=True,help='Archivo JSON nuevo de evidencia privada.')
    args=parser.parse_args()
    cutoff=datetime.fromisoformat(args.as_of)
    if cutoff.utcoffset() is None or cutoff>datetime.now(timezone.utc):
        parser.error('La fecha debe tener zona horaria y no estar en el futuro.')
    engine=create_db_engine(Settings().database_url)
    @event.listens_for(engine,'connect')
    def read_only(connection,_record):
        connection.execute('PRAGMA query_only=ON')
    try:
        service=MarketService(DataService(engine))
        rows=[assess_market(service,s['market_listing_id'],'raw',cutoff) for s in PILOT['items']]
        result=dict(policy=POLICY,as_of=cutoff.isoformat(),network_requests=0,database_writes=0,items=rows)
        output=Path(args.output)
        output.parent.mkdir(parents=True,exist_ok=True)
        encoded=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
        if output.exists():
            if output.read_text(encoding='utf-8')!=encoded:raise SystemExit('La evidencia existente difiere: utiliza otro archivo de salida.')
        else:
            with output.open('x',encoding='utf-8') as stream:stream.write(encoded)
        print(json.dumps([dict(symbol=s['symbol'],identity=r['identity']['state'],research=r['research_state'],
            backtest=r['backtest_state'],bars=r['dataset']['bars'] if r['dataset'] else 0,manifest=r['manifest_id']) for s,r in zip(PILOT['items'],rows)],indent=2))
    finally:engine.dispose()


if __name__=='__main__':main()
