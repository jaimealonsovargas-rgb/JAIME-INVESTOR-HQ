"""Only loopback llama.cpp; no credentials, proxy, redirect or remote fallback."""
import json
import os
import time
from urllib.parse import urlsplit
import httpx
from app.research_contracts import Opinion, canonical


class NoLocalModel(Exception):
    pass


def grounded_schema(data):
    """Small llama.cpp-compatible schema. Facts are constrained to evidence excerpts;
    free qualitative narrative remains explicitly unverified and validated separately.
    """
    schema = Opinion.model_json_schema()
    schema.pop('$defs', None)
    records = [e for e in data.get('evidence', [])[:16] if e.get('excerpt')]
    schema['properties']['claims'] = {'type': 'array', 'maxItems': min(2, len(records)), 'items': {
        'type': 'object', 'additionalProperties': False,
        'required': ['claim_type', 'text', 'evidence_ids', 'confidence'],
        'properties': {'claim_type': {'const': 'FACT'},
            'text': {'enum': [e['excerpt'] for e in records] or ['NO_DATA']},
            'evidence_ids': {'type': 'array', 'items': {'enum': [e['id'] for e in records] or ['NO_EVIDENCE']}, 'minItems': 1, 'maxItems': 1},
            'confidence': {'enum': ['LOW','MEDIUM','HIGH']}}}}
    for key in ('overview','thesis'):
        schema['properties'][key] = {'type': 'string', 'maxLength': 400}
    for key in ('unknowns','invalidation_conditions','catalysts','risks','key_disagreements'):
        schema['properties'][key] = {'type': 'array', 'maxItems': 2, 'items': {'type': 'string','maxLength':250}}
    return schema


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

    async def chat(self, system, data, max_tokens=700):
        if (await self.probe())['state'] != 'AVAILABLE':
            raise NoLocalModel()
        # Conservative budget, no silently truncated evidence or huge external documents.
        prompt = canonical(data)
        if len(prompt) > 14000 or not 1 <= max_tokens <= 900:
            raise ValueError('CONTEXT_BUDGET')
        start = time.perf_counter()
        payload = {'model': self.status['model'], 'messages': [{'role': 'system', 'content': system},
                   {'role': 'user', 'content': 'UNTRUSTED_CONTENT_JSON\n' + prompt}], 'temperature': 0,
                   'max_tokens': max_tokens, 'stream': False,
                   'chat_template_kwargs': {'enable_thinking': False}, 'reasoning_effort': 'none',
                   'response_format': {'type': 'json_object', 'schema': grounded_schema(data)}}
        async with httpx.AsyncClient(trust_env=False, follow_redirects=False, transport=self.transport, timeout=175) as client:
            response = await client.post(self.endpoint + '/v1/chat/completions', json=payload)
            response.raise_for_status()
            if len(response.content) > 64000:
                raise ValueError('OUTPUT_BUDGET')
            body = response.json()
        choice = body['choices'][0]
        if choice.get('finish_reason') != 'stop':
            raise ValueError('TRUNCATED_OUTPUT')
        parsed = Opinion.model_validate(json.loads(choice['message']['content']))
        return parsed, {'runtime': 'llama.cpp', 'model': self.status['model'], 'duration_ms': round((time.perf_counter()-start)*1000), 'usage': body.get('usage', {})}
