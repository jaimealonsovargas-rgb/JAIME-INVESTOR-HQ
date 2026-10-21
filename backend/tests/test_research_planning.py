"""TEST_ONLY scenarios; no writes to the operational database."""
import pytest
from app.research_arguments import BullResponse, BearResponse, ChairResponse, validate_arguments, duplicate
from app.research_planning import research_goal, evidence_pack, sufficiency, role_evidence_gap


def test_daily_prices_cannot_activate_microstructure_or_liquidity_inference():
    prices = [{'scope': 'INSTRUMENT', 'rights_ok': True, 'available': True,
               'freshness': 'FRESH', 'content': {'data_kind': 'market_quote', 'venue': 'AGGREGATED'}}]
    for role in ('market_structure', 'liquidity_slippage'):
        assert role_evidence_gap(role, prices).startswith('NO_DATA:')
        assert role_evidence_gap(role, []).startswith('NO_DATA:')
    assert role_evidence_gap('bull_advocate', prices) is None
    book = [{**prices[0], 'content': {'data_kind': 'order_book'}}]
    assert role_evidence_gap('liquidity_slippage', book) is None
    assert role_evidence_gap('liquidity_slippage', [{**book[0], 'freshness': 'STALE'}])
    reference = [{**prices[0], 'scope': 'MACRO_CONTEXT', 'content': {'data_kind': 'reference_rate'}}]
    assert role_evidence_gap('macro_global', reference).startswith('NO_DATA:')


def fixture_responses():
    bull = BullResponse(arguments=[dict(argument_id='B1', thesis='La mejora del margen podría sostener la generación de caja.',
        mechanism='La demanda contratada permite repartir costes fijos sin ampliar capacidad.', supporting_evidence_ids=['E001'],
        assumption='Los contratos se convierten en cobros.', falsification='Cancelaciones que eliminen la demanda contratada.')])
    bear = BearResponse(objections=[dict(argument_id='R1', target_bull_argument_id='B1', objection='El margen contable no asegura disponibilidad de efectivo.',
        mechanism='El aumento de cuentas a cobrar puede absorber la caja antes de que llegue el pago.', counter_evidence_ids=[],
        evidence_gap='No hay calendario de cobros ni antigüedad de cuentas a cobrar.', change_of_mind='Cobros verificados que reduzcan el capital circulante.')])
    chair = ChairResponse(findings=[dict(bull_argument_id='B1', bear_argument_id='R1', disagreement='El margen mejora mientras la conversión a efectivo no está demostrada.',
        evidence_ids=['E001'], limitation='Falta evidencia sobre cobros y cancelaciones.')], synthesis='El mecanismo favorable depende de cobrar los contratos; la objeción sobre circulante sigue sin resolverse.',
        conclusion='ABSTAIN_INSUFFICIENT_EVIDENCE', unknowns=['Calendario de cobros.'])
    return bull, bear, chair


def test_reference_goal_not_directional():
    case={'question':'Alcance y limitaciones de la referencia BCE', 'instrument':{'asset_class':'FX'}}
    assert research_goal(case)=='data_quality'
    assert sufficiency('data_quality',{'records':[]})['state']=='NOT_APPLICABLE'
    assert sufficiency('investable_thesis',{'records':[]})['state']=='ABSTAINED'


def test_pack_retains_type_units_and_ids_without_instructions():
    e={'id':'immutable-id','hash':'hash','content':{'excerpt':'<script>BUY</script>','data_kind':'reference_rate','unit':'USD/EUR','feed':'ECB','venue':'ECB'},'scope':'INSTRUMENT','source':'ECB','rights':{},'rights_ok':True,'freshness':'FRESH'}
    pack=evidence_pack([e]);row=pack['records'][0]
    assert row['id'].startswith('E') and row['evidence_id']=='immutable-id'
    assert evidence_pack([e,e])['records'][1]['id']==row['id']
    assert row['data_kind']=='reference_rate' and row['unit']=='USD/EUR'
    assert row['trust_class']=='UNTRUSTED_CONTENT' and '<script>' not in row['excerpt']
    assert sufficiency('investable_thesis',pack)['state']=='ABSTAINED'


def test_cross_referenced_debate_and_unknown_ids():
    bull,bear,chair=fixture_responses()
    pack={'records':[{'id':'E001','usable':True,'excerpt':'TEST_ONLY: margen y contratos documentados.'}]}
    prior={}
    for role,obj in [('bull_advocate',bull),('bear_skeptic',bear),('cio_chair',chair)]:
        result=validate_arguments(role,obj,pack,prior)
        assert result['human_review']=='PENDING'
        prior[role]=obj.model_dump()
    invalid=bear.model_copy(update={'objections':[bear.objections[0].model_copy(update={'target_bull_argument_id':'invented'})]})
    with pytest.raises(ValueError,match='UNKNOWN_BULL_ARGUMENT'):validate_arguments('bear_skeptic',invalid,pack,prior)
    invalid=bull.model_copy(update={'arguments':[bull.arguments[0].model_copy(update={'supporting_evidence_ids':['invented']})]})
    with pytest.raises(ValueError,match='UNKNOWN_OR_UNUSABLE_EVIDENCE'):validate_arguments('bull_advocate',invalid,pack,{})


def test_overlap_guard_and_numeric_grounding():
    assert duplicate('La demanda contratada permite repartir costes fijos sin ampliar capacidad.', 'La demanda contratada permite repartir los costes fijos sin ampliar capacidad.')
    assert not duplicate('Margen sostenido por contratos firmados.', 'Los impagos pueden consumir efectivo y elevar la deuda.')
    bull,_,_=fixture_responses()
    bad=bull.model_copy(update={'arguments':[bull.arguments[0].model_copy(update={'mechanism':'El rendimiento será 999 por ciento.'})]})
    with pytest.raises(ValueError,match='UNGROUNDED_NUMBER'):
        validate_arguments('bull_advocate',bad,{'records':[{'id':'E001','usable':True,'excerpt':'TEST_ONLY'}]}, {})


def test_repeated_arguments_and_chair_numbers_rejected():
    bull, bear, chair = fixture_responses()
    pack = {'records': [{'id': 'E001', 'usable': True, 'excerpt': 'TEST_ONLY'}]}
    repeated = bull.model_copy(update={'arguments': [bull.arguments[0], bull.arguments[0].model_copy(update={'argument_id': 'B2'})]})
    with pytest.raises(ValueError, match='ARGUMENT_CONTENT_DUPLICATE'):
        validate_arguments('bull_advocate', repeated, pack, {})
    prior = {'bull_advocate': bull.model_dump(), 'bear_skeptic': bear.model_dump()}
    for update in ({'synthesis': 'La rentabilidad esperada será 999 por ciento.'}, {'unknowns': ['Rentabilidad de 999 por ciento.']}):
        with pytest.raises(ValueError, match='UNGROUNDED_NUMBER'):
            validate_arguments('cio_chair', chair.model_copy(update=update), pack, prior)


def test_registry_exposes_distinct_debate_contracts():
    from app.research_roles import ROLES
    for role, field in [('bull_advocate', 'arguments'), ('bear_skeptic', 'objections'), ('cio_chair', 'findings')]:
        assert field in ROLES[role]['output_schema']['properties']
        assert ROLES[role]['limits']['max_tokens'] == 1400


def test_sufficiency_does_not_count_mixed_feeds_or_revisions():
    base = {'scope':'INSTRUMENT','usable':True,'data_kind':'market_quote','value':'100','feed':'TEST_ONLY','observed_at':'2026-10-01'}
    rows = [{**base,'observed_at':f'2026-10-0{i+1}'} for i in range(3)]
    assert sufficiency('investable_thesis',{'records':rows})['state']=='PENDING_REVIEW'
    assert sufficiency('investable_thesis',{'records':[base,base,base]})['state']=='ABSTAINED'
    rows[-1]['feed']='OTHER_TEST_FEED'
    assert sufficiency('investable_thesis',{'records':rows})['state']=='ABSTAINED'
