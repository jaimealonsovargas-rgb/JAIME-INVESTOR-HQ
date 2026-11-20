"""Durable, bounded B3.1 trials. Register and commit before validating or running.

CAS leases fence concurrent/stale workers. A crashed attempt stays visible; an
expired lease can be resumed with the same inputs/code, at most three attempts.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert

from app.database import Base
from app.quant_contracts import ExperimentConfig, SyntheticDataset
from app.quant_engine import ENGINE_VERSION, ExperimentRejected, run_reference

DATASETS = Base.metadata.tables['quant_datasets']
TRIALS = Base.metadata.tables['quant_trials']
EVENTS = Base.metadata.tables['quant_trial_events']
TERMINAL = {'COMPLETED', 'REJECTED', 'FAILED'}
MAX_REQUEST_BYTES = 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def code_hash():
    folder = Path(__file__).parent
    return digest({name: hashlib.sha256((folder/name).read_bytes()).hexdigest()
                   for name in ('quant_contracts.py', 'quant_engine.py', 'quant_store.py', 'quant_schema.py',
                       'quant_real.py','b32_review.py','dataset_admission.py','dataset_evidence.py',
                       'admission_contracts.py','dataset_manifests.py','history_rights.py')})


class TrialRegistry:
    def __init__(self, engine, *, clock=None):
        self.engine = engine
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _now(self):
        now = self.clock()
        if now.utcoffset() is None:
            raise ValueError('AWARE_CLOCK_REQUIRED')
        return now.astimezone(timezone.utc)

    @staticmethod
    def _event(connection, row, state, reason, now, attempt=None):
        connection.execute(EVENTS.insert().values(trial_id=row['id'], at=now, state=state,
                           reason=reason, attempt=row['attempt'] if attempt is None else attempt))

    def submit(self, trial_id, dataset, config):
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', trial_id):
            raise ValueError('INVALID_TRIAL_ID')
        # Transport admission only. Every bounded JSON request is persisted,
        # including invalid financial contracts; non-JSON/oversize are not trials.
        encoded = canonical(dict(dataset=dataset, config=config))
        if len(encoded.encode()) > MAX_REQUEST_BYTES:
            raise ValueError('REQUEST_TOO_LARGE')
        request = json.loads(encoded)  # detach mutable caller inputs
        dataset, config = request['dataset'], request['config']
        request_hash = digest(request)
        now = self._now().isoformat()
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            existing = c.execute(select(TRIALS).where(TRIALS.c.id == trial_id)).mappings().first()
            if existing:
                if existing['request_hash'] != request_hash:
                    raise ValueError('IDEMPOTENCY_CONFLICT')
                return dict(existing)
            dataset_hash = digest(dataset)
            c.execute(insert(DATASETS).values(hash=dataset_hash, payload=dataset).on_conflict_do_nothing())
            row = dict(id=trial_id, request_hash=request_hash, dataset_hash=dataset_hash,
                       config_hash=digest(config), code_hash=code_hash(), config=config,
                       runtime=dict(python=platform.python_version(), engine=ENGINE_VERSION, seed=0),
                       state='QUEUED', reason='REGISTERED_BEFORE_VALIDATION', created_at=now,
                       updated_at=now, attempt=0, lease_token=None, lease_until=None, result=None, result_hash=None)
            c.execute(TRIALS.insert().values(**row))
            self._event(c, row, row['state'], row['reason'], now)
        return row

    def get(self, trial_id):
        with self.engine.connect() as c:
            row = c.execute(select(TRIALS).where(TRIALS.c.id == trial_id)).mappings().one()
            return dict(row)

    def events(self, trial_id):
        with self.engine.connect() as c:
            return [dict(r) for r in c.execute(select(EVENTS).where(EVENTS.c.trial_id == trial_id)
                                              .order_by(EVENTS.c.sequence)).mappings()]

    def run(self, trial_id):
        now = self._now()
        with self.engine.begin() as c:
            c.exec_driver_sql('BEGIN IMMEDIATE')
            row = dict(c.execute(select(TRIALS).where(TRIALS.c.id == trial_id)).mappings().one())
            if row['state'] in TERMINAL:
                return row
            if row['state'] == 'RUNNING' and row['lease_until'] > now.isoformat():
                return row
            if row['state'] == 'RUNNING':
                self._event(c, row, 'INTERRUPTED', 'LEASE_EXPIRED', now.isoformat())
            if row['attempt'] >= 3:
                c.execute(update(TRIALS).where(TRIALS.c.id == trial_id).values(
                    state='FAILED', reason='RECOVERY_LIMIT', updated_at=now.isoformat(), lease_token=None, lease_until=None))
                self._event(c, row, 'FAILED', 'RECOVERY_LIMIT', now.isoformat())
                row.update(state='FAILED', reason='RECOVERY_LIMIT', lease_token=None, lease_until=None, updated_at=now.isoformat())
                return row
            token = str(uuid4())
            attempt = row['attempt'] + 1
            c.execute(update(TRIALS).where(TRIALS.c.id == trial_id).values(state='RUNNING', reason='REFERENCE_RUNNING',
                      attempt=attempt, lease_token=token, lease_until=(now+timedelta(seconds=60)).isoformat(), updated_at=now.isoformat()))
            self._event(c, row, 'RUNNING', 'REFERENCE_RUNNING', now.isoformat(), attempt)
            dataset = c.execute(select(DATASETS.c.payload).where(DATASETS.c.hash == row['dataset_hash'])).scalar_one()
        # Commit registration/claim before any engine work. No transaction held during calculation.
        result = None
        try:
            if digest(dataset) != row['dataset_hash'] or digest(row['config']) != row['config_hash']:
                raise ExperimentRejected('INPUT_HASH_MISMATCH')
            if digest(dict(dataset=dataset, config=row['config'])) != row['request_hash']:
                raise ExperimentRejected('INPUT_HASH_MISMATCH')
            if row['code_hash'] != code_hash() or row['runtime']['python'] != platform.python_version():
                raise ExperimentRejected('ENGINE_VERSION_CHANGED')
            if isinstance(dataset,dict) and dataset.get('kind')=='MARKET_RETROSPECTIVE':
                from app.quant_real import run_retrospective
                from app.dataset_manifests import ManifestStore
                from app.storage_budget import StorageGovernor
                result=run_retrospective(dataset,row['config'],ManifestStore(StorageGovernor.for_engine(self.engine)),self._now())
                state,reason='COMPLETED','RETROSPECTIVE_EXPLORATORY_ONLY'
            elif not isinstance(dataset, dict) or dataset.get('kind') != 'SYNTHETIC_TEST':
                raise ExperimentRejected('REAL_DATA_NOT_ENABLED_B3_1')
            else:
                validated_data = SyntheticDataset.model_validate(dataset)
                validated_config = ExperimentConfig.model_validate(row['config'])
                result = run_reference(validated_data, validated_config)
                state, reason = 'COMPLETED', 'SYNTHETIC_ENGINE_CHECK_ONLY'
        except ValidationError:
            state, reason = 'REJECTED', 'INVALID_EXPERIMENT_CONTRACT'
        except ExperimentRejected as error:
            state, reason = 'REJECTED', str(error)
        except TimeoutError:
            state, reason = 'FAILED', 'REFERENCE_DEADLINE'
        except Exception:
            # No exception text or provider/secret content is persisted.
            state, reason = 'FAILED', 'REFERENCE_ENGINE_ERROR'
        finished = self._now().isoformat()
        with self.engine.begin() as c:
            changed = c.execute(update(TRIALS).where(TRIALS.c.id == trial_id, TRIALS.c.state == 'RUNNING',
                                TRIALS.c.lease_token == token, TRIALS.c.lease_until > finished).values(
                state=state, reason=reason, result=result, result_hash=digest(result) if result is not None else None,
                updated_at=finished, lease_token=None, lease_until=None))
            if changed.rowcount:
                self._event(c, row, state, reason, finished, attempt)
        return self.get(trial_id)
