"""Only loopback llama.cpp; no credentials, proxy, redirect or remote fallback."""
import json
import os
import time
from urllib.parse import urlsplit
import httpx
from app.research_contracts import Opinion, canonical, digest


class NoLocalModel(Exception):
    pass


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
    def __init__(self, endpoint=None, transport=None):
        endpoint = endpoint or os.environ.get('HQ_LOCAL_LLM_URL', 'http://127.0.0.1:8089')
        u = urlsplit(endpoint)
        if u.scheme != 'http' or u.hostname not in ('127.0.0.1', 'localhost') or u.username or u.password or u.query or u.fragment or u.path not in ('', '/'):
            raise ValueError('LOCAL_LLM_LOOPBACK_ONLY')
        self.endpoint = f'http://127.0.0.1:{u.port or 8089}'
        self.transport = transport
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

    async def chat(self, system, data, max_tokens=700, contract=None, seed=17):
        if (await self.probe())['state'] != 'AVAILABLE':
            raise NoLocalModel()
        # Conservative budget, no silently truncated evidence or huge external documents.
        def model_view(value):
            if isinstance(value, dict):
                return {k: model_view(v) for k, v in value.items() if k != 'evidence_id'}
            if isinstance(value, list):
                return [model_view(v) for v in value]
            return value
        prompt = canonical(model_view(data))
        if len(prompt) > 20000 or not 1 <= max_tokens <= (1500 if contract else 900):
            raise ValueError('CONTEXT_BUDGET')
        start = time.perf_counter()
        payload = {'model': self.status['model'], 'messages': [{'role': 'system', 'content': system},
                   {'role': 'user', 'content': 'UNTRUSTED_CONTENT_JSON\n' + prompt}], 'temperature': .2 if contract else 0, 'seed': seed,
                   'max_tokens': max_tokens, 'stream': False,
                   'chat_template_kwargs': {'enable_thinking': False}, 'reasoning_effort': 'none',
                   'response_format': {'type': 'json_object', 'schema': contract.model_json_schema() if contract else grounded_schema(data)}}
        async with httpx.AsyncClient(trust_env=False, follow_redirects=False, transport=self.transport, timeout=295) as client:
            try:
                response = await client.post(self.endpoint + '/v1/chat/completions', json=payload)
            except httpx.TimeoutException:
                raise TimeoutError('LOCAL_LLM_TIMEOUT') from None
            response.raise_for_status()
            if len(response.content) > 64000:
                raise ValueError('OUTPUT_BUDGET')
            body = response.json()
        choice = body['choices'][0]
        if choice.get('finish_reason') != 'stop':
            raise ValueError('TRUNCATED_OUTPUT')
        parsed = (contract or Opinion).model_validate(json.loads(choice['message']['content']))
        if contract is None:
            parsed = attach_extracts(parsed, data)
        return parsed, {'runtime': 'llama.cpp', 'model': self.status['model'], 'duration_ms': round((time.perf_counter()-start)*1000), 'usage': body.get('usage', {}), 'model_prompt_hash': digest(prompt), 'raw_model_output_hash': digest(choice['message']['content']), 'claims_origin': 'STRUCTURED_HYPOTHESES' if contract else 'PYTHON_EXACT_EVIDENCE_EXTRACTION'}
