"""Private receipts bind SEC calculation and instance bytes to one identified filing."""
from datetime import datetime
import gzip
import hashlib
import json
import os
import re
import time
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.data_http import FetchError
from app.filing_reconciliation import extract_equations
from app.sec_http import MAX_BYTES, archive_raw, statement_url
from app.sec_normalize import accession, cik_text
from app.sec_quota import reserve, backoff
from app.sec_store import FILINGS


def receipt_path(sec,cik,accn):
    return sec.raw_root.parent/'statements'/cik_text(cik)/(accession(accn)+'.json')


def fetch_one(sec,cik,accn,primary,kind):
    for _ in range(6):
        now = sec.data.clock()
        with Session(sec.data.engine) as session,session.begin():
            session.connection().exec_driver_sql('BEGIN IMMEDIATE')
            until = reserve(session,now)
        if not until:
            break
        delay = (datetime.fromisoformat(until)-now).total_seconds()
        if delay>2:
            raise FetchError('RATE_LIMITED')
        time.sleep(max(0.01,delay))
    else:
        raise FetchError('RATE_LIMITED')
    try:
        raw = sec.http.fetch_statement(cik,accn,primary,kind)
    except FetchError as error:
        if error.state=='RATE_LIMITED':
            with Session(sec.data.engine) as session,session.begin():
                session.connection().exec_driver_sql('BEGIN IMMEDIATE')
                backoff(session,sec.data.clock(),error.retry_after)
        raise
    return raw, dict(kind=kind,url=statement_url(cik,accn,primary,kind),
                     sha256=hashlib.sha256(raw).hexdigest())


def acquire(sec,cik,annual):
    # A saved receipt is a read; a missing one reserves both originals before HTTP.
    path = receipt_path(sec,cik,annual['accession'])
    if path.exists():
        return _acquire(sec,cik,annual)
    with sec.data.storage.admission():
        return _acquire(sec,cik,annual)


def _acquire(sec,cik,annual):
    if sec.access()!='READY':
        raise PermissionError('SOURCE_UNAVAILABLE')
    accn = annual['accession']
    path = receipt_path(sec,cik,accn)
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    with sec.data.engine.connect() as c:
        snap = sec.store._snapshot(c,cik,'submissions',sec.data.clock())
        doc = c.scalar(select(FILINGS.c.payload).where(FILINGS.c.snapshot_id==snap['id'],
                       FILINGS.c.accession==accn)) if snap else None
    if not doc or (doc['filed'],doc['report_date'],doc['form'])!=(annual['filed'],annual['end'],annual['form']):
        raise ValueError('FILING_IDENTITY_UNVERIFIED')
    primary = doc['primary_document']
    try:
        calc,calc_ref = fetch_one(sec,cik,accn,primary,'calculation')
    except FetchError as error:
        if error.state!='NOT_FOUND':
            raise
        calc,calc_ref = fetch_one(sec,cik,accn,primary,'schema')
    instance,instance_ref = fetch_one(sec,cik,accn,primary,'instance')
    # Validate before publishing a receipt. No URLs embedded in XML are fetched.
    extract_equations(calc,instance,dict(entity_id=cik,annual=annual))
    folder = path.parent.parent/'raw'
    for data in (calc,instance):
        archive_raw(folder,data,extension='.xml.gz')
    manifest = dict(cik=cik,accession=accn,primary=primary,received_at=sec.data.clock().isoformat(),
                    calculation=calc_ref,instance=instance_ref)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix('.'+uuid4().hex+'.tmp')
    try:
        temp.write_text(json.dumps(manifest),encoding='utf-8')
        try:
            os.link(temp,path)  # publish once, including the first receipt time
        except FileExistsError:
            pass
    finally:
        temp.unlink(missing_ok=True)
    return json.loads(path.read_text(encoding='utf-8'))


def read_filing(sec,model,cutoff):
    cik,accn = model['entity_id'],model['annual']['accession']
    path = receipt_path(sec,cik,accn)
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding='utf-8'))
    if (record['cik'],record['accession'])!=(cik,accn):
        raise ValueError('FILING_IDENTITY_UNVERIFIED')
    if datetime.fromisoformat(record['received_at'])>cutoff:
        return None
    data = []
    for key,kinds in [('calculation',('calculation','schema')),('instance',('instance',))]:
        ref = record[key]
        if (ref['kind'] not in kinds or not re.fullmatch(r'[a-f0-9]{64}',ref['sha256'])
                or ref['url']!=statement_url(cik,accn,record['primary'],ref['kind'])):
            raise ValueError('INVALID_FILING_RECEIPT')
        try:
            with gzip.open(path.parent.parent/'raw'/(ref['sha256']+'.xml.gz'),'rb') as stream:
                raw = stream.read(MAX_BYTES+1)
        except (EOFError,OSError):
            raise ValueError('ORIGINAL_UNAVAILABLE') from None
        if len(raw)>MAX_BYTES or hashlib.sha256(raw).hexdigest()!=ref['sha256']:
            raise ValueError('ORIGINAL_INTEGRITY_FAILED')
        data.append(raw)
    return dict(receipt=record,equations=extract_equations(*data,model))
