"""Bounded role context and a minimum, non-semantic debate quality guard."""
import re


def role_context(role_id, prior):
    # Bull develops an independent argument, rather than copying the last analyst.
    # Bear receives the actual Bull argument; Chair receives both sides in full.
    allowed = {'bear_skeptic': {'bull_advocate'},
               'cio_chair': {'bull_advocate', 'bear_skeptic'}}.get(role_id, set())
    return [{'role': r['role_id'], 'thesis': r['opinion'].get('thesis', ''),
             'risks': r['opinion'].get('risks', []),
             'key_disagreements': r['opinion'].get('key_disagreements', [])}
            for r in prior if r['role_id'] in allowed and r.get('opinion')]


def validate_debate(role_id, opinion, prior):
    if role_id not in ('bull_advocate', 'bear_skeptic', 'cio_chair'):
        return
    if not opinion.thesis.strip() or not opinion.risks or not opinion.invalidation_conditions:
        raise ValueError('DEBATE_ARGUMENT_MISSING')
    if role_id == 'bear_skeptic':
        bull = next((r['opinion'] for r in prior if r['role_id'] == 'bull_advocate'), None)
        if not bull:
            raise ValueError('DEPENDENCY_INCOMPLETE')
        normalize = lambda text: re.sub(r'\W+', '', text.casefold())
        if normalize(bull.get('thesis', '')) == normalize(opinion.thesis):
            raise ValueError('DEBATE_DUPLICATE_THESIS')
        if not opinion.key_disagreements:
            raise ValueError('DEBATE_DISAGREEMENT_MISSING')
    # Passing this guard is not proof of semantic quality: acceptance also
    # requires reading the actual evidence and both generated arguments.
