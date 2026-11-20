"""Versioned accounting research. Fixed Decimal formulas, never generated code.

Annual comparisons use the comparative figures in the SAME filing. They are not
an as-reported historical dataset, a forecast, or an investment recommendation.
"""
from datetime import date
from decimal import Decimal, localcontext
from app.sec_normalize import annual_view, document_url
from app.company_reconciliation import opening_cash

TEMPLATE = 'company-accounting-v3.1'
FORMULAS = {
    'operating_margin': ('Margen operativo', 'operating_income', 'revenue', 'percent'),
    'parent_net_margin': ('Resultado de la matriz / ingresos', 'net_income', 'revenue', 'percent'),
    'current_ratio': ('Liquidez corriente', 'current_assets', 'current_liabilities', 'multiple'),
    'cfo_margin': ('Caja operativa / ingresos', 'operating_cash_flow', 'revenue', 'percent'),
    'liabilities_assets': ('Pasivos / activos', 'liabilities', 'assets', 'percent'),
}
ROLES = {
    'model_builder': 'fundamental_equity',
    'earnings_reviewer': 'value_quality',
    'valuation_reviewer': 'valuation',
    'numerical_reviewer': 'data_quality',
}
LIMITATIONS = [
    'Modelo contable anual descriptivo; no es una proyección integrada de tres estados.',
    'Comparativas del mismo informe, que pueden estar revisadas; no reconstruyen lo conocido por el mercado en el pasado.',
    'Conceptos estándar de la entidad; etiquetas propias, segmentos y causas de revisiones requieren lectura adicional.',
    'Sin consenso, guidance fechado ni transcript: no se calculan sorpresas ni se atribuyen opiniones a la dirección.',
    'Sin hipótesis de flujos, WACC, crecimiento terminal, peers y vínculo verificado con precios: DCF, comparables y precio objetivo bloqueados.',
]


def number(value):
    result = Decimal(value)
    if not result.is_finite() or len(str(value)) > 100 or abs(result) > Decimal('1e30'):
        raise ValueError('INVALID_MODEL_NUMBER')
    return result


def exact(value):
    return format(value, 'f')


def calculated(ident, label, formula, unit, inputs, *, value=None, reason=None):
    return dict(id=ident, label=label, formula=formula, unit=unit,
        state='AVAILABLE' if value is not None else 'BLOCKED',
        value=exact(value) if value is not None else None, reason=reason,
        evidence_ids=[f['id'] for f in inputs if f is not None])


def mapping(view):
    return {m['metric']: m['fact'] for m in view['metrics']} if view else {}


def period_comparable(current, prior):
    if not prior or prior['currency'] != current['currency']:
        return False
    days = lambda p: (date.fromisoformat(p['end']) - date.fromisoformat(p['start'])).days
    gap = (date.fromisoformat(current['start']) - date.fromisoformat(prior['end'])).days
    return abs(days(current) - days(prior)) <= 7 and 1 <= gap <= 7


def build_model(cik, facts, source):
    annual = annual_view(facts)
    if annual is None:
        raise ValueError('NO_ANNUAL_ACCOUNTS')
    if annual['state'] == 'AMBIGUOUS_CURRENCY':
        raise ValueError('AMBIGUOUS_CURRENCY')
    prior = annual_view([f for f in facts if f['accession'] == annual['accession']
                         and f['end'] < annual['start']])
    current, previous = mapping(annual), mapping(prior)
    selected = {f['id']: f for view in (annual, prior) if view for m in view['metrics'] if (f := m['fact'])}
    opening = opening_cash(facts, annual)
    if opening:
        selected[opening['id']] = opening
    evidence = {ident: dict(**f, snapshot_id=source['snapshot_id'], receipt_id=source['receipt_id'],
        received_at=source['received_at'], source_hash=source['payload_hash'],
        url=document_url(cik, f['accession'])) for ident, f in selected.items()}
    metrics, changes = [], []
    with localcontext() as ctx:
        ctx.prec = 48
        for ident, (label, numerator, denominator, unit) in FORMULAS.items():
            a, b = current.get(numerator), current.get(denominator)
            reason = 'Faltan magnitudes del mismo informe, periodo y divisa.'
            if ident=='liabilities_assets' and b and not a:
                missing = next(m for m in annual['metrics'] if m['metric']==numerator)
                reason = ('Hay importes contradictorios para el pasivo total.' if missing['state']=='CONFLICT' else
                          'Falta un subtotal de pasivos etiquetado para este balance. El ratio usa el subtotal declarado.')
            value = None
            if a and b and a['unit'] == b['unit']:
                if number(b['value']) > 0:
                    value = number(a['value']) / number(b['value']) * (100 if unit == 'percent' else 1)
                else:
                    reason = 'El denominador debe ser positivo; no se convierte en cero.'
            metrics.append(calculated(ident, label, f'{numerator} / {denominator}' + (' × 100' if unit == 'percent' else ''),
                unit, [a, b], value=value, reason=reason if value is None else None))
        cfo, capex = current.get('operating_cash_flow'), current.get('capex')
        # IFRS payment signs are not inferred from the tag alone.
        cash_proxy = None
        reason = 'Se necesitan caja operativa y pagos positivos de inmovilizado US-GAAP comparables.'
        if cfo and capex and cfo['unit'] == capex['unit'] and capex['taxonomy'] == 'us-gaap' and number(capex['value']) >= 0:
            cash_proxy = number(cfo['value']) - number(capex['value'])
        metrics.append(calculated('cfo_less_ppe', 'Caja operativa menos inversión material',
            'operating_cash_flow − capex', annual['currency'], [cfo, capex], value=cash_proxy,
            reason=reason if cash_proxy is None else 'Medida parcial; no equivale a flujo libre para descontar en un DCF.'))
        comparable = period_comparable(annual, prior)
        for key in ('revenue', 'operating_income', 'net_income', 'operating_cash_flow', 'diluted_eps'):
            a, b = current.get(key), previous.get(key)
            value = delta = None
            reason = 'No hay periodos anuales consecutivos comparables en el mismo informe.'
            if comparable and a and b:
                if (a['taxonomy'], a['concept'], a['unit']) != (b['taxonomy'], b['concept'], b['unit']):
                    reason = 'Cambió el concepto o su unidad; se bloquea la comparación.'
                else:
                    delta = number(a['value']) - number(b['value'])
                    if number(b['value']) > 0:
                        value = delta / number(b['value']) * 100
                        reason = None
                    else:
                        reason = 'Base anterior nula o negativa: se muestra la diferencia, sin porcentaje.'
            item = calculated(key, next(m['label'] for m in annual['metrics'] if m['metric'] == key),
                '(actual − anterior) / anterior × 100', 'percent', [a, b], value=value, reason=reason)
            item.update(current=a['value'] if a else None, previous=b['value'] if b else None,
                        delta=exact(delta) if delta is not None else None, source_unit=a['unit'] if a else None)
            changes.append(item)
    return dict(template_version=TEMPLATE, entity_id=cik, instrument_ids=[], source=source,
        annual=annual, comparative=prior, metrics=metrics, evidence=evidence, roles=ROLES,
        opening_cash_id=opening['id'] if opening else None,
        earnings=dict(state='DESCRIPTIVE', basis='SAME_FILING_COMPARATIVES', changes=changes,
            consensus='NOT_AVAILABLE', guidance='NOT_AVAILABLE', transcript='NOT_AVAILABLE',
            period_note='Ventanas de 52/53 semanas admitidas con diferencia máxima de siete días; sin ajuste por semana adicional.'),
        valuation=dict(state='BLOCKED', target_price=None, dcf=None, comparables=None,
            missing=['Flujos proyectados y supuestos fechados', 'WACC y crecimiento terminal',
                     'Puente completo de deuda, caja y capital', 'Peers justificados', 'Identidad y precio vinculados']),
        narrative=dict(state='NOT_REQUESTED', reason='Entrega determinista; no se ha ejecutado ni simulado una inferencia local.'),
        limitations=LIMITATIONS, execution_ready=False, backtest_ready=False)
