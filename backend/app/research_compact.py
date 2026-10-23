"""Small descriptive LLM contract. Python owns all facts and calculations."""
import re
from pydantic import Field
from app.research_contracts import Strict, Opinion, Claim
from app.research_semantics import validate_financial_prose


class CompactResearch(Strict):
    summary: str = Field(min_length=20, max_length=420)
    evidence_ids: list[str] = Field(min_length=1, max_length=4)
    limitations: list[str] = Field(min_length=1, max_length=2)


def validate_compact(answer: CompactResearch, pack: dict) -> tuple[Opinion, dict]:
    usable = {row['id']: row for row in pack['records'] if row['usable'] and row['scope'] in ('INSTRUMENT', 'DERIVED_FEATURE')}
    if any(eid not in usable for eid in answer.evidence_ids):
        raise ValueError('UNKNOWN_OR_UNUSABLE_EVIDENCE')
    prose = ' '.join([answer.summary, *answer.limitations])
    if re.search(r'(?<![\w])[-+]?\d+(?:[.,]\d+)*', prose):
        raise ValueError('NUMBERS_OUTSIDE_CLAIMS')
    if re.search(r'\b(comprar|vender|buy|sell|rentabilidad garantizada|subirá|bajará)\b', prose, re.I):
        raise ValueError('UNSUPPORTED_DIRECTIONAL_VIEW')
    for text in [answer.summary, *answer.limitations]:
        validate_financial_prose(text, pack)
    excerpts = [usable[eid] for eid in answer.evidence_ids]
    facts = [Claim(claim_type='FACT', text=row['excerpt'], evidence_ids=[row['evidence_id']], confidence='MEDIUM')
             for row in excerpts]
    opinion = Opinion(overview=answer.summary, thesis='', claims=facts, unknowns=answer.limitations,
                      invalidation_conditions=['Revisar al actualizar datos, derechos o unidades.'],
                      research_view='INSUFFICIENT_EVIDENCE')
    return opinion, {'state': 'PROVISIONAL', 'basis': 'CONTRACT_AND_GROUNDING_ONLY',
                     'reason': 'Síntesis cualitativa; requiere revisión humana para inferencias causales.'}
