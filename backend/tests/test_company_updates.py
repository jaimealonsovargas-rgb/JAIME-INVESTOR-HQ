import json
from sqlalchemy import select, update
from app.company_updates import EVENTS, process_update
from test_company_models import imported, accounting
from test_sec_financials import service, CIK, drain
from app.sec_store import FILINGS
from app.sec_normalize import filed_bound


def test_newer_annual_disclosure_marks_local_model_pending_without_future_leak(service):
    models=imported(service)
    original=models.build(CIK,'coverage-original')
    annual=original['payload']['annual']
    with models.engine.begin() as c:
        row=c.execute(select(FILINGS)).mappings().first()
        newer={**row['payload'],'accession':'0000000001-26-000099','filed':'2026-09-20',
               'published_bound':filed_bound('2026-09-20')}
        c.execute(FILINGS.insert().values(snapshot_id=row['snapshot_id'],accession=newer['accession'],
                  filed=newer['filed'],form='10-K',payload=newer))
    pending=models.build(CIK,'coverage-pending')
    assert pending['payload']['annual_filing_coverage']['state']=='BLOCKED'
    assert pending['payload']['review']['state']=='PARTIAL'
    with models.engine.begin() as c:
        c.execute(FILINGS.update().where(FILINGS.c.accession==newer['accession']).values(
            payload={**newer,'published_bound':'2027-01-01T05:00:00+00:00'}))
    with models.engine.connect() as c:
        assert models.filing_coverage(c,CIK,annual,service.data.clock())['state']=='PASS'


def test_retry_of_previous_template_keeps_original_result(service,monkeypatch):
    import app.company_model as model_module
    import app.company_service as service_module
    models=imported(service)
    current=model_module.TEMPLATE
    monkeypatch.setattr(model_module,'TEMPLATE','test-previous-template')
    monkeypatch.setattr(service_module,'TEMPLATE','test-previous-template')
    old=models.build(CIK,'stable-request-before-upgrade')
    monkeypatch.setattr(model_module,'TEMPLATE',current)
    monkeypatch.setattr(service_module,'TEMPLATE',current)
    assert models.build(CIK,'stable-request-before-upgrade')==old
    newer=models.build(CIK,'new-request-after-upgrade')
    assert newer['id']!=old['id']
    assert models.get(CIK,old['id'])==old


def test_changed_sec_payload_updates_once_and_recovers_after_completion_gap(service):
    models=imported(service); first=models.build(CIK,'before-update')
    body=accounting(); body['facts']['us-gaap']['NetIncomeLoss']['units']['USD'][0]['val']=22
    old_fetch=service.http.fetch
    service.http.fetch=lambda cik,kind:json.dumps(body).encode() if kind=='companyfacts' else old_fetch(cik,kind)
    service.enqueue('changed-source-job',[CIK]); drain(service)
    with models.engine.connect() as c:
        event=dict(c.execute(select(EVENTS)).mappings().one())
    assert event['state']=='SUCCEEDED'
    new=models.get(CIK,event['model_id'])
    assert new['version']==2 and new['previous_id']==first['id']
    assert new['payload']['source']['snapshot_id']==event['snapshot_id']
    assert models.get(CIK,first['id'])==first
    # Simulate crash after committed build, before acknowledgement.
    with models.engine.begin() as c:
        c.execute(update(EVENTS).values(state='PENDING', model_id=None))
    assert process_update(service)
    assert models.versions(CIK)['total']==2
    service.enqueue('same-source-job',[CIK]); drain(service)
    with models.engine.connect() as c:
        assert len(c.execute(select(EVENTS)).all())==1


def test_older_report_cannot_replace_current_annual(service):
    models=imported(service); first=models.build(CIK,'before-older-report')
    body=accounting()
    for tag in body['facts']['us-gaap'].values():
        for row in tag['units']['USD']:
            if row['end']=='2026-06-30':
                row['end']='2024-06-30'
                if 'start' in row:row['start']='2023-07-01'
    old_fetch=service.http.fetch
    service.http.fetch=lambda cik,kind:json.dumps(body).encode() if kind=='companyfacts' else old_fetch(cik,kind)
    service.enqueue('older-source-job',[CIK]); drain(service)
    with models.engine.connect() as c:
        event=c.execute(select(EVENTS)).mappings().one()
    assert event['state']=='BLOCKED' and event['reason']=='OLDER_FINANCIAL_REPORT'
    assert models.versions(CIK)['total']==1 and models.get(CIK,first['id'])==first
