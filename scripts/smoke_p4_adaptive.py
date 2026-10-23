"""Local P4 smoke: genuine HTTP research run; stores private financial payloads in output/."""
import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instrument-id', required=True)
    parser.add_argument('--depth', choices=('ordinary', 'deep'), default='ordinary')
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--refresh-public', action='store_true')
    parser.add_argument('--question', default='Describir la evidencia disponible y sus límites sin pronosticar.')
    parser.add_argument('--wait-seconds', type=int, default=45)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.summary and args.depth != 'ordinary':
        parser.error('La síntesis compacta solo pertenece al modo ordinario.')
    root = 'http://127.0.0.1:8000'
    headers = {'X-HQ-Research': '1', 'Idempotency-Key': 'case-' + uuid.uuid4().hex}
    start = time.perf_counter()
    with httpx.Client(trust_env=False, follow_redirects=False, timeout=12) as client:
        case = client.post(root + '/api/research/cases', headers=headers, json={
            'instrument_id': args.instrument_id, 'question': args.question,
            'research_goal': 'descriptive_research'}).raise_for_status().json()
        run_key = 'run-' + uuid.uuid4().hex
        headers['Idempotency-Key'] = run_key
        jobs = client.post(root + f"/api/research/cases/{case['id']}/run", headers=headers, json={
            'priority': 10, 'refresh_public': args.refresh_public, 'analysis_depth': args.depth,
            'include_local_summary': args.summary}).raise_for_status().json()
        dossier = {}
        while time.perf_counter() - start < args.wait_seconds:
            dossier = client.get(root + f"/api/research/cases/{case['id']}", params={'run_key': run_key}).raise_for_status().json()
            if dossier['status'] not in ('RUNNING', 'IDLE'):
                break
            time.sleep(.5)
        elapsed = round(time.perf_counter() - start, 3)
    report = {'at': datetime.now(timezone.utc).isoformat(), 'case': case, 'run_key': run_key,
              'jobs_queued': jobs, 'elapsed_seconds': elapsed, 'dossier': dossier}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case_id': case['id'], 'run_key': run_key, 'depth': args.depth,
                      'elapsed_seconds': elapsed, 'status': dossier.get('status'),
                      'quality': dossier.get('quality', {}).get('state'),
                      'job_states': [(job['role_id'], job['state'], job.get('error')) for job in dossier.get('jobs', [])],
                      'evidence_count': len(dossier.get('evidence', [])),
                      'results_count': len(dossier.get('results', []))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
