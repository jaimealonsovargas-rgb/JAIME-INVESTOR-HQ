"""Closed trust anchors. Caller assertions never establish market-data rights."""
from .admission_contracts import fingerprint, instant

REGISTRY_VERSION='admission-trust-v2'
# Additions require code review; neither paths nor CLI switches can extend trust.
REAL_EVIDENCE_REGISTRY={}
MAX_RECORDS=32


def trusted_registry():
    from .b32_review import reviewed_records
    return {**REAL_EVIDENCE_REGISTRY, **reviewed_records()}


def registered_evidence(candidate):
    """Select only reviewed server entries, never import caller-provided authority."""
    if candidate['domain'] != 'MARKET_DATA':
        return None
    subject = fingerprint(candidate)
    records = [r for _, r in sorted(trusted_registry().items())
               if isinstance(r, dict) and r.get('subject_hash') == subject]
    return {'version':'admission-evidence-v1', 'records':records} if records else None


def bounded_json(value, depth=0, budget=None):
    if budget is None: budget=[100000]
    budget[0]-=1
    if depth>12 or budget[0]<0: raise ValueError('EVIDENCE_BUDGET')
    if value is None or isinstance(value,bool): return
    if isinstance(value,str):
        if len(value)>512: raise ValueError('EVIDENCE_STRING_BUDGET')
        return
    if isinstance(value,int) and not isinstance(value,bool) and abs(value)<10**20: return
    if isinstance(value,list) and len(value)<=5000:
        for item in value: bounded_json(item,depth+1,budget)
        return
    if isinstance(value,dict) and len(value)<=64:
        for k,v in value.items():
            if not isinstance(k,str) or len(k)>128: raise ValueError('EVIDENCE_KEY')
            bounded_json(v,depth+1,budget)
        return
    raise ValueError('EVIDENCE_TYPE')


def evidence_record(kind, subject_hash, payload, published_at):
    body={'id':'TEST:'+kind, 'kind':kind, 'authority':'TEST_FIXTURE_V1',
          'subject_hash':subject_hash,'published_at':instant(published_at),'payload':payload}
    return dict(body,hash=fingerprint(body))


def verified_records(candidate, evidence):
    records={}
    errors=[]
    registry=trusted_registry()
    if evidence is None:
        return records,['EVIDENCE_MISSING']
    if not isinstance(evidence,dict) or set(evidence)!= {'version','records'} or evidence['version']!='admission-evidence-v1' or not isinstance(evidence['records'],list) or len(evidence['records'])>MAX_RECORDS:
        return records,['EVIDENCE_CONTRACT_INVALID']
    subject=fingerprint(candidate)
    synthetic=candidate['domain']==candidate['provider']=='SYNTHETIC_TEST'
    for record in evidence['records']:
        try:
            if not isinstance(record,dict) or set(record)!={'id','kind','authority','subject_hash','published_at','payload','hash'}:
                raise ValueError()
            # Bound all nested evidence before hashing or inspecting it.
            bounded_json(record)
            body={k:v for k,v in record.items() if k!='hash'}
            if record['hash']!=fingerprint(body) or record['subject_hash']!=subject:
                errors.append('EVIDENCE_HASH_OR_SUBJECT_MISMATCH'); continue
            if instant(record['published_at'])>candidate['cutoff']:
                errors.append('EVIDENCE_AFTER_CUTOFF'); continue
            fixture=(synthetic and record['authority']=='TEST_FIXTURE_V1' and record['id']=='TEST:'+record['kind'])
            trusted=registry.get(record['hash'])==record
            if not (fixture or trusted):
                errors.append('UNTRUSTED_EVIDENCE'); continue
            if record['kind'] in records:
                errors.append('DUPLICATE_EVIDENCE_KIND'); continue
            if not isinstance(record['payload'],dict):
                raise ValueError()
            records[record['kind']]=record
        except (ValueError,TypeError,KeyError,OverflowError,RecursionError):
            errors.append('EVIDENCE_CONTRACT_INVALID')
    return records,sorted(set(errors))
