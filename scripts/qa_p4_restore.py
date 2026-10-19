"""Real SQLite backup/reopen regression, local only; no queued job execution."""
import json
import sqlite3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import Settings
from app.database import create_db_engine
from app.data_service import DataService
from app.portfolio_service import PortfolioService
from app.research_store import ResearchStore
from app.research_service import ResearchService
from app.research_contracts import digest,utc

source=ROOT/'data/jaime_hq.db'
target=ROOT/'output/p4-preflight/restore-p4.db'
with sqlite3.connect(source) as live:
    if live.execute("SELECT COUNT(*) FROM agent_jobs WHERE state IN ('RUNNING','QUEUED')").fetchone()[0]:
        raise SystemExit('WAIT_FOR_TERMINAL_JOBS')
    with sqlite3.connect(target) as backup: live.backup(backup)
checks=[]
for iteration in range(2):
    settings=Settings(_env_file=None,database_url='sqlite:///'+target.as_posix())
    engine=create_db_engine(settings.database_url)
    data=DataService(engine);portfolio=PortfolioService(engine,data);store=ResearchStore(engine)
    before=portfolio.summary();store.initialize();store.recover()
    dossier=ResearchService(engine,data,portfolio).dossier('ccadc542-5ddf-415f-8692-676415729886')
    with engine.connect() as conn:
        integrity=conn.exec_driver_sql('PRAGMA integrity_check').scalar()
        version=conn.exec_driver_sql('SELECT version_num FROM alembic_version').scalar()
        counts={t:conn.exec_driver_sql('SELECT COUNT(*) FROM '+t).scalar() for t in ('agents','agent_jobs','research_cases','evidence','agent_results','research_claims','ledger_events','instruments')}
    after=portfolio.summary()
    assert before['ledger_hash']==after['ledger_hash']=='fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836'
    assert after['cash_eur']==after['nav_eur']=='10000.00' and after['positions_count']==0
    assert integrity=='ok' and version=='0004_research' and counts['agents']==30
    checks.append({'iteration':iteration+1,'integrity':integrity,'schema':version,'counts':counts,'ledger_hash':after['ledger_hash'],'dossier_status':dossier['status'],'jobs_hash':digest(dossier['jobs']),'result_hashes':{r['job_id']:r['input_hash'] for r in dossier['results']}})
    engine.dispose()
assert checks[0]['counts']==checks[1]['counts'] and checks[0]['jobs_hash']==checks[1]['jobs_hash']
(ROOT/'output/p4-preflight/restore-result.json').write_text(json.dumps({'at':utc(),'method':'SQLite online backup then two isolated engine reopen/recovery cycles; no HTTP, no new jobs','checks':checks},indent=2),encoding='utf-8')
print('RESTORE_PASS: two reopen/recovery cycles, research and MASTER preserved')
