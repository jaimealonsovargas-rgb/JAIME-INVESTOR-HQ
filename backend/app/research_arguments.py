"""Different contracts for advocacy, criticism and synthesis; never orders."""
import re
from difflib import SequenceMatcher
from typing import Literal
from pydantic import Field
from app.research_contracts import Strict, Opinion, Claim


class BullArgument(Strict):
    argument_id: Literal['B1', 'B2', 'B3']
    thesis: str = Field(min_length=12, max_length=700)
    mechanism: str = Field(min_length=12, max_length=700)
    supporting_evidence_ids: list[str] = Field(min_length=1, max_length=6)
    assumption: str = Field(min_length=8, max_length=400)
    falsification: str = Field(min_length=8, max_length=400)


class BullResponse(Strict):
    arguments: list[BullArgument] = Field(min_length=1, max_length=3)


class BearArgument(Strict):
    argument_id: Literal['R1', 'R2', 'R3']
    target_bull_argument_id: str
    objection: str = Field(min_length=12, max_length=700)
    mechanism: str = Field(min_length=12, max_length=700)
    counter_evidence_ids: list[str] = Field(max_length=6)
    evidence_gap: str = Field(max_length=400)
    change_of_mind: str = Field(min_length=8, max_length=400)


class BearResponse(Strict):
    objections: list[BearArgument] = Field(min_length=1, max_length=3)


class Finding(Strict):
    bull_argument_id: str
    bear_argument_id: str
    disagreement: str = Field(min_length=12, max_length=700)
    evidence_ids: list[str] = Field(min_length=1, max_length=6)
    limitation: str = Field(min_length=8, max_length=400)


class ChairResponse(Strict):
    findings: list[Finding] = Field(min_length=1, max_length=3)
    synthesis: str = Field(min_length=12, max_length=900)
    conclusion: Literal['CONDITIONAL_RESEARCH', 'ABSTAIN_INSUFFICIENT_EVIDENCE']
    unknowns: list[str] = Field(min_length=1, max_length=5)


CONTRACTS = {'bull_advocate': BullResponse, 'bear_skeptic': BearResponse, 'cio_chair': ChairResponse}
TASKS = {
    'bull_advocate': 'Construye el mejor caso A FAVOR de la tesis. Explica un mecanismo causal CONDICIONAL, con evidencias citadas, supuesto y falsación. No enumeres solo carencias. Uno a tres argumentos diferentes.',
    'bear_skeptic': 'Construye el mejor caso EN CONTRA. Refuta o limita un mecanismo concreto de Bull mediante una evidencia contraria o laguna específica. Cita target_bull_argument_id. No copies su tesis ni su mecanismo. Explica qué prueba cambiaría tu juicio.',
    'cio_chair': 'Confronta cada argumento Bull y su objeción Bear por ID. Explica el desacuerdo real, pondera las fuentes y límites y sintetiza sin BUY/SELL ni órdenes. Abstente si la evidencia no resuelve el desacuerdo.',
}
for role_id in TASKS:
    TASKS[role_id] += (' Prioriza UN argumento sólido y breve; añade otros solo si son independientes. '
        'Redacta argumentos cualitativos: no copies cifras, fechas, porcentajes ni cantidades en palabras. '
        'Python ya presenta los valores exactos y sus fuentes. Los identificadores van solo en campos de IDs. '
        'No cambies ni niegues los hechos aportados para defender tu rol. Un mecanismo explica cómo una causa produce un efecto; '
        'no escribas la etiqueta "mecanismo causal" como respuesta. El supuesto debe ser una condición NO demostrada, '
        'no un hecho contrario a las fuentes. Menos de sesenta palabras por campo.')


def tokens(text):
    return re.findall(r'\w+', text.casefold())


def duplicate(a, b):
    left, right = tokens(a), tokens(b)
    if not left or not right:
        return False
    overlap = len(set(left) & set(right)) / max(1, len(set(left) | set(right)))
    return SequenceMatcher(None, left, right).ratio() >= .82 or overlap >= .85


def validate_arguments(role_id, response, pack, prior):
    """Structural/lexical guard only, NOT a proof of financial reasoning."""
    available = {e['id'] for e in pack['records'] if e['usable']}
    bull = {a['argument_id']: a for a in prior.get('bull_advocate', {}).get('arguments', [])}
    bear = {a['argument_id']: a for a in prior.get('bear_skeptic', {}).get('objections', [])}
    data = response.model_dump()
    rows = data.get('arguments', data.get('objections', data.get('findings', [])))
    ids = [a.get('argument_id') for a in rows if 'argument_id' in a]
    if len(ids) != len(set(ids)):
        raise ValueError('ARGUMENT_ID_DUPLICATE')
    headline = 'thesis' if role_id == 'bull_advocate' else 'objection'
    if role_id != 'cio_chair' and any(duplicate(row[headline], previous[headline])
                                    for index, row in enumerate(rows) for previous in rows[:index]):
        raise ValueError('ARGUMENT_CONTENT_DUPLICATE')
    if role_id != 'cio_chair' and any(duplicate(row['mechanism'], previous['mechanism'])
                                    for index, row in enumerate(rows) for previous in rows[:index]):
        raise ValueError('ARGUMENT_CONTENT_DUPLICATE')
    for row in rows:
        citations = row.get('supporting_evidence_ids', row.get('counter_evidence_ids', row.get('evidence_ids', [])))
        if any(i not in available for i in citations):
            raise ValueError('UNKNOWN_OR_UNUSABLE_EVIDENCE')
        numeric = r'(?<![\w])[-+]?\d+(?:[.,]\d+)*'
        source_numbers = set(re.findall(numeric, ' '.join(e['excerpt'] for e in pack['records'] if e['id'] in citations)))
        text = ' '.join(v for k, v in row.items() if isinstance(v, str) and not k.endswith('_id'))
        if any(n not in source_numbers for n in re.findall(numeric, text)):
            raise ValueError('UNGROUNDED_NUMBER')
        if role_id == 'bear_skeptic':
            target = bull.get(row['target_bull_argument_id'])
            if not target:
                raise ValueError('UNKNOWN_BULL_ARGUMENT')
            if not citations and len(row['evidence_gap'].strip()) < 12:
                raise ValueError('COUNTER_EVIDENCE_OR_GAP_REQUIRED')
            if duplicate(row['mechanism'], target['mechanism']) or duplicate(row['objection'], target['thesis']):
                raise ValueError('DEBATE_SEMANTIC_OVERLAP')
        if role_id == 'cio_chair':
            b, r = bull.get(row['bull_argument_id']), bear.get(row['bear_argument_id'])
            if not b or not r or r['target_bull_argument_id'] != row['bull_argument_id']:
                raise ValueError('UNKNOWN_DEBATE_PAIR')
    if role_id == 'cio_chair':
        citations = {i for row in rows for i in row['evidence_ids']}
        numbers = set(re.findall(numeric, ' '.join(e['excerpt'] for e in pack['records'] if e['id'] in citations)))
        narrative = ' '.join([data['synthesis'], *data['unknowns']])
        if any(n not in numbers for n in re.findall(numeric, narrative)):
            raise ValueError('UNGROUNDED_NUMBER')
    return {'state': 'ACCEPTED', 'basis': 'STRUCTURAL_AND_LEXICAL_CHECKS_ONLY', 'human_review': 'PENDING'}


def to_opinion(role_id, response, pack):
    """Display projection of genuine output; only Python copies exact facts."""
    data = response.model_dump()
    rows = data.get('arguments', data.get('objections', data.get('findings', [])))
    cited = {i for row in rows for i in row.get('supporting_evidence_ids', row.get('counter_evidence_ids', row.get('evidence_ids', [])))}
    facts = [Claim(claim_type='FACT', text=e['excerpt'], evidence_ids=[e['evidence_id']], confidence='MEDIUM') for e in pack['records'] if e['id'] in cited][:12]
    thesis = data.get('synthesis') or rows[0].get('thesis', rows[0].get('objection', ''))
    return Opinion(overview=thesis, thesis=thesis, claims=facts,
                   unknowns=data.get('unknowns', [row.get('assumption', row.get('evidence_gap', '')) for row in rows]),
                   invalidation_conditions=[row.get('falsification', row.get('change_of_mind', row.get('limitation', ''))) for row in rows],
                   risks=[row.get('assumption', row.get('objection', row.get('limitation', ''))) for row in rows],
                   key_disagreements=[row.get('disagreement', row.get('mechanism', '')) for row in rows],
                   research_view='INSUFFICIENT_EVIDENCE')
