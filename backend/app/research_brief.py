"""Small, deterministic comparisons for interpretation. No forecast or LLM math."""
from decimal import Decimal, InvalidOperation


def computed_context(pack):
    findings = []
    descriptions = {
        'period_return': ('El cambio neto del periodo observado es positivo.',
                          'El cambio neto del periodo observado es negativo.',
                          'El cambio neto del periodo observado es nulo.'),
        'z_score': ('La última observación está por encima de la media de la muestra.',
                    'La última observación está por debajo de la media de la muestra.',
                    'La última observación coincide con la media de la muestra.'),
        'sample_volatility': ('Existe dispersión calculada de los cambios observados; no está anualizada.',
                               None, 'Los cambios de esta muestra tienen dispersión nula; no garantiza ausencia de riesgo.'),
        'max_drawdown_observed': (None, 'La muestra incluye una caída desde un máximo previo.',
                                  'No hubo caídas desde máximos en la muestra; no garantiza continuidad.'),
    }
    for row in pack['records']:
        if not row.get('usable') or row.get('scope') != 'DERIVED_FEATURE':
            continue
        name = row.get('excerpt', '').partition(':')[0]
        if name not in descriptions:
            continue
        try:
            value = Decimal(str(row.get('value')))
            if not value.is_finite():
                continue
        except InvalidOperation:
            continue
        description = descriptions[name][0 if value > 0 else 1 if value < 0 else 2]
        if description:
            findings.append({'id': row['id'], 'finding': description})
    return {'method': 'hq.comparisons.1', 'findings': findings,
            'scope': 'Estadísticas descriptivas ya calculadas por Python. No prueban causalidad, persistencia ni valoración justa.'}
