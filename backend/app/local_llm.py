"""Only loopback llama.cpp; no credentials, proxy, redirect or remote fallback."""
import json
import math
import os
import time
from urllib.parse import urlsplit
import httpx
from app.research_contracts import Opinion, canonical, digest
from app.research_wire import DebateWire, ROLES as WIRE_ROLES, strict_json


class NoLocalModel(Exception):
    pass


class LocalLLMFailure(ValueError):
    """Safe machine-readable failure plus diagnostics, never model/source prose."""
    def __init__(self, code, metrics):
        super().__init__(code)
        self.metrics = metrics


def _numbers(value, keys):
    if not isinstance(value, dict):
        return {}
    return {key: number for key, number in value.items() if key in keys and
            type(number) in (int, float) and math.isfinite(number) and number >= 0}


def model_view(value):
    """Compact repeated source metadata without dropping fact IDs, units or scope."""
    if isinstance(value, dict):
        if value.get('schema_version') == 'evidence-pack.v1' and isinstance(value.get('records'), list):
            fields = ('scope', 'data_kind', 'provider', 'series_id', 'feed', 'venue',
                      'currency', 'unit', 'period_precision')
            sources, identities, records = {}, {}, []
            for row in value['records']:
                descriptor = {k: row[k] for k in fields if row.get(k) is not None}
                identity = canonical(descriptor)
                source_id = identities.setdefault(identity, 'S' + str(len(identities) + 1))
                sources[source_id] = descriptor
                records.append({**{k: row.get(k) for k in ('id', 'observed_at', 'usable', 'excerpt')}, 'source_id': source_id})
            return {'schema_version': 'evidence-pack.compact.v1', 'sources': sources, 'records': records}
        return {k: model_view(v) for k, v in value.items() if k != 'evidence_id'
                and not (k == 'evidence' and 'evidence_pack' in value)}
    if isinstance(value, list):
        return [model_view(v) for v in value]
    return value


def argument_schema(contract, data):
    schema = contract.model_json_schema()
    key = {'BullResponse': 'arguments', 'BearResponse': 'objections', 'ChairResponse': 'findings'}.get(contract.__name__)
    if not key:
        return schema
    schema['properties'][key]['maxItems'] = 1
    # Python owns financial figures and their exact citations. Generative prose is
    # qualitative; ordinary validators still check all evidence and cross-links.
    aliases = [e['id'] for e in data.get('evidence_pack', {}).get('records', []) if e.get('usable')]
    for definition in [schema, *schema.get('$defs', {}).values()]:
        for name, prop in definition.get('properties', {}).items():
            if prop.get('type') == 'string' and not name.endswith('_id') and 'enum' not in prop and 'const' not in prop:
                prop.update(pattern='^[^0-9]*$', maxLength=min(prop.get('maxLength', 120), 220 if name == 'synthesis' else 120))
            if name in ('supporting_evidence_ids', 'counter_evidence_ids', 'evidence_ids') and aliases:
                prop['items'] = {'type': 'string', 'enum': aliases}
            if name == 'unknowns':
                prop.update(maxItems=2, items={'type': 'string', 'pattern': '^[^0-9]*$', 'minLength': 1, 'maxLength': 120})
    return schema


def grounded_schema(data):
    """Small llama.cpp-compatible schema. Python supplies the exact facts;
    free qualitative narrative remains explicitly unverified and validated separately.
    """
    schema = Opinion.model_json_schema()
    schema.pop('$defs', None)
    schema['required'] = list(schema['properties'])
    # This initial pipeline has no validated sufficiency rubric for a directional
    # investment conclusion. Descriptive research must not turn into a bullish
    # rating merely because the model has completed a response.
    schema['properties']['research_view'] = {'const': 'INSUFFICIENT_EVIDENCE'}
    # Facts and IDs are copied by Python, not generated. The model supplies only
    # interpretation; a separate validator still checks every extracted claim.
    schema['properties']['claims'] = {'type': 'array', 'maxItems': 0, 'items': {'type': 'string'}}
    for key in ('overview','thesis'):
        schema['properties'][key] = {'type': 'string', 'maxLength': 400}
    for key in ('unknowns','invalidation_conditions','catalysts','risks','key_disagreements'):
        schema['properties'][key] = {'type': 'array', 'maxItems': 1, 'items': {'type': 'string','maxLength':250}}
    return schema


def attach_extracts(opinion, data):
    if opinion.claims:
        raise ValueError('MODEL_FACT_GENERATION_DENIED')
    if opinion.research_view != 'INSUFFICIENT_EVIDENCE':
        raise ValueError('UNSUPPORTED_DIRECTIONAL_VIEW')
    records = [e for e in data.get('evidence', []) if e.get('excerpt')][:12]
    return Opinion.model_validate({**opinion.model_dump(), 'claims': [
        {'claim_type': 'FACT', 'text': e['excerpt'], 'evidence_ids': [e['id']], 'confidence': 'MEDIUM'} for e in records]})


class LocalLLM:
    def __init__(self, endpoint=None, transport=None, *, bounded_thinking=None):
        endpoint = endpoint or os.environ.get('HQ_LOCAL_LLM_URL', 'http://127.0.0.1:8089')
        u = urlsplit(endpoint)
        if u.scheme != 'http' or u.hostname not in ('127.0.0.1', 'localhost') or u.username or u.password or u.query or u.fragment or u.path not in ('', '/'):
            raise ValueError('LOCAL_LLM_LOOPBACK_ONLY')
        self.endpoint = f'http://127.0.0.1:{u.port or 8089}'
        self.transport = transport
        self.bounded_thinking = (os.environ.get('HQ_LOCAL_LLM_THINKING', 'false').lower() == 'true'
                                 if bounded_thinking is None else bounded_thinking)
        self.status = {'state': 'NO_LOCAL_MODEL', 'runtime': 'llama.cpp', 'model': None, 'endpoint': self.endpoint, 'last_checked_at': None}

    async def probe(self):
        from app.research_contracts import utc
        try:
            async with httpx.AsyncClient(trust_env=False, follow_redirects=False, transport=self.transport, timeout=3) as client:
                r = await client.get(self.endpoint + '/v1/models')
                r.raise_for_status()
                model = r.json()['data'][0]['id']
                self.status.update(state='AVAILABLE', model=str(model)[:200])
        except (httpx.HTTPError, ValueError, KeyError, IndexError):
            self.status.update(state='NO_LOCAL_MODEL', model=None)
        self.status['last_checked_at'] = utc()
        return self.status

    async def chat(self, system, data, max_tokens=700, contract=None, seed=17, timeout_seconds=295):
        if (await self.probe())['state'] != 'AVAILABLE':
            raise NoLocalModel()
        # Conservative budget, no silently truncated evidence or huge external documents.
        wire = DebateWire(contract, data) if contract and contract.__name__ in WIRE_ROLES else None
        prompt = canonical(model_view(wire.data if wire else data))
        if len(prompt) > 20000 or not 1 <= max_tokens <= (1500 if contract else 900):
            raise ValueError('CONTEXT_BUDGET')
        start = time.perf_counter()
        schema = wire.schema if wire else argument_schema(contract, data) if contract else grounded_schema(data)
        payload = {'model': self.status['model'], 'messages': [{'role': 'system', 'content': system + (wire.instructions if wire else '')},
                   {'role': 'user', 'content': 'UNTRUSTED_CONTENT_JSON\n' + prompt}], 'temperature': .2 if contract else 0, 'seed': seed,
                   'max_tokens': max_tokens, 'stream': False,
                   'chat_template_kwargs': {'enable_thinking': self.bounded_thinking},
                   'reasoning_effort': 'low' if self.bounded_thinking else 'none',
                   'response_format': {'type': 'json_object', 'schema': schema}}
        def diagnostics(body=None, content=None, finish_reason=None):
            body = body if isinstance(body, dict) else {}
            metrics = {'runtime': 'llama.cpp', 'model': self.status['model'],
                       'duration_ms': round((time.perf_counter() - start) * 1000),
                       'usage': _numbers(body.get('usage'), ('prompt_tokens', 'completion_tokens', 'total_tokens')),
                       'timings': _numbers(body.get('timings'), ('prompt_n', 'prompt_ms', 'predicted_n',
                           'predicted_ms', 'predicted_per_second', 'cache_n', 'prompt_per_second')),
                       'bounded_thinking': self.bounded_thinking, 'model_prompt_hash': digest(prompt),
                       'model_system_hash': digest(payload['messages'][0]['content']),
                       'claims_origin': 'STRUCTURED_HYPOTHESES' if contract else 'PYTHON_EXACT_EVIDENCE_EXTRACTION'}
            if wire:
                metrics.update(wire.metadata)
            if isinstance(content, str):
                metrics['raw_model_output_hash'] = digest(content)
            if finish_reason is not None:
                metrics['finish_reason'] = finish_reason if finish_reason in ('stop', 'length', 'tool_calls', 'content_filter') else 'UNKNOWN'
            return metrics
        async with httpx.AsyncClient(trust_env=False, follow_redirects=False, transport=self.transport, timeout=timeout_seconds) as client:
            try:
                response = await client.post(self.endpoint + '/v1/chat/completions', json=payload)
            except httpx.TimeoutException:
                error = TimeoutError('LOCAL_LLM_TIMEOUT')
                error.metrics = diagnostics()
                raise error from None
            if response.status_code >= 500:
                try:
                    body = response.json()
                    failure = body.get('error', {}).get('message', '')
                except (ValueError, AttributeError):
                    body = {}
                    failure = ''
                raise LocalLLMFailure('LOCAL_LLM_FORMAT' if isinstance(failure, str) and 'peg-native format' in failure else 'LOCAL_LLM_SERVER_ERROR', diagnostics(body))
            response.raise_for_status()
            if len(response.content) > 64000:
                raise LocalLLMFailure('OUTPUT_BUDGET', diagnostics())
            try:
                body = response.json()
                choice = body['choices'][0]
                content = choice['message']['content']
                if not isinstance(content, str):
                    raise TypeError()
            except (ValueError, KeyError, IndexError, TypeError):
                raise LocalLLMFailure('MALFORMED_LLM_RESPONSE', diagnostics()) from None
        metrics = diagnostics(body, content, choice.get('finish_reason', 'UNKNOWN'))
        if choice.get('finish_reason') != 'stop':
            raise LocalLLMFailure('TRUNCATED_OUTPUT', metrics)
        try:
            parsed = wire.decode(strict_json(content)) if wire else (contract or Opinion).model_validate(json.loads(content))
            if contract is None:
                parsed = attach_extracts(parsed, data)
        except (ValueError, KeyError, TypeError) as exc:
            if isinstance(getattr(exc, 'details', None), dict):
                metrics['contract_violation'] = exc.details
            code = str(exc) if str(exc) in {'WIRE_DUPLICATE_FIELD', 'WIRE_FIELDS_INVALID', 'WIRE_ARRAY_INVALID',
                'WIRE_DUPLICATE_ITEM', 'WIRE_STRING_INVALID', 'WIRE_UNKNOWN_ID_OR_ENUM', 'WIRE_STRING_BUDGET',
                'WIRE_NUMERIC_PROSE', 'MODEL_FACT_GENERATION_DENIED', 'UNSUPPORTED_DIRECTIONAL_VIEW'} else 'MALFORMED_LLM_RESULT'
            raise LocalLLMFailure(code, metrics) from None
        return parsed, metrics
