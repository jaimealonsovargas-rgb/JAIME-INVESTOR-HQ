"""Fixed SEC JSON/XML endpoints and a private content-addressed archive."""
import gzip
import hashlib
import os
import re
import time
from pathlib import Path
from uuid import uuid4
import httpx
from app.data_http import FetchError, public_dns, retry_seconds
from app.universe_service import valid_sec_contact
from app.sec_normalize import accession, cik_text, document_url

MAX_BYTES = 32 * 1024 * 1024


def source_url(cik, kind):
    if not re.fullmatch(r'\d{10}', cik) or int(cik) == 0:
        raise ValueError('INVALID_CIK')
    if kind == 'submissions':
        return f'https://data.sec.gov/submissions/CIK{cik}.json'
    if kind == 'companyfacts':
        return f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'
    raise ValueError('INVALID_ENDPOINT')


class SecHttp:
    def __init__(self, settings, transport=None, resolver=public_dns):
        self.settings, self.transport, self.resolver = settings, transport, resolver

    def fetch(self, cik, kind):
        url = source_url(cik, kind)
        return self._get(url, 'data.sec.gov', 'application/json')

    def fetch_statement(self, cik, accn, primary, kind):
        url = statement_url(cik, accn, primary, kind)
        return self._get(url, 'www.sec.gov', 'application/xml, text/xml')

    def _get(self, url, host, accept):
        if not valid_sec_contact(self.settings):
            raise FetchError('CONFIG_REQUIRED')
        headers = {'User-Agent': 'JAIME-Investor-HQ ' + self.settings.secret('sec_contact'), 'Accept': accept}
        started = time.monotonic()
        try:
            self.resolver(host)
            with httpx.Client(transport=self.transport, trust_env=False, follow_redirects=False,
                              timeout=httpx.Timeout(20, connect=5)) as client:
                with client.stream('GET', url, headers=headers) as response:
                    if response.status_code != 200:
                        code = {401: 'AUTH_FAILED', 403: 'RIGHTS_RESTRICTED', 404: 'NOT_FOUND', 429: 'RATE_LIMITED'}.get(response.status_code, 'ERROR')
                        raise FetchError(code, response.status_code, retry_seconds(response.headers.get('Retry-After', '60')))
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise FetchError('INVALID_PAYLOAD')
                        if time.monotonic() - started > 45:
                            raise FetchError('TIMEOUT')
                        chunks.append(chunk)
                    return b''.join(chunks)
        except FetchError:
            raise
        except httpx.TimeoutException:
            raise FetchError('TIMEOUT') from None
        except (httpx.HTTPError, OSError):
            raise FetchError('OFFLINE') from None


def statement_url(cik, accn, primary, kind):
    suffixes = {'calculation':'_cal.xml', 'schema':'.xsd', 'instance':'_htm.xml'}
    if kind not in suffixes or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}\.htm', primary):
        raise ValueError('UNSUPPORTED_STATEMENT_DOCUMENT')
    return document_url(cik_text(cik), accession(accn), primary[:-4] + suffixes[kind])


def archive_raw(root: Path, raw: bytes, *, extension='.json.gz'):
    digest = hashlib.sha256(raw).hexdigest()
    root.mkdir(parents=True, exist_ok=True)
    target = root / (digest + extension)
    if not target.exists():
        temporary = root / (digest + '.' + str(uuid4()) + '.tmp')
        try:
            temporary.write_bytes(gzip.compress(raw, compresslevel=3, mtime=0))
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return digest
