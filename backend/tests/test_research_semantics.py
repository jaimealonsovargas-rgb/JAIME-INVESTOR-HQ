"""TEST_ONLY typed financial contradictions; no data or model fabrication."""
import pytest
from app.research_arguments import BullResponse, validate_arguments
from app.research_compact import CompactResearch, validate_compact
from app.research_semantics import validate_financial_prose


def pack():
    return {'records': [
        {'id': 'E1', 'evidence_id': 'fixture-price', 'scope': 'INSTRUMENT',
         'data_kind': 'market_quote', 'usable': True, 'excerpt': 'TEST_ONLY: precio observado.'},
        {'id': 'E2', 'evidence_id': 'fixture-return', 'scope': 'DERIVED_FEATURE',
         'data_kind': 'derived_feature', 'usable': True, 'value': '-0.12', 'excerpt': 'period_return: -0.12'},
        {'id': 'E3', 'evidence_id': 'fixture-vol', 'scope': 'DERIVED_FEATURE',
         'data_kind': 'derived_feature', 'usable': True, 'value': '0.03', 'excerpt': 'sample_volatility: 0.03'},
    ]}


@pytest.mark.parametrize('text', [
    'No se han calculado estadísticas.', 'Sin métricas calculadas.',
    'No hay indicadores calculados.', 'No se ha calculado volatilidad histórica.',
    'Falta el dato de retorno del periodo.',
])
def test_explicit_denial_of_available_python_features_rejected(text):
    with pytest.raises(ValueError, match='CONTRADICTS_COMPUTED_FEATURES'):
        validate_financial_prose(text, pack())


@pytest.mark.parametrize('text', [
    'No se han calculado estadísticas fundamentales.',
    'Falta volatilidad implícita.', 'Falta rentabilidad futura.',
    'No hay métricas suficientes para valorar la empresa.',
    'No hay datos de ingresos ni ratios de valoración.',
    'El retorno observado es negativo.',
    'Si el retorno observado es positivo, se revisaría la hipótesis.',
    'No se sabe si el retorno futuro será positivo.',
    'La rentabilidad no está garantizada.',
    'No garantiza beneficios.',
    'Si los ingresos crecen, podrían reducir el peso de los costes.',
    'No sabemos si los ingresos aumentaron.',
    'Una fuente no demuestra causalidad.',
    'La muestra es limitada; una vez contrastada podría cambiar la lectura.',
])
def test_real_gaps_conditional_hypotheses_and_observed_sign_remain_allowed(text):
    validate_financial_prose(text, pack())


@pytest.mark.parametrize('value,text', [
    ('-0.12', 'El retorno observado es positivo.'),
    ('0.12', 'La rentabilidad del periodo fue negativa.'),
    ('0', 'El rendimiento calculado resulta positivo.'),
])
def test_sign_is_compared_by_decimal_not_the_model(value, text):
    evidence = pack()
    evidence['records'][1]['value'] = value
    with pytest.raises(ValueError, match='CONTRADICTS_RETURN_SIGN'):
        validate_financial_prose(text, evidence)


def test_stale_derived_values_cannot_certify_a_contradiction():
    evidence = pack()
    evidence['records'][1]['usable'] = False
    validate_financial_prose('El retorno observado es positivo.', evidence)


@pytest.mark.parametrize('text', ['Los ingresos aumentaron.', 'El margen operativo mejora y los beneficios crecen.'])
def test_prices_do_not_substantiate_company_accounts(text):
    with pytest.raises(ValueError, match='UNSUPPORTED_FINANCIAL_ASSERTION'):
        validate_financial_prose(text, pack())


def test_fundamental_source_is_not_rejected_by_price_only_guard():
    evidence = pack()
    evidence['records'].append({'id': 'F1', 'scope': 'INSTRUMENT', 'usable': True,
                                'data_kind': 'financial_statement', 'excerpt': 'TEST_ONLY: cuentas.'})
    validate_financial_prose('Los ingresos aumentaron.', evidence)
    # Passing this narrow guard does not certify the assertion or its citation.


@pytest.mark.parametrize('text', ['La rentabilidad está garantizada.', 'El mecanismo garantiza beneficios.'])
def test_guarantees_rejected(text):
    with pytest.raises(ValueError, match='UNSUPPORTED_GUARANTEE'):
        validate_financial_prose(text, pack())


@pytest.mark.parametrize('text', ['Subiría veinte por ciento.', 'Costaría un millón de euros.',
                                 'El cambio será de treinta y dos puntos básicos.'])
def test_written_amounts_cannot_bypass_qualitative_contract(text):
    with pytest.raises(ValueError, match='QUALITATIVE_NUMERIC_AMOUNT'):
        validate_financial_prose(text, pack())


def test_debate_and_compact_use_same_contradiction_guard():
    bull = BullResponse(arguments=[{'argument_id': 'B1', 'thesis': 'Si la recuperación persiste, habría apoyo.',
        'mechanism': 'El retorno observado es positivo.', 'supporting_evidence_ids': ['E2'],
        'assumption': 'Persistencia todavía no demostrada.', 'falsification': 'Una reversión observable de la trayectoria.'}])
    with pytest.raises(ValueError, match='CONTRADICTS_RETURN_SIGN'):
        validate_arguments('bull_advocate', bull, pack(), {})
    answer = CompactResearch(summary='No se han calculado estadísticas.', evidence_ids=['E2'],
                             limitations=['Faltan datos fundamentales.'])
    with pytest.raises(ValueError, match='CONTRADICTS_COMPUTED_FEATURES'):
        validate_compact(answer, pack())


def test_compact_retains_true_missing_fundamentals_gap():
    answer = CompactResearch(summary='La muestra aporta observaciones históricas comparables.', evidence_ids=['E2'],
                             limitations=['No se han calculado estadísticas fundamentales.'])
    _, quality = validate_compact(answer, pack())
    assert quality['state'] == 'PROVISIONAL'


def test_observation_is_not_a_bull_causal_mechanism():
    bull = BullResponse(arguments=[{'argument_id':'B1','thesis':'La trayectoria observada muestra una tendencia negativa.',
        'mechanism':'El cambio neto del periodo observado es negativo.', 'supporting_evidence_ids':['E2'],
        'assumption':'La trayectoria no es un indicador de causalidad.',
        'falsification':'La trayectoria no refleja caídas cada día.'}])
    with pytest.raises(ValueError,match='DEBATE_MECHANISM_MISSING'):
        validate_arguments('bull_advocate',bull,pack(),{})


def test_causal_validation_does_not_depend_on_a_verb_whitelist():
    bull = BullResponse(arguments=[{'argument_id':'B1','thesis':'Una recuperación podría sostenerse si cambia la demanda.',
        'mechanism':'La demanda nueva amortiguaría las ventas si persiste.', 'supporting_evidence_ids':['E2'],
        'assumption':'La nueva demanda todavía no está demostrada.',
        'falsification':'Una reversión de la recuperación observada.'}])
    assert validate_arguments('bull_advocate',bull,pack(),{})['human_review']=='PENDING'


@pytest.mark.parametrize('mechanism,assumption,code',[
    ('Mecanismo causal condicional: la demanda cambiaría la trayectoria.', 'Persistencia no demostrada.', 'DEBATE_CONTRACT_PARROT'),
    ('La demanda podría sostener el precio si cambia el equilibrio.', 'Una recuperación podría sostenerse si cambia la demanda.', 'DEBATE_CONTRACT_PARROT'),
    ('La demanda podría cambiar la trayectoria pero no se', 'Persistencia no demostrada.', 'DEBATE_INCOMPLETE_SENTENCE'),
])
def test_contract_echo_and_cut_off_clause_rejected(mechanism,assumption,code):
    bull=BullResponse(arguments=[{'argument_id':'B1','thesis':'Una recuperación podría sostenerse si cambia la demanda.',
        'mechanism':mechanism,'supporting_evidence_ids':['E2'],'assumption':assumption,
        'falsification':'Una reversión de la recuperación observada.'}])
    with pytest.raises(ValueError,match=code):validate_arguments('bull_advocate',bull,pack(),{})
