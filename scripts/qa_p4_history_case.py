"""Real local research using authorized P2 history; private output, no orders."""
import json
import time
import argparse
from pathlib import Path
import httpx

parser = argparse.ArgumentParser()
parser.add_argument('--run-key', default='history-compact-p48-run')
parser.add_argument('--output', type=Path, default=Path('output/p4-data-refresh/research-history-real.json'))
args = parser.parse_args()
out = args.output
with httpx.Client(base_url='http://127.0.0.1:8000', trust_env=False, timeout=30) as client:
    before = client.get('/api/portfolio/master/summary').json()
    instruments = client.get('/api/instruments').json()
    instrument = next(i for i in instruments if i['symbol'] == 'btc-bitcoin' and i['venue'] == 'AGGREGATED')
    headers = {'X-HQ-Research': '1', 'Idempotency-Key': 'history-compact-p48-case'}
    response = client.post('/api/research/cases', headers=headers, json={
        'instrument_id': instrument['id'], 'research_goal': 'investable_thesis',
        'question': '¿Qué hipótesis condicional y objeción permite la tendencia del histórico diario agregado de Bitcoin? Limitarse a precios observados y features descriptivas; no inferir valor intrínseco, libro de órdenes, liquidez ejecutable ni rentabilidad futura. Abstenerse donde falte evidencia.'})
    response.raise_for_status()
    case_id = response.json()['id']
    headers['Idempotency-Key'] = args.run_key
    response = client.post(f'/api/research/cases/{case_id}/run', headers=headers,
                           json={'priority': 10, 'refresh_public': False})
    response.raise_for_status()
    previous = None
    for _ in range(160):
        dossier = client.get(f'/api/research/cases/{case_id}').json()
        state = [(j['role_id'], j['state'], j.get('error')) for j in dossier['jobs']]
        if state != previous:
            print(json.dumps({'case_id': case_id, 'jobs': state}, ensure_ascii=True), flush=True)
            previous = state
        after = client.get('/api/portfolio/master/summary').json()
        result = {'classification': 'REAL_LOCAL_PERSONAL_USE_DO_NOT_PUBLISH_RAW_DATA',
                  'before_hash': before['ledger_hash'], 'after_hash': after['ledger_hash'],
                  'dossier': dossier, 'semantic_acceptance': 'PENDING_REVIEW'}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        assert before['ledger_hash'] == after['ledger_hash']
        if dossier['status'] not in ('IDLE', 'RUNNING'):
            break
        time.sleep(10)
    print(json.dumps({'status': dossier['status'], 'quality': dossier['quality']}, ensure_ascii=True))
