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
    thesis: str = Field(default='', max_length=1200)
    catalysts: list[str] = Field(default_factory=list, max_length=6)
    risks: list[str] = Field(default_factory=list, max_length=6)
    key_disagreements: list[str] = Field(default_factory=list, max_length=6)


class CreateCase(Strict):
    research_goal: Literal['data_quality', 'macro_reference', 'descriptive_research', 'investable_thesis'] | None = None
    instrument_id: str = Field(min_length=1, max_length=64)
    question: str = Field(default='Evaluar evidencia, contexto y límites del instrumento.', min_length=1, max_length=800)


class RunCase(Strict):
    priority: int = Field(default=10, ge=0, le=100)
    refresh_public: bool = False
    analysis_depth: Literal['ordinary', 'deep'] = 'ordinary'
    include_local_summary: bool = False


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
        available = set(re.findall(r'(?<![\w])[-+]?\d+(?:[.,]\d+)*', ' '.join(canonical(e['content']) for e in cited)))
        if numbers and (not cited or any(n not in available for n in numbers)):
            raise ValueError('UNGROUNDED_NUMBER')
        valid = bool(cited) and all(e['freshness'] == 'FRESH' and e['rights_ok'] and e.get('available', True) for e in cited)
        exact = any(claim.text == e['content'].get('excerpt') for e in cited)
        rows.append({**claim.model_dump(), 'text': sanitize(claim.text), 'claim_id': digest(claim.model_dump()),
                     'verified': valid and exact and claim.claim_type == 'FACT',
                     'grounding': 'VERIFIED_EXTRACT' if valid and exact and claim.claim_type == 'FACT' else 'UNVERIFIED', 'timestamp': utc()})
    # Repeated figures in a summary inherit the exact verified claim references.
    # A number appearing somewhere in a cited blob is not sufficient.
    supported_numbers = set(n for row in rows if row['verified'] for n in re.findall(r'(?<![\w])[-+]?\d+(?:[.,]\d+)*', row['text']))
    for text in [opinion.overview, opinion.thesis, *opinion.unknowns, *opinion.invalidation_conditions, *opinion.catalysts, *opinion.risks, *opinion.key_disagreements]:
        if any(n not in supported_numbers for n in re.findall(r'(?<![\w])[-+]?\d+(?:[.,]\d+)*', text)):
            raise ValueError('NUMBERS_OUTSIDE_CLAIMS')
    return list({row['claim_id']: row for row in rows}.values())


def withhold_unsupported_narrative(opinion: Opinion, evidence: list[dict]):
    """Keep strict claim validation. Withhold whole unsupported numeric passages,
    never silently repair a number or pretend that a model's prose is evidence.
    The original output hash and affected field hashes remain auditable.
    """
    fields = ('overview', 'thesis', 'unknowns', 'invalidation_conditions', 'catalysts', 'risks', 'key_disagreements')
    empty = {key: '' if key in ('overview', 'thesis') else [] for key in fields}
    rows = ground(opinion.model_copy(update=empty), evidence)
    supported = {n for row in rows if row['verified'] for n in re.findall(r'(?<![\w])[-+]?\d+(?:[.,]\d+)*', row['text'])}
    withheld = []
    def check(text, path):
        text = sanitize(text)
        if any(n not in supported for n in re.findall(r'(?<![\w])[-+]?\d+(?:[.,]\d+)*', text)):
            withheld.append({'field': path, 'reason': 'NUMBERS_OUTSIDE_CLAIMS', 'text_hash': digest(text)})
            return 'NO VERIFICADO: pasaje omitido por contener cifras sin evidencia vinculada.'
        return text
    updates = {key: check(getattr(opinion, key), key) if key in ('overview', 'thesis') else [check(text, f'{key}[{i}]') for i, text in enumerate(getattr(opinion, key))] for key in fields}
    if withheld:
        updates['research_view'] = 'INSUFFICIENT_EVIDENCE'
    return opinion.model_copy(update=updates), withheld
