"""Immutable private B4 dossiers. Consumers pin the ID of a verified delivery."""
import json
import os
from pathlib import Path
import re
from uuid import uuid4
from app.dataset_manifests import canonical, publish_no_replace
from app.quant_store import digest
from app.storage_budget import MIB


class ValidationStore:
    limit = 32 * MIB

    def __init__(self, storage):
        self.storage = storage
        self.root = Path(storage.output_root).absolute() / 'strategy-validation'

    def path(self, dossier_id):
        if not isinstance(dossier_id, str) or not re.fullmatch('[a-f0-9]{64}', dossier_id):
            raise ValueError('INVALID_DOSSIER_ID')
        path = self.root / (dossier_id + '.json')
        if path.resolve() != path.absolute() or path.is_symlink():
            raise ValueError('VALIDATION_PATH_REDIRECTED')
        return path

    @staticmethod
    def verify(body):
        decision = body['decision']
        hypotheses = body['hypotheses']
        search = body['search']
        selected = [h['id'] for h in hypotheses if h['selected']]
        comparable = any(len(h['comparisons']) == len(search['scenarios']) for h in hypotheses)
        empty_status = 'NO_CANDIDATES' if comparable else 'EVIDENCE_INCOMPLETE'
        if (body['version'] != 'b4-validation-dossier-v1' or digest(body['policy']) != body['policy_hash']
                or search['planned_trials'] != search['recorded_trials'] or len(body['trials']) != search['planned_trials']
                or len(hypotheses) != search['hypotheses'] or selected != decision['candidate_ids']
                or decision['orders_enabled'] is not False or decision['execution_ready'] is not False
                or (decision['status'], decision['next_action']) != (
                    ('CANDIDATES_FOR_REVIEW', 'REVIEW') if selected else (empty_status, 'OBSERVE'))):
            raise ValueError('INVALID_VALIDATION_HANDOFF')
        return digest(body)

    def read(self, dossier_id):
        with self.path(dossier_id).open('rb') as stream:
            raw = stream.read(self.limit + 1)
        if len(raw) > self.limit:
            raise ValueError('DOSSIER_TOO_LARGE')
        body = json.loads(raw)
        if self.verify(body) != dossier_id or raw != canonical(body):
            raise ValueError('DOSSIER_INTEGRITY')
        return body

    def publish(self, body):
        dossier_id = self.verify(body)
        target = self.path(dossier_id)
        raw = canonical(body)
        if len(raw) > self.limit:
            raise ValueError('DOSSIER_TOO_LARGE')
        with self.storage.admission(reserve=max(MIB, 2 * len(raw)), destination='output'):
            self.root.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                temp = self.root / ('.' + uuid4().hex + '.tmp')
                try:
                    with temp.open('xb') as stream:
                        stream.write(raw)
                        stream.flush()
                        os.fsync(stream.fileno())
                    try:
                        publish_no_replace(temp, target)
                    except FileExistsError:
                        pass  # Another process published this content first.
                finally:
                    temp.unlink(missing_ok=True)
            self.read(dossier_id)
        return dossier_id
