"""P4 contracts: evidence-bound research, never executable instructions."""
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


def utc():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sanitize(value: str) -> str:
    # No markup, terminal control characters or bidi controls enter a prompt/UI.
    value = re.sub(r'<[^>]*>', '', value)
    return ''.join(c for c in value if c in '\n\t' or (ord(c) >= 32 and c not in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069'))[:4000]


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class Claim(Strict):
    claim_type: Literal['FACT', 'INTERPRETATION', 'GAP', 'HYPOTHESIS']
    text: str = Field(min_length=1, max_length=1200)
    evidence_ids: list[str] = Field(max_length=12)
    confidence: Literal['LOW', 'MEDIUM', 'HIGH']


class Opinion(Strict):
    overview: str = Field(max_length=1200)
    claims: list[Claim] = Field(max_length=12)
    unknowns: list[str] = Field(max_length=12)
    invalidation_conditions: list[str] = Field(max_length=8)
    research_view: Literal['POSITIVE', 'NEUTRAL', 'NEGATIVE', 'INSUFFICIENT_EVIDENCE']


class CreateCase(Strict):
    instrument_id: str = Field(min_length=1, max_length=64)
    question: str = Field(default='Evaluar evidencia, contexto y límites del instrumento.', min_length=1, max_length=800)


class RunCase(Strict):
    priority: int = Field(default=10, ge=0, le=100)
    refresh_public: bool = False


def ground(opinion: Opinion, evidence: list[dict]) -> list[dict]:
    """A citation is not proof of an interpretation. Only exact excerpts are verified.

    Numeric tokens must occur in the cited record. Unsupported facts are never
    promoted by model self-confidence; semantic entailment remains UNVERIFIED.
    """
    known = {e['id']: e for e in evidence}
    rows = []
    for claim in opinion.claims:
        if any(i not in known for i in claim.evidence_ids):
            raise ValueError('UNKNOWN_EVIDENCE')
        cited = [known[i] for i in claim.evidence_ids]
        if claim.claim_type == 'FACT' and not cited:
            raise ValueError('FACT_WITHOUT_EVIDENCE')
        numbers = re.findall(r'(?<![\w])[-+]?\d+(?:[.,]\d+)*', claim.text)
        available = ' '.join(canonical(e['content']) for e in cited)
        if numbers and (not cited or any(n not in available for n in numbers)):
            raise ValueError('UNGROUNDED_NUMBER')
        valid = bool(cited) and all(e['freshness'] == 'FRESH' and e['rights_ok'] and e.get('available', True) for e in cited)
        exact = any(claim.text == e['content'].get('excerpt') for e in cited)
        rows.append({**claim.model_dump(), 'text': sanitize(claim.text), 'claim_id': digest(claim.model_dump()),
                     'verified': valid and exact and claim.claim_type == 'FACT',
                     'grounding': 'VERIFIED_EXTRACT' if valid and exact and claim.claim_type == 'FACT' else 'UNVERIFIED', 'timestamp': utc()})
    # Narratives cannot smuggle unsupported financial figures around claims.
    for text in [opinion.overview, *opinion.unknowns, *opinion.invalidation_conditions]:
        if re.search(r'\d', text):
            raise ValueError('NUMBERS_OUTSIDE_CLAIMS')
    return rows
