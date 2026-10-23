"""Two tiny localhost canaries: verifies actual grammar enforcement, not finance."""
import json
import argparse
from pathlib import Path
import sys
import time
import httpx


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('output/p4-debate-repair/schema-canary.json'))
    parser.add_argument('--length',action='store_true')
    args=parser.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
    from app.research_wire import _text
    with httpx.Client(trust_env=False, follow_redirects=False, timeout=30) as client:
        status = client.get('http://127.0.0.1:8000/api/agents/status').raise_for_status().json()
        if status['active_jobs'] or status['queue']:
            raise SystemExit('ACTIVE_HQ_JOBS')
        model = client.get('http://127.0.0.1:8089/v1/models').raise_for_status().json()['data'][0]['id']
        schema = {'type':'object','properties':{'gate':{'const':'HQ_SCHEMA_OK'}},
                  'required':['gate'],'additionalProperties':False}
        if args.length:
            schema={'type':'object','properties':{'text':_text(12,25)},'required':['text'],'additionalProperties':False}
        reports = []
        for variant in (('json_object',) if args.length else ('json_object', 'json_schema')):
            fmt = ({'type':'json_object','schema':schema} if variant == 'json_object' else
                   {'type':'json_schema','json_schema':{'name':'hq_canary','strict':True,'schema':schema}})
            start = time.perf_counter()
            response = client.post('http://127.0.0.1:8089/v1/chat/completions', json={
                'model':model, 'messages':[{'role':'system','content':'Escribe JSON válido del esquema. Texto español.'},
                    {'role':'user','content':'Escribe ok en el campo text.' if args.length else 'Contesta con la palabra hola, sin JSON.'}],
                'max_tokens':32,'temperature':0,'seed':17,'stream':False,
                'chat_template_kwargs':{'enable_thinking':False},'reasoning_effort':'none',
                'response_format':fmt})
            body = response.json()
            record = {'classification':'TEST_ONLY_SCHEMA_CANARY','model':model,'variant':variant,
                      'http':response.status_code,'elapsed_seconds':round(time.perf_counter()-start,3),
                      'usage':body.get('usage'),'timings':body.get('timings'),'pass':False}
            if response.status_code == 200:
                choice=body['choices'][0]
                record.update(content=choice['message'].get('content'),finish_reason=choice.get('finish_reason'))
                try:
                    decoded=json.loads(record['content'])
                    record['pass']=(12<=len(decoded['text'])<=25 if args.length else decoded=={'gate':'HQ_SCHEMA_OK'}) and record['finish_reason']=='stop'
                except (ValueError,TypeError): pass
            reports.append(record)
            print(json.dumps(record,ensure_ascii=True),flush=True)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(reports,indent=2),encoding='utf-8')
        if not all(r['pass'] for r in reports):raise SystemExit(1)


if __name__=='__main__': main()
