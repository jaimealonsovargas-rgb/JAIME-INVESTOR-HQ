"""Objective routing and typed evidence, independent of a generative model."""
from app.research_contracts import digest, sanitize

GOALS = {'data_quality', 'macro_reference', 'investable_thesis'}


def role_evidence_gap(role_id, evidence):
    """Do not ask a model to manufacture microstructure from aggregated prices."""
    if role_id == 'macro_global':
        macro = [e for e in evidence if e['scope'] == 'MACRO_CONTEXT' and e['rights_ok']
                 and e.get('available', True) and e['freshness'] == 'FRESH'
                 and e['content'].get('data_kind') == 'macro_series']
        if not macro:
            return 'NO_DATA: no hay series macroeconómicas relevantes para una explicación del instrumento; una referencia de divisas no identifica causas ni régimen macro.'
        return None
    if role_id not in ('market_structure', 'liquidity_slippage'):
        return None
    direct = [e['content'] for e in evidence if e['scope'] == 'INSTRUMENT'
              and e['rights_ok'] and e.get('available', True) and e['freshness'] == 'FRESH']
    # Only explicitly typed, authorized microstructure data could open this lane.
    # Existing daily aggregates are not an order book, spread, venue rule or depth.
    kinds = {'market_structure', 'order_book'} if role_id == 'market_structure' else {'order_book'}
    if not any(c.get('data_kind') in kinds for c in direct):
        return ('NO_DATA: falta evidencia específica de microestructura; los precios agregados no describen reglas ni libro de una plaza.'
                if role_id == 'market_structure' else
                'NO_DATA: faltan bid/ask, profundidad y costes verificables; no se estima spread ni slippage desde precios diarios.')
    return None


def research_goal(case):
    explicit = case.get('research_goal')
    if explicit in GOALS:
        return explicit
    question = case['question'].casefold()
    if any(word in question for word in ('calidad de datos', 'derechos', 'alcance', 'limitaciones de la referencia')):
        return 'data_quality'
    if case['instrument'].get('asset_class') in ('MACRO', 'MACRO_SERIES') or any(word in question for word in ('referencia bce', 'contexto macro', 'serie estadística')):
        return 'macro_reference'
    return 'investable_thesis'


def evidence_pack(evidence):
    records = []
    for e in evidence:
        c = e['content']
        records.append({'id': 'E' + digest(e['id'])[:12], 'evidence_id': e['id'], 'scope': e['scope'],
                        'data_kind': c.get('data_kind', 'derived_feature' if e['scope']=='DERIVED_FEATURE' else 'context'),
                        'feed': c.get('feed', e['source']), 'venue': c.get('venue'),
                        'provider': e.get('provider'), 'series_id': c.get('series_id'),
                        'period_precision': c.get('period_precision'),
                        'currency': c.get('currency'), 'unit': c.get('unit'),
                        'observed_at': e.get('observed_at'), 'source': e['source'],
                        'rights': e['rights'], 'freshness': e['freshness'],
                        'usable': bool(e['rights_ok'] and e.get('available', True) and e['freshness']=='FRESH'),
                        'value': c.get('value'), 'excerpt': sanitize(c.get('excerpt', '')),
                        'trust_class': 'UNTRUSTED_CONTENT'})
    return {'schema_version': 'evidence-pack.v1', 'records': records,
            'manifest_hash': digest({e['id']: e['hash'] for e in evidence}),
            'limitations': ['Una referencia estadística no es spread, precio ejecutable ni plataforma.',
                            'El contexto MASTER no es evidencia del instrumento ni una posición en él.']}


def sufficiency(goal, pack):
    direct = [e for e in pack['records'] if e['scope']=='INSTRUMENT' and e['usable']]
    if goal != 'investable_thesis':
        return {'state': 'NOT_APPLICABLE', 'reason': 'Informe de referencia/calidad; debate direccional no aplicable.'}
    groups = {}
    for e in direct:
        if e['data_kind'] not in ('market_quote', 'ohlcv') or e.get('value') is None or not e.get('observed_at'):
            continue
        identity = tuple(e.get(k) for k in ('provider', 'feed', 'series_id', 'venue', 'currency', 'unit', 'period_precision', 'data_kind'))
        groups.setdefault(identity, set()).add(e['observed_at'])
    # Conservative evidence gate, not a suitability assessment or P5 risk veto.
    if not any(len(times) >= 3 for times in groups.values()):
        return {'state': 'ABSTAINED', 'reason': 'ABSTAIN_INSUFFICIENT_EVIDENCE: falta evidencia de mercado comparable y vigente.'}
    return {'state': 'PENDING_REVIEW', 'reason': 'Evidencia mínima disponible; los argumentos todavía requieren validación.'}
