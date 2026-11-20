"""Review a bounded batch of issuers against actual annual SEC statements."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.company_model import TEMPLATE
from app.company_service import CompanyService
from app.config import Settings
from app.data_http import FetchError
from app.data_identity import fingerprint
from app.data_service import DataService
from app.database import create_db_engine
from app.filing_archive import acquire
from app.sec_normalize import annual_view, cik_text
from app.sec_service import SecService


def run_batch(service,ciks):
    ciks = list(dict.fromkeys(cik_text(cik) for cik in ciks))
    if not 1<=len(ciks)<=25:
        raise ValueError('El lote admite entre 1 y 25 emisores.')
    results = []
    for cik in ciks:
        try:
            service.readable()
            with service.engine.connect() as c:
                facts,source = service.source(c,cik,service.data.clock())
            annual = annual_view(facts)
            if not annual or not annual.get('currency'):
                raise ValueError('NO_COMPARABLE_ANNUAL_ACCOUNTS')
            receipt = acquire(service.sec,cik,annual)
            key = 'filing-batch-'+fingerprint([TEMPLATE,cik,source['snapshot_id'],receipt])
            m = service.build(cik,key,snapshot_id=source['snapshot_id'])
            p = m['payload']
            if 'filing_statement' not in p:
                raise ValueError('FILING_RECEIPT_UNAVAILABLE')
            results.append(dict(cik=cik,name=source['name'],id=m['id'],version=m['version'],
                period=annual['end'],accession=annual['accession'],state=p['review']['state'],
                reason=p['update']['reason'],receipt=receipt,checks=p['review']['checks'],
                coverage=p['annual_filing_coverage']))
        except (FetchError,PermissionError,ValueError) as error:
            results.append(dict(cik=cik,error=error.state if isinstance(error,FetchError) else str(error)))
    return results


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Contrasta un lote de modelos locales con sus estados anuales SEC.')
    parser.add_argument('ciks',nargs='+',help='Identificadores SEC de los emisores con cuentas locales')
    args = parser.parse_args()
    data = DataService(create_db_engine(Settings().database_url))
    rows = run_batch(CompanyService(SecService(data)),args.ciks)
    print(json.dumps(rows,indent=2,ensure_ascii=True))
    sys.exit(int(any('error' in row for row in rows)))
