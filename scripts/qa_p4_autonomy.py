"""Real unattended local acceptance. Starts its own backend; never creates a case/run.

Private evidence stays in output/. Stop existing backend first. The only writes
through HTTP are pause/resume controls and the required rejected order probe.
No model is started. Uses existing real P2 transport, not fixture responses.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

import httpx
from diagnose_p4_runtime import Monitor

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'output/p4-autonomy')
    parser.add_argument('--database-url')
    parser.add_argument('--source-disabled', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'at_utc': datetime.now(timezone.utc).isoformat(), 'classification': 'REAL_UNATTENDED_BACKEND',
              'writes': [], 'reads': [], 'source_disabled': args.source_disabled}
    client = httpx.Client(base_url='http://127.0.0.1:8000', timeout=5, trust_env=False)
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'backend'), 'AUTONOMY_ENABLED': 'true',
           'AUTONOMY_STARTUP_DELAY_SECONDS': '12', 'DATA_AUTO_REFRESH_ENABLED': 'false'}
    if args.database_url:
        env['DATABASE_URL'] = args.database_url
    if args.source_disabled:
        env['DATA_DISABLED_SOURCES'] = 'A21'
    process = None
    server_pid = None
    files = []
    monitor = None

    def get(path):
        response = client.get(path)
        response.raise_for_status()
        report['reads'].append(path)
        return response.json()

    def control(action, key):
        report['writes'].append({'path': '/api/research/autonomy/control', 'action': action})
        response = client.post('/api/research/autonomy/control', json={'action': action},
            headers={'X-HQ-Research': '1', 'Idempotency-Key': key})
        response.raise_for_status()
        return response.json()

    def start(label):
        nonlocal process, server_pid
        files.extend([(args.output / (label + '.stdout.log')).open('w'), (args.output / (label + '.stderr.log')).open('w')])
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:create_app', '--factory',
            '--host', '127.0.0.1', '--port', '8000', '--no-access-log'], cwd=ROOT, env=env,
            stdout=files[-2], stderr=files[-1], creationflags=subprocess.CREATE_NO_WINDOW)
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('Backend exited; inspect local stderr')
            try:
                if client.get('/health').status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
        else:
            raise TimeoutError('Backend startup')
        # Windows venv launcher may have a child; measure the actual server process.
        raw = subprocess.check_output(['powershell', '-NoProfile', '-Command',
            '(Get-NetTCPConnection -State Listen -LocalPort 8000).OwningProcess'], text=True)
        server_pid = int(raw.strip())
        return server_pid

    def stop():
        nonlocal process, server_pid
        if server_pid:
            subprocess.run(['powershell', '-NoProfile', '-Command', f'Stop-Process -Id {server_pid} -ErrorAction SilentlyContinue'], check=True)
        if process:
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
        process, server_pid = None, None

    try:
        start('first-start')
        monitor = Monitor(server_pid)
        monitor.thread.start()
        report['master_before'] = get('/api/portfolio/master/summary')
        report['runtime_before'] = get('/api/agents/status')
        assert report['runtime_before']['runtime']['state'] == 'NO_LOCAL_MODEL'
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            status = get('/api/research/autonomy')
            if status['tasks'] and status['tasks'][0]['state'] not in ('QUEUED', 'RUNNING'):
                break
            time.sleep(1)
        else:
            raise TimeoutError('No autonomous terminal task')
        task = status['tasks'][0]
        report['task'] = task
        report['status_completed'] = status
        if task['case_id']:
            dossier = get('/api/research/cases/' + task['case_id'])
            (args.output / 'dossier-private.json').write_text(json.dumps(dossier, indent=2, ensure_ascii=False), encoding='utf-8')
            report['jobs'] = dossier['jobs']
            assert {j['role_id'] for j in dossier['jobs']} == {'data_quality', 'momentum_trend', 'volatility_regime'}
            assert all(j['kind'] != 'llm' for j in dossier['jobs'])
            assert dossier['quality']['state'] == 'VERIFIED_DATA'
        assert task['state'] == ('ABSTAINED' if args.source_disabled else 'SUCCEEDED')
        report['idle_started_at'] = time.monotonic()
        time.sleep(12)
        monitor.close()
        report['resource_samples'] = monitor.rows
        monitor = None
        report['master_after'] = get('/api/portfolio/master/summary')
        for key in ('ledger_hash', 'cash_eur', 'nav_eur', 'positions_count'):
            assert report['master_before'][key] == report['master_after'][key]
        report['orders_status'] = client.post('/api/orders', json={}).status_code
        report['writes'].append({'path': '/api/orders', 'expected_rejection': True})
        assert report['orders_status'] == 403
        first_ids = [t['id'] for t in status['tasks']]
        stop()
        start('restart')
        report['after_restart'] = get('/api/research/autonomy')
        assert [t['id'] for t in report['after_restart']['tasks']] == first_ids
        if task['case_id']:
            assert get('/api/research/cases/' + task['case_id'])['jobs'] == report['jobs']
        report['paused'] = control('pause', 'autonomy-qa-pause-' + task['id'])
        assert report['paused']['paused']
        stop()
        start('paused-restart')
        report['paused_restart'] = get('/api/research/autonomy')
        assert report['paused_restart']['paused']
        assert [t['id'] for t in report['paused_restart']['tasks']] == first_ids
        report['resumed'] = control('resume', 'autonomy-qa-resume-' + task['id'])
        report['agents_after'] = get('/api/agents/status')
        assert report['agents_after']['roles'] == 30
        assert report['agents_after']['active_jobs'] == report['agents_after']['queue'] == 0
        report['acceptance'] = 'PASS'
    except BaseException as error:
        report['acceptance'] = 'FAILED'
        report['error_type'] = type(error).__name__
        raise
    finally:
        if monitor:
            monitor.close()
            report['resource_samples'] = monitor.rows
        stop()
        for file in files:
            file.close()
        (args.output / 'acceptance-private.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps({'acceptance': report.get('acceptance'), 'task_id': report.get('task', {}).get('id'),
                          'task_state': report.get('task', {}).get('state'), 'orders': report.get('orders_status')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
