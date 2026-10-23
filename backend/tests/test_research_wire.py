"""TEST_ONLY: serialization/guards; mocked output is never integration evidence."""
import asyncio
from copy import deepcopy
import json

import httpx
import pytest

from app.local_llm import LocalLLM, LocalLLMFailure
from app.research_arguments import BullResponse, BearResponse, ChairResponse, validate_arguments
from app.research_contracts import canonical, digest
from app.research_wire import DebateWire, strict_json, WIRE_VERSION


LONG_ID = 'E001122aabbcc'
OTHER_ID = 'E112233aabbcc'


def brief():
    return {'question': 'TEST_ONLY: interpretar las observaciones.', 'evidence_pack': {
        'schema_version': 'evidence-pack.v1', 'records': [
            {'id': LONG_ID, 'evidence_id': 'immutable', 'usable': True,
             'excerpt': 'TEST_ONLY: descripción literal E001122aabbcc, nunca sustituir texto.',
             'scope': 'INSTRUMENT', 'unit': 'USD', 'data_kind': 'market_quote'},
            {'id': OTHER_ID, 'evidence_id': 'immutable-stale', 'usable': False,
             'excerpt': 'TEST_ONLY: antiguo.', 'scope': 'INSTRUMENT'}]}, 'prior_arguments': {}}


def outputs():
    bull = {'i': 'B1', 't': 'La demanda podría sostener los cobros.',
            'm': 'Los contratos pueden aportar ingresos si se cobran.', 'e': ['E1'],
            'a': 'Los clientes cumplen sus contratos.', 'f': 'Cancelaciones que impidan cobrar.'}
    bear = {'i': 'R1', 'b': 'B1', 'o': 'El contrato no asegura recibir efectivo.',
            'm': 'La morosidad puede demorar el efectivo contratado.', 'e': [],
            'g': 'Falta evidencia de cobros efectivos.', 'c': 'Cobros verificados sin retrasos.'}
    chair = {'b': 'B1', 'r': 'R1', 'd': 'La demanda prevista no resuelve el riesgo de cobro.', 'e': ['E1'],
             'l': 'Falta comprobar los cobros.', 's': 'El mecanismo favorable depende de cobros que la objeción considera inciertos.',
             'c': 'A', 'u': ['Calendario de cobros.']}
    return bull, bear, chair


def test_round_trip_all_fields_and_cross_references_without_rewriting_text():
    data = brief()
    original = deepcopy(data)
    for contract, role, output in zip((BullResponse, BearResponse, ChairResponse),
                                     ('bull_advocate', 'bear_skeptic', 'cio_chair'), outputs()):
        wire = DebateWire(contract, data)
        assert wire.data['evidence_pack']['records'][0]['id'] == 'E1'
        assert wire.data['evidence_pack']['records'][0]['excerpt'] == original['evidence_pack']['records'][0]['excerpt']
        assert wire.data['evidence_pack']['records'][0]['evidence_id'] == 'immutable'
        decoded = wire.decode(output)
        assert validate_arguments(role, decoded, data['evidence_pack'], data['prior_arguments'])['state'] == 'ACCEPTED'
        assert len(canonical(output)) < len(canonical(decoded.model_dump()))
        assert wire.metadata == {'wire_version': WIRE_VERSION, 'wire_map_hash': digest(wire.to_wire)}
        if role != 'bull_advocate':
            assert wire.data['prior_arguments']['bull_advocate'][0]['e'] == ['E1']
            assert wire.data['prior_arguments']['bull_advocate'][0]['t'] == outputs()[0]['t']
        data['prior_arguments'][role] = decoded.model_dump()
    assert data['evidence_pack'] == original['evidence_pack']
    assert data['prior_arguments']['cio_chair']['conclusion'] == 'ABSTAIN_INSUFFICIENT_EVIDENCE'


@pytest.mark.parametrize('patch,code', [
    ({'e': ['invented']}, 'WIRE_UNKNOWN_ID_OR_ENUM'),
    ({'e': ['E2']}, 'WIRE_UNKNOWN_ID_OR_ENUM'),
    ({'e': ['E1', 'E1']}, 'WIRE_DUPLICATE_ITEM'),
    ({'t': 'Subirá un 100 por ciento.'}, 'WIRE_NUMERIC_PROSE'),
    ({'t': 'a' * 111}, 'WIRE_STRING_BUDGET'),
    ({'extra': 'ignored?'}, 'WIRE_FIELDS_INVALID'),
    ({'i': 'B2'}, 'WIRE_UNKNOWN_ID_OR_ENUM'),
])
def test_wire_refuses_unknown_fields_ids_duplicates_and_numeric_prose(patch, code):
    with pytest.raises(ValueError, match=code):
        DebateWire(BullResponse, brief()).decode(outputs()[0] | patch)


def test_missing_fields_duplicate_json_and_fabricated_prior_targets_rejected():
    value = outputs()[0]
    del value['f']
    with pytest.raises(ValueError, match='WIRE_FIELDS_INVALID'):
        DebateWire(BullResponse, brief()).decode(value)
    with pytest.raises(ValueError, match='WIRE_DUPLICATE_FIELD'):
        strict_json('{"t":"first","t":"second"}')
    data = brief()
    data['prior_arguments']['bull_advocate'] = DebateWire(BullResponse, data).decode(outputs()[0]).model_dump()
    with pytest.raises(ValueError, match='WIRE_UNKNOWN_ID_OR_ENUM'):
        DebateWire(BearResponse, data).decode(outputs()[1] | {'b': 'B3'})


def test_source_map_is_per_call_and_missing_prior_citation_is_not_silently_dropped():
    data = brief()
    one = DebateWire(BullResponse, data)
    data['evidence_pack']['records'].reverse()
    two = DebateWire(BullResponse, data)
    assert one.to_wire[LONG_ID] == 'E1' and two.to_wire[LONG_ID] == 'E2'
    assert one.metadata['wire_map_hash'] != two.metadata['wire_map_hash']
    data['prior_arguments']['bull_advocate'] = one.decode(outputs()[0]).model_dump()
    data['evidence_pack']['records'] = []
    with pytest.raises(ValueError, match='WIRE_PRIOR_EVIDENCE_MISSING'):
        DebateWire(BearResponse, data)


def mock_chat(content, finish='stop'):
    requests = []
    def handler(request):
        if request.url.path.endswith('/models'):
            return httpx.Response(200, json={'data': [{'id': 'TEST_ONLY'}]})
        payload = json.loads(request.content)
        requests.append(payload)
        return httpx.Response(200, json={'choices': [{'finish_reason': finish, 'message': {'content': content}}],
            'usage': {'prompt_tokens': 200, 'completion_tokens': 30, 'total_tokens': 230, 'secret': 'must-not-survive'},
            'timings': {'prompt_ms': 10, 'predicted_ms': 20, 'predicted_per_second': 15, 'raw_prompt': 'private'}})
    return LocalLLM(transport=httpx.MockTransport(handler)), requests


@pytest.mark.parametrize('key',['id','evidence_id'])
def test_python_comparisons_keep_resolvable_ids_in_compacted_prompt(key):
    from app.local_llm import model_view
    data = brief()
    data['computed_context'] = {'findings':[{key:LONG_ID,'finding':'TEST_ONLY comparación.'}]}
    model = model_view(DebateWire(BullResponse, data).data)
    assert model['computed_context']['findings'][0] == {'id':'E1','finding':'TEST_ONLY comparación.'}
    assert data['computed_context']['findings'][0][key] == LONG_ID


def test_grammar_pattern_itself_enforces_length_and_digits():
    import re
    pattern = DebateWire(BullResponse, brief()).schema['properties']['t']['pattern']
    assert re.fullmatch(pattern, 'Descripción cualitativa.')
    assert not re.fullmatch(pattern, 'breve')
    assert not re.fullmatch(pattern, 'x' * 111)
    assert not re.fullmatch(pattern, 'Habrá un cambio del 10 por ciento.')


def test_local_client_sends_compact_contract_and_restores_public_output():
    llm, requests = mock_chat(canonical(outputs()[0]))
    answer, metrics = asyncio.run(llm.chat('TEST_ONLY POLICY', brief(), contract=BullResponse, max_tokens=384))
    assert answer.arguments[0].supporting_evidence_ids == [LONG_ID]
    assert metrics['wire_version'] == WIRE_VERSION and metrics['finish_reason'] == 'stop'
    assert metrics['usage'] == {'prompt_tokens': 200, 'completion_tokens': 30, 'total_tokens': 230}
    assert 'raw_prompt' not in metrics['timings']
    payload = requests[0]
    assert set(payload['response_format']['schema']['properties']) == set(outputs()[0])
    assert 't=tesis' in payload['messages'][0]['content']
    assert 'UNTRUSTED_CONTENT_JSON' in payload['messages'][1]['content']
    assert 'tools' not in payload


@pytest.mark.parametrize('content,finish,code', [
    ('{"i":"B1"', 'length', 'TRUNCATED_OUTPUT'),
    ('{bad', 'stop', 'MALFORMED_LLM_RESULT'),
    (canonical(outputs()[0] | {'e': ['unknown']}), 'stop', 'WIRE_UNKNOWN_ID_OR_ENUM'),
    (canonical(outputs()[0])[:-1] + ',"i":"B1"}', 'stop', 'WIRE_DUPLICATE_FIELD'),
])
def test_failure_retains_safe_metrics_without_repair_or_raw_text(content, finish, code):
    llm, _ = mock_chat(content, finish)
    with pytest.raises(LocalLLMFailure, match=code) as caught:
        asyncio.run(llm.chat('TEST_ONLY POLICY', brief(), contract=BullResponse, max_tokens=384))
    metrics = caught.value.metrics
    assert metrics['usage']['completion_tokens'] == 30
    assert metrics['raw_model_output_hash'] == digest(content)
    assert metrics['finish_reason'] == finish
    assert metrics['wire_version'] == WIRE_VERSION
    assert content not in canonical(metrics)


def test_transport_timeout_has_safe_diagnostics_and_stays_timeout():
    def handler(request):
        if request.url.path.endswith('/models'):
            return httpx.Response(200, json={'data': [{'id': 'TEST_ONLY'}]})
        raise httpx.ReadTimeout('TEST_ONLY never expose this text', request=request)
    llm = LocalLLM(transport=httpx.MockTransport(handler))
    with pytest.raises(TimeoutError) as caught:
        asyncio.run(llm.chat('TEST_ONLY POLICY', brief(), contract=BullResponse, max_tokens=384))
    assert str(caught.value) == 'LOCAL_LLM_TIMEOUT'
    assert caught.value.metrics['wire_version'] == WIRE_VERSION
    assert caught.value.metrics['usage'] == {}
