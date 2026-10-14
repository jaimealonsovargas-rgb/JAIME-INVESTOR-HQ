"""Smoke real y limitado. Sin órdenes; claves y cuerpos privados no salen del proceso."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.database import create_db_engine,check_database
from app.data_service import DataService
from app.data_catalog import CATALOG

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sources',default=','.join(CATALOG))
    parser.add_argument('--output',default='docs/evidencias/P2/smoke-real.json')
    parser.add_argument('--database',default='output/p2-smoke.db')
    args=parser.parse_args()
    ids=args.sources.split(',')
    if any(id not in CATALOG for id in ids):raise SystemExit('ID de fuente no permitido.')
    path=(ROOT/args.database).resolve()
    if not path.is_relative_to(ROOT):raise SystemExit('DB debe quedar dentro del repositorio.')
    os.environ['DATABASE_URL']='sqlite:///'+path.as_posix()
    from alembic import command
    from alembic.config import Config
    command.upgrade(Config(str(ROOT/'alembic.ini')),'head')
    engine=create_db_engine(Settings().database_url);check_database(engine)
    data=DataService(engine);results=[]
    for id in ids:
        result=data.query(id)
        public=result.model_dump(mode='json',exclude={'observations'})
        public['observations_count']=len(result.observations)
        public['payload_hashes']=sorted({o.payload_hash for o in result.observations})
        results.append(public)
        print(id,result.state,result.http_status,'HTTP verificado:',result.real_connection,flush=True)
        destination=ROOT/args.output;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps({'performed_at':datetime.now(timezone.utc).isoformat(),'method':'SafeDataHttp real; sin mocks; una consulta acotada por modalidad, cache/cuota compartida','results':results,'quality':data.quality()},ensure_ascii=False,indent=2),encoding='utf-8')
    engine.dispose()

if __name__=='__main__':main()
