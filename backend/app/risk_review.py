"""B4 -> B5 boundary. Release pins are internal and never accepted from n8n or a browser."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
from time import monotonic

from app.quant_store import digest
from app.risk_contracts import RiskInputs
from app.risk_engine import POLICY, POLICY_HASH, assess
from app.storage_budget import MIB
from app.validation_store import ValidationStore


@dataclass(frozen=True)
class Binding:
    dossier: str
    # A separately reviewed, content-addressed PAPER account/market/committee packet.
    # The current B4 delivery has no candidates and therefore needs no packet.
    packet_sha256: str | None = None


CURRENT = Binding('5b3f92b437746935f3a4d58991c84962e5f1f2dd7f774083659b66fbe5a35421')
MAX_DOSSIER_BYTES = 4 * MIB
MAX_PACKET_BYTES = MIB
BUDGET = dict(local_workers=1, dossiers=1, max_candidates=32, max_instruments=256,
              max_read_bytes=MAX_DOSSIER_BYTES + MAX_PACKET_BYTES, wall_seconds=5, network_calls=0, llm_calls=0, cost_eur=0)


class RiskReview:
    def __init__(self, storage, binding=CURRENT):
        self.store = ValidationStore(storage)
        self.store.limit = MAX_DOSSIER_BYTES
        self.root = Path(storage.output_root).absolute() / 'risk-inputs'
        self.binding = binding

    def packet(self):
        ident = self.binding.packet_sha256
        if not isinstance(ident, str) or not re.fullmatch('[a-f0-9]{64}', ident):
            raise ValueError('INVALID_REVIEWED_INPUT_ID')
        path = self.root / (ident + '.json')
        if path.resolve() != path.absolute() or path.is_symlink():
            raise ValueError('RISK_INPUT_PATH_REDIRECTED')
        with path.open('rb') as stream:
            raw = stream.read(MAX_PACKET_BYTES + 1)
        if len(raw) > MAX_PACKET_BYTES or hashlib.sha256(raw).hexdigest() != ident:
            raise ValueError('RISK_INPUT_INTEGRITY')
        return RiskInputs.model_validate_json(raw)

    def run(self, cycle_id, now, window_end):
        start = monotonic()
        cutoff, validation, cases, account = window_end, None, [], None
        outcome, reason = 'VETO', 'DOSSIER_INVALID'
        try:
            dossier = self.store.read(self.binding.dossier)
            decision = dossier['decision']
            validation = decision['status']
            expiry = datetime.fromisoformat(dossier['source']['review_expires_at'])
            if expiry.utcoffset() is None:
                raise ValueError('INVALID_SOURCE_EXPIRY')
            cutoff = min(cutoff, expiry)
            if now >= cutoff:
                reason = 'EVIDENCE_EXPIRED'
            elif validation == 'NO_CANDIDATES':
                outcome, reason = 'OBSERVE', 'NO_CANDIDATES'
            elif validation == 'EVIDENCE_INCOMPLETE':
                reason = 'VALIDATION_INCOMPLETE'
            elif (validation != 'CANDIDATES_FOR_REVIEW' or not dossier['point_in_time']
                    or dossier['reserved_oos_sessions'] <= 0 or dossier['temporal_reasons']):
                reason = 'INDEPENDENT_VALIDATION_REQUIRED'
            elif len(decision['candidate_ids']) > BUDGET['max_candidates']:
                reason = 'CANDIDATE_BUDGET_EXCEEDED'
            elif self.binding.packet_sha256 is None:
                reason = 'REVIEWED_PAPER_INPUTS_MISSING'
            else:
                reason = 'RISK_INPUTS_INVALID'
                packet = self.packet()
                if (packet.dossier_id != self.binding.dossier
                        or set(decision['candidate_ids']) != {p.candidate_id for p in packet.proposals}
                        or any('listing:' + p.listing_id not in dossier['instruments'] for p in packet.proposals)):
                    raise ValueError('INPUT_SCOPE_MISMATCH')
                account = dict(account_ref=packet.account.account_ref, snapshot_ref=packet.account.snapshot_ref,
                               as_of=packet.account.as_of.isoformat(), domain=packet.account.domain)
                cases = assess(packet, now, cutoff)
                cutoff = min(cutoff, *(datetime.fromisoformat(c['expires_at']) for c in cases))
                if all(c['veto'] for c in cases):
                    reason = 'ALL_PROPOSALS_VETOED'
                else:
                    outcome, reason = 'ASSESSED', 'PAPER_RISK_REVIEWED'
        except FileNotFoundError:
            reason = 'DOSSIER_MISSING' if validation is None else 'REVIEWED_PAPER_INPUTS_MISSING'
        except (ValueError, TypeError, LookupError, AttributeError, OSError, ArithmeticError, RecursionError):
            # No file paths, account values or validation inputs are copied to error messages.
            pass
        if monotonic() - start >= BUDGET['wall_seconds']:
            outcome, reason, cases = 'VETO', 'RISK_TIME_BUDGET_EXCEEDED', []
        record = dict(version='b5-risk-decision-v1', cycle_id=cycle_id, dossier_id=self.binding.dossier,
            input_ref=self.binding.packet_sha256, policy_id=POLICY.version, policy_hash=POLICY_HASH,
            decided_at=now.astimezone(timezone.utc).isoformat(), expires_at=cutoff.astimezone(timezone.utc).isoformat(),
            validation=validation, outcome=outcome, reason=reason, cases=cases, account=account,
            budget=BUDGET.copy(), mode='PAPER', orders_enabled=False, execution_ready=False)
        return dict(**record, decision_id=digest(record))
