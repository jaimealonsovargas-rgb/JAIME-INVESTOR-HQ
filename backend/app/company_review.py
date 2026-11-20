"""Read-only arithmetic review using exact rational numbers, independent of builder."""
from fractions import Fraction
from app.company_reconciliation import cash_check, decimal_text
from app.filing_reconciliation import review_equation


def review_model(model):
    facts = model['evidence']
    checks = []
    for row in model['metrics']:
        if row['state'] != 'AVAILABLE':
            checks.append(dict(id=row['id'], state='BLOCKED', reason=row['reason'], evidence_ids=row['evidence_ids']))
            continue
        inputs = [facts[i] for i in row['evidence_ids']]
        a, b = [Fraction(f['value']) for f in inputs]
        expected = a - b if row['id'] == 'cfo_less_ppe' else a / b * (100 if row['unit'] == 'percent' else 1)
        actual = Fraction(row['value'])
        good = abs(actual - expected) <= max(Fraction(1, 10**36), abs(expected) / 10**40)
        checks.append(dict(id=row['id'], state='PASS' if good else 'FAIL',
            reason='Cálculo contrastado con aritmética racional.' if good else 'Discrepancia de cálculo.', evidence_ids=row['evidence_ids']))
    for row in model['earnings']['changes']:
        if row['delta'] is None:
            continue
        a, b = [Fraction(facts[i]['value']) for i in row['evidence_ids']]
        good = Fraction(row['delta']) == a - b
        if row['value'] is not None:
            good = good and b > 0 and abs(Fraction(row['value']) - (a-b)/b*100) <= max(Fraction(1,10**36),abs((a-b)/b*100)/10**40)
        checks.append(dict(id='change_'+row['id'], state='PASS' if good else 'FAIL',
            reason='Variación contrastada con los dos datos de origen.', evidence_ids=row['evidence_ids']))
    m = {r['metric']: r['fact'] for r in model['annual']['metrics']}
    total = [m.get(k) for k in ('assets', 'balance_total')]
    if all(total) and all((f['unit'], f['end'], f['accession'], f['start']) ==
                         (model['annual']['currency'], model['annual']['end'], model['annual']['accession'], None) for f in total):
        residual = Fraction(total[0]['value']) - Fraction(total[1]['value'])
        checks.append(dict(id='balance_reported_total', state='PASS' if residual == 0 else 'FAIL',
            reason='Activos frente al total declarado de pasivos y patrimonio. Este cotejo no concilia sus componentes.',
            residual=decimal_text(residual), unit=model['annual']['currency'], evidence_ids=[f['id'] for f in total]))
    balance = [m.get(k) for k in ('assets', 'liabilities', 'equity_total')]
    if all(balance):
        if any((f['unit'], f['end'], f['accession'], f['start']) !=
               (model['annual']['currency'], model['annual']['end'], model['annual']['accession'], None) for f in balance):
            balance = []
    if all(balance) and balance:
        a, l, e = [Fraction(f['value']) for f in balance]
        # Exact agreement; no invented rounding/materiality threshold.
        checks.append(dict(id='balance', state='PASS' if a == l+e else 'FAIL',
            reason='Activos = pasivos + patrimonio total.' if a == l+e else 'Balance no conciliado; revisar alcance y redondeo del informe.',
            residual=decimal_text(a-l-e), unit=model['annual']['currency'], evidence_ids=[f['id'] for f in balance]))
    else:
        checks.append(dict(id='balance', state='BLOCKED', reason='Se necesitan activos, pasivos y patrimonio con minoritarios; no se sustituye por patrimonio de la matriz.', evidence_ids=[]))
    checks.append(cash_check(model))
    if coverage := model.get('annual_filing_coverage'):
        checks.append(dict(id='annual_filing_coverage',state=coverage['state'],reason=coverage['reason'],evidence_ids=[]))
    if filing := model.get('filing_statement'):
        for index,check in enumerate(checks):
            if check['id'] not in ('balance','cash_roll_forward'):
                continue
            evaluated = review_equation(model,check['id'],filing['equations'][check['id']])
            # A separately observed disagreement is never masked by a passing equation.
            if check['state']=='FAIL' or (check['state']=='PASS' and evaluated['state']=='BLOCKED'):
                checks.append({**evaluated,'id':'filed_'+check['id']})
            else:
                checks[index] = evaluated
    selected = [m['fact'] for view in (model['annual'], model['comparative']) if view for m in view['metrics'] if m['fact']]
    provenance = all(f['id'] in facts and f == {k: facts[f['id']][k] for k in f} and f['cik'] == model['entity_id'] for f in selected)
    checks.append(dict(id='provenance', state='PASS' if provenance else 'FAIL', reason='Cada input conserva identidad, documento, unidad, periodo y recibo.', evidence_ids=sorted(facts)))
    return dict(role_id='data_quality', reviewer_version='accounting-rational-review-v3',
        state='FAILED' if any(c['state']=='FAIL' for c in checks) else 'PARTIAL' if any(c['state']=='BLOCKED' for c in checks) else 'PASSED',
        checks=checks, scope='Revisión numérica independiente del constructor; no valida una tesis ni recomienda inversión.')
