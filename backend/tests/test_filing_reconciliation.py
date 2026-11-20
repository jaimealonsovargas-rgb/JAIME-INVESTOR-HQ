import hashlib
import json
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
import pytest
from app.filing_archive import read_filing,receipt_path
from app.filing_reconciliation import BALANCE, extract_equations, review_equation, xml_document
from app.sec_http import archive_raw, statement_url
from test_company_models import accounting,model


def example():
    m=model(accounting())
    annual=m['annual']
    ns='http://www.xbrl.org/2003/'
    xl='http://www.w3.org/1999/xlink'
    header=f'<linkbase xmlns="{ns}linkbase" xmlns:x="{xl}">'
    relation='<calculationLink x:role="https://example.org/BalanceSheets">'
    terms=['Liabilities','StockholdersEquity','CommitmentsAndContingencies']
    for name in [BALANCE,*terms]:
        relation+=f'<loc x:label="{name}" x:href="https://xbrl.fasb.org/us-gaap/2025/elts/us-gaap-2025.xsd#us-gaap_{name}"/>'
    for name in terms:
        relation+=f'<calculationArc x:from="{BALANCE}" x:to="{name}" weight="1.00" x:arcrole="https://xbrl.org/2023/arcrole/summation-item"/>'
    calc=(header+relation+'</calculationLink></linkbase>').encode()
    raw=f'''<xbrl xmlns="{ns}instance" xmlns:g="http://fasb.org/us-gaap/2025" xmlns:iso="{ns}iso4217" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <unit id="u"><measure>iso:USD</measure></unit><context id="end"><entity><identifier scheme="http://www.sec.gov/CIK">{m['entity_id']}</identifier></entity>
    <period><instant>{annual['end']}</instant></period></context>
    <g:LiabilitiesAndStockholdersEquity contextRef="end" unitRef="u">100</g:LiabilitiesAndStockholdersEquity>
    <g:Liabilities contextRef="end" unitRef="u">60</g:Liabilities>
    <g:StockholdersEquity contextRef="end" unitRef="u">40</g:StockholdersEquity>
    <g:CommitmentsAndContingencies contextRef="end" unitRef="u" xsi:nil="true"/></xbrl>'''.encode()
    return m,calc,raw


def test_filed_equation_cross_checks_two_independent_amounts():
    m,calc,raw=example()
    eq=extract_equations(calc,raw,m)['balance']
    assert all(t['context']=='end' for t in eq['terms'])
    metrics={r['metric']:r for r in m['annual']['metrics']}
    assets=metrics['assets']['fact']
    assets['value']='100'
    metrics['balance_total']['fact']={**assets,'value':'100','concept':BALANCE}
    result=review_equation(m,'balance',eq)
    assert result['state']=='PASS' and result['residual']==result['source_residual']==result['cross_residual']=='0'
    assets['value']='99.999'
    assert review_equation(m,'balance',eq)['cross_residual']=='-0.001'
    eq['terms'][1]['value']='61'
    assert review_equation(m,'balance',eq)['state']=='FAIL'


@pytest.mark.parametrize('before,after',[
    (b'iso:USD',b'iso:EUR'),(b'2003/iso4217',b'2003/untrusted'),
    (b'</entity>',b'<segment/></entity>'),(b'</period>',b'</period><scenario/>'),
    (b'g:StockholdersEquity',b'g:AnotherConcept'),(b'xsi:nil="true"',b''),
])
def test_missing_or_incompatible_facts_cannot_pass(before,after):
    m,calc,raw=example()
    assert 'blocked' in extract_equations(calc,raw.replace(before,after),m)['balance']


def test_ambiguous_conflicting_and_unsafe_relationships():
    m,calc,raw=example()
    pair=calc[calc.index(b'<calculationLink'):calc.index(b'</linkbase>')]
    assert 'blocked' in extract_equations(calc.replace(b'</linkbase>',pair+b'</linkbase>'),raw,m)['balance']
    assert 'blocked' in extract_equations(calc.replace(b'weight="1.00"',b'weight="2"'),raw,m)['balance']
    extra=b'<g:Liabilities contextRef="end" unitRef="u">70</g:Liabilities>'
    assert 'blocked' in extract_equations(calc,raw.replace(b'</xbrl>',extra+b'</xbrl>'),m)['balance']
    with pytest.raises(ValueError,match='UNSAFE'):
        xml_document(b'<!DOCTYPE x><x/>')


def test_receipt_applies_only_from_local_acquisition_and_checks_both_hashes(tmp_path):
    m,calc,raw=example()
    sec=SimpleNamespace(raw_root=tmp_path/'raw')
    cik,acc=m['entity_id'],m['annual']['accession']
    path=receipt_path(sec,cik,acc); path.parent.mkdir(parents=True)
    now=datetime.now(timezone.utc)
    receipt=dict(cik=cik,accession=acc,primary='issuer.htm',received_at=now.isoformat())
    folder=path.parent.parent/'raw'
    for key,content in [('calculation',calc),('instance',raw)]:
        digest=archive_raw(folder,content,extension='.xml.gz')
        receipt[key]=dict(kind=key,sha256=digest,url=statement_url(cik,acc,'issuer.htm',key))
    path.write_text(json.dumps(receipt))
    assert read_filing(sec,m,now-timedelta(seconds=1)) is None
    assert read_filing(sec,m,now)['equations']['balance']['total']['value']=='100'
    archive=(folder/(hashlib.sha256(raw).hexdigest()+'.xml.gz'))
    archive.write_bytes((folder/(hashlib.sha256(calc).hexdigest()+'.xml.gz')).read_bytes())
    with pytest.raises(ValueError,match='INTEGRITY'):
        read_filing(sec,m,now)


@pytest.mark.parametrize('primary',['../x.htm','https://other/x.htm','x?y.htm','x%2ft.htm'])
def test_statement_fetch_uses_only_fixed_sec_archive_documents(primary):
    with pytest.raises(ValueError):
        statement_url('1','0000000001-26-000001',primary,'instance')
