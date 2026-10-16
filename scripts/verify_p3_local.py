"""Read-only HTTP acceptance and consistent SQLite backup/restore verification.

The sole POST is the mandatory negative test against the local blocked orders API.
Restoration occurs in a separate output DB, never over the user's database.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from app.config import Settings
from app.main import create_app

folder = Path('output/p3-preflight')
folder.mkdir(parents=True, exist_ok=True)
result = {'at': datetime.now(timezone.utc).isoformat(), 'environment': 'Windows local', 'http': {}}
for path in ('/health', '/api/portfolio/master/summary', '/api/portfolio/master/positions', '/api/portfolio/master/ledger',
             '/api/portfolio/master/nav/history', '/api/portfolio/master/performance', '/api/data/quality'):
    with urllib.request.urlopen('http://127.0.0.1:8000'+path, timeout=10) as response:
        body = json.load(response)
        result['http'][path] = {'status': response.status, 'body': body['counts'] if path.endswith('/quality') else body}
try:
    urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/api/orders', data=b'{"mode":"LIVE"}', headers={'Content-Type':'application/json'}), timeout=5)
    raise AssertionError('Orders must be blocked')
except urllib.error.HTTPError as error:
    assert error.code == 403
    result['orders'] = {'status':error.code, 'body':json.loads(error.read())}
source = Path(make_url(Settings().database_url).database)
restore = folder / ('restore-verification-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.db')
with sqlite3.connect(source) as src, sqlite3.connect(restore) as dst:
    src.backup(dst)
    result['restore'] = {'integrity':dst.execute('PRAGMA integrity_check').fetchone()[0],
        'foreign_keys':dst.execute('PRAGMA foreign_key_check').fetchall(),
        'schema':dst.execute('SELECT version_num FROM alembic_version').fetchone()[0],
        'instruments':dst.execute('SELECT count(*) FROM instruments').fetchone()[0],
        'events':dst.execute("SELECT count(*) FROM ledger_events WHERE portfolio_id='MASTER'").fetchone()[0]}
result['restore']['backup_sha256'] = hashlib.sha256(restore.read_bytes()).hexdigest()
before = result['http']['/api/portfolio/master/summary']['body']
result['restarts_restored_db'] = []
for _ in range(2):
    with TestClient(create_app(Settings(database_url='sqlite:///'+restore.resolve().as_posix())), base_url='http://127.0.0.1') as client:
        summary = client.get('/api/portfolio/master/summary').json()
        evidence = {key:summary[key] for key in ('nav_eur','cash_eur','positions_count','events_count','ledger_hash')}
        assert evidence == {key:before[key] for key in evidence}
        assert evidence['nav_eur']=='10000.00' and evidence['positions_count']==0 and evidence['events_count']==1
        assert client.post('/api/orders', json={'mode':'LIVE'}).status_code==403
        result['restarts_restored_db'].append(evidence)
assert result['restore']['integrity']=='ok' and not result['restore']['foreign_keys']
(folder/'acceptance.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'NAV':before['nav_eur'], 'positions':before['positions_count'], 'events':before['events_count'], 'restore':result['restore'], 'restarts':2, 'orders':403}, indent=2))
