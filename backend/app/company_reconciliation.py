"""Conservative, exact checks. Never mix restricted cash with balance-sheet cash."""
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction


def decimal_text(value):
    from decimal import localcontext
    with localcontext() as ctx:
        ctx.prec = 100
        return format(Decimal(value.numerator) / Decimal(value.denominator), 'f')


def opening_cash(facts, annual):
    end = (date.fromisoformat(annual['start']) - timedelta(days=1)).isoformat()
    rows = [f for f in facts if f['metric'] == 'cash_restricted' and
            not f.get('quality_flags') and f['start'] is None and
            (f['end'], f['accession'], f['filed'], f['unit']) ==
            (end, annual['accession'], annual['filed'], annual['currency'])]
    return min(rows, key=lambda f: f['id']) if len({Decimal(f['value']) for f in rows}) == 1 else None


def cash_check(model):
    annual = model['annual']
    m = {r['metric']: r['fact'] for r in annual['metrics']}
    opening = model['evidence'].get(model.get('opening_cash_id'))
    ending = m.get('cash_restricted')
    flows = [m.get(k) for k in ('operating_cash_flow', 'investing_cash_flow',
                              'financing_cash_flow', 'restricted_cash_fx', 'restricted_cash_change')]
    rows = [opening, ending, *flows]
    ids = [f['id'] for f in rows if f]
    blocked = dict(id='cash_roll_forward', state='BLOCKED', evidence_ids=ids,
                   reason='Faltan saldo inicial/final, flujos, variación o divisas del mismo informe y alcance de efectivo restringido. No se asumen ceros.')
    if not all(rows):
        labels = ['saldo inicial', 'saldo final', 'flujo operativo', 'flujo de inversión',
                  'flujo de financiación', 'efecto de divisas compatible', 'variación declarada']
        return {**blocked, 'reason': 'Faltan: ' + ', '.join(label for label, fact in zip(labels, rows) if not fact) + '. No se mezclan alcances ni se asumen ceros.'}
    if any((f['cik'], f['accession'], f['filed'], f['unit'], f['taxonomy']) !=
           (model['entity_id'], annual['accession'], annual['filed'], annual['currency'], 'us-gaap') for f in rows):
        return {**blocked, 'reason': 'Identidad, informe, divisa o taxonomía incompatibles.'}
    expected_open = (date.fromisoformat(annual['start']) - timedelta(days=1)).isoformat()
    if (opening['end'] != expected_open or ending['end'] != annual['end'] or
        opening['start'] is not None or ending['start'] is not None or
        opening['concept'] != ending['concept'] or
        any((f['start'], f['end']) != (annual['start'], annual['end']) for f in flows)):
        return {**blocked, 'reason': 'Saldos o flujos de periodos/alcance incompatibles.'}
    start, end, operating, investing, financing, fx, reported = [Fraction(f['value']) for f in rows]
    residual = end - start - operating - investing - financing - fx
    reported_residual = end - start - reported
    # Fractions preserve exact arithmetic independently of Decimal context.
    return dict(id='cash_roll_forward', state='PASS' if residual == reported_residual == 0 else 'FAIL',
                reason='Saldo final − inicial = operación + inversión + financiación + divisas; cotejado con la variación declarada. Comprobación aritmética, no certificación del estado completo.',
                residual=decimal_text(residual), reported_residual=decimal_text(reported_residual),
                unit=annual['currency'], evidence_ids=ids)
