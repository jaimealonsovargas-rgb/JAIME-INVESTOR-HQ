"""D2 manual coordinator. No automatic schedule, subscription or broker order."""
import argparse,json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.database import create_db_engine,check_database
from app.history_service import HistoryService,fixture_request


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['submit','fixture','step','status','pause','resume','cancel'])
    parser.add_argument('id');parser.add_argument('--request',type=Path)
    parser.add_argument('--targets',type=int,default=10)
    parser.add_argument('--max-units',type=int,default=10)
    parser.add_argument('--offset',type=int,default=0)
    args=parser.parse_args()
    if not 1<=args.max_units<=100 or not 1<=args.targets<=5000:parser.error('Límites: 1–100 unidades por ejecución, 1–5.000 objetivos por lote.')
    engine=create_db_engine(Settings().database_url)
    try:
        check_database(engine);service=HistoryService(engine)
        if args.action=='submit':
            if args.request is None:parser.error('--request es obligatorio.')
            with args.request.open('rb') as f:raw=f.read(4*1024*1024+1)
            if len(raw)>4*1024*1024:parser.error('Petición mayor de 4 MiB.')
            service.enqueue(args.id,json.loads(raw))
        elif args.action=='fixture':service.enqueue(args.id,fixture_request(args.targets))
        elif args.action=='step':
            for _ in range(args.max_units):
                if not service.step(args.id)['worked']:break
        elif args.action in ('pause','resume','cancel'):service.control(args.id,args.action)
        print(json.dumps(service.store.status(args.id,offset=args.offset),ensure_ascii=False,indent=2))
    finally:engine.dispose()


if __name__=='__main__':main()
