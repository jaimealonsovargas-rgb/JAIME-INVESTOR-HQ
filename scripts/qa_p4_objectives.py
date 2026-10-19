"""Actual localhost objective acceptance; no synthetic data and no financial writes."""
import json
import time
from pathlib import Path
import httpx

out = Path('output/p4-advanced/objectives-real.json')
with httpx.Client(base_url='http://127.0.0.1:8000', trust_env=False, timeout=30) as client:
    before = client.get('/api/portfolio/master/summary').json()
    instruments = client.get('/api/instruments').json()
    instrument = next(i for i in instruments if i['symbol']=='EXR.D.USD.EUR.SP00.A')
    cases = []
    for goal, question in [('macro_reference','Alcance y limitaciones de la referencia BCE; informe informativo.'),
                           ('investable_thesis','Evaluar una tesis de inversión con evidencia del instrumento, absteniéndose si solo hay referencias.')]:
        headers = {'X-HQ-Research':'1','Idempotency-Key':'advanced-objective-'+goal}
        response = client.post('/api/research/cases', headers=headers, json={'instrument_id':instrument['id'],'question':question,'research_goal':goal})
        response.raise_for_status()
        case = response.json()
        headers['Idempotency-Key'] = 'advanced-run-'+goal
        run = client.post('/api/research/cases/'+case['id']+'/run', headers=headers, json={'priority':10,'refresh_public':goal=='macro_reference'})
        run.raise_for_status()
        cases.append(case)
    for _ in range(90):
        dossiers = [client.get('/api/research/cases/'+case['id']).json() for case in cases]
        if all(d['status'] not in ('IDLE','RUNNING') for d in dossiers): break
        time.sleep(2)
    after = client.get('/api/portfolio/master/summary').json()
    orders = client.post('/api/orders',json={})
    result = {'classification':'REAL_LOCAL_HTTP','before':before,'after':after,'orders_status':orders.status_code,'dossiers':dossiers}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    assert before['ledger_hash']==after['ledger_hash'] and orders.status_code==403
    assert dossiers[0]['quality']['state']=='NOT_APPLICABLE' and len(dossiers[0]['jobs'])==4
    assert dossiers[1]['quality']['state']=='ABSTAINED'
    assert all(d['status']=='COMPLETE' for d in dossiers)
    print(json.dumps({'cases':[{'id':d['id'],'jobs':len(d['jobs']),'evidence':len(d['evidence']),'quality':d['quality']} for d in dossiers], 'orders_status':orders.status_code,'master_hash':after['ledger_hash']}))
