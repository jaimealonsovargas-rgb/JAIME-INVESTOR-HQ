"""One real debate with OS telemetry and financial-invariant checks, no retries."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import httpx
from diagnose_p4_runtime import Monitor


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--name',default='qwen25-wire-v1')
    args=parser.parse_args()
    if not args.name.replace('-','').isalnum(): raise SystemExit('INVALID_REPORT_NAME')
    folder=Path('output/p4-debate-repair'); folder.mkdir(parents=True,exist_ok=True)
    with httpx.Client(trust_env=False,follow_redirects=False,timeout=10) as client:
        before=client.get('http://127.0.0.1:8000/api/portfolio/master/summary').raise_for_status().json()
        status=client.get('http://127.0.0.1:8000/api/agents/status').raise_for_status().json()
        if status['active_jobs'] or status['queue']: raise SystemExit('ACTIVE_JOBS')
        monitor=Monitor(args.pid); monitor.thread.start(); start=time.perf_counter()
        try:
            result=subprocess.run([sys.executable,'scripts/smoke_p4_adaptive.py',
                '--instrument-id','d4e13ead-f622-515e-8bc6-c8fbcaa91130','--depth','deep',
                '--refresh-public','--wait-seconds','270','--output',str(folder/(args.name+'.json')),
                '--question','¿Puede sostenerse una tesis favorable a partir de la trayectoria observada? Contrástala con el riesgo de reversión y las limitaciones de los datos.'],
                timeout=280,check=False)
        finally:
            monitor.close()
            after=client.get('http://127.0.0.1:8000/api/portfolio/master/summary').raise_for_status().json()
            orders=client.post('http://127.0.0.1:8000/api/orders',json={}).status_code
            report={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                    'wall_seconds':time.perf_counter()-start,'samples':monitor.rows,
                    'ledger_before':before['ledger_hash'],'ledger_after':after['ledger_hash'],
                    'cash_eur':after['cash_eur'],'nav_eur':after['nav_eur'],
                    'positions_count':after['positions_count'],'orders_http':orders}
            (folder/(args.name+'-telemetry.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
        assert before['ledger_hash']==after['ledger_hash'] and orders==403
        assert after['cash_eur']==after['nav_eur']=='10000.00' and after['positions_count']==0
        dossier=json.loads((folder/(args.name+'.json')).read_text(encoding='utf-8'))['dossier']
        # COMPLETE is only a technical gate; semantic review is still separate.
        raise SystemExit(result.returncode or (0 if dossier['status']=='COMPLETE' and dossier['quality']['state']!='REJECTED' else 2))


if __name__=='__main__':main()
