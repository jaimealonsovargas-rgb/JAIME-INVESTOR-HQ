"""One bounded SEC directory request; shared provider quota and no trading transport."""
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy.orm import Session
from app.database import DataQuota
from app.data_catalog import CATALOG
from app.data_http import FetchError, public_dns, retry_seconds
from app.universe_contracts import parse_catalogue
from app.universe_store import UniverseStore
from app.sec_quota import reserve, backoff
from app.storage_budget import admitted

SEC_DIRECTORY = 'https://www.sec.gov/files/company_tickers_exchange.json'


def valid_sec_contact(settings):
    value = settings.secret('sec_contact') or ''
    return '@' in value and len(value) <= 250 and not any(ord(ch) < 32 for ch in value)


class CatalogueHttp:
    def __init__(self, settings, transport=None, resolver=public_dns):
        self.settings, self.transport, self.resolver = settings, transport, resolver

    def fetch_sec(self):
        if not valid_sec_contact(self.settings):
            raise FetchError('CONFIG_REQUIRED')
        # Fixed URL; no caller-controlled path, query, redirect or host.
        headers = {'User-Agent': 'JAIME-Investor-HQ ' + self.settings.secret('sec_contact'), 'Accept': 'application/json'}
        started = time.monotonic()
        try:
            self.resolver('www.sec.gov')
            with httpx.Client(transport=self.transport, trust_env=False, follow_redirects=False, timeout=httpx.Timeout(15, connect=5)) as client:
                with client.stream('GET', SEC_DIRECTORY, headers=headers) as response:
                    if response.status_code != 200:
                        raise FetchError({401: 'AUTH_FAILED', 403: 'RIGHTS_RESTRICTED', 429: 'RATE_LIMITED'}.get(response.status_code, 'ERROR'),
                                         response.status_code, retry_seconds(response.headers.get('Retry-After', '60')))
                    raw, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 16 * 1024 * 1024:
                            raise FetchError('INVALID_PAYLOAD')
                        if time.monotonic() - started > 30:
                            raise FetchError('TIMEOUT')
                        raw.append(chunk)
                    return b''.join(raw)
        except FetchError:
            raise
        except httpx.TimeoutException:
            raise FetchError('TIMEOUT') from None
        except (httpx.HTTPError, OSError):
            raise FetchError('OFFLINE') from None


class UniverseService:
    def __init__(self, data, http=None):
        self.data = data
        self.store = UniverseStore(data.engine)
        self.http = http or CatalogueHttp(data.settings)

    def preparation(self):
        settings = self.data.settings
        sec = self.data.initial(CATALOG['A09']).state
        if not settings.data_public_enabled:
            sec = 'DISABLED'
        elif sec == 'NOT_VERIFIED' and not valid_sec_contact(settings):
            sec = 'CONFIG_REQUIRED'
        if sec == 'NOT_VERIFIED':
            sec = 'READY_TO_FETCH'
        alpaca = all(settings.secret(k) for k in ('alpaca_api_key', 'alpaca_secret_key'))
        return [dict(provider='SEC', state=sec, implemented=True,
                     purpose='Catálogo de emisores, símbolos y mercados',
                     reason='Contacto local configurado; puede descargarse el catálogo.' if sec == 'READY_TO_FETCH' else
                            'Configura SEC_CONTACT en .env y reinicia el backend; respeta las fuentes desactivadas.',
                     docs='https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data'),
                dict(provider='ALPACA', state=('READY_TO_FETCH' if alpaca else 'NO_CREDENTIALS') if settings.alpaca_market_enabled and settings.data_public_enabled and 'B04' not in settings.data_disabled_sources.split(',') else 'DISABLED', implemented=True,
                     purpose='Catálogo de activos, precios y cuenta PAPER',
                     reason='Claves locales presentes; integración por universo y derechos pendientes.' if alpaca else
                            'Faltan ALPACA_API_KEY y ALPACA_SECRET_KEY en .env. No compartas claves en el chat.',
                     docs='https://docs.alpaca.markets/us/reference/get-v2-assets-1')]

    def summary(self):
        return {**self.store.summary(), 'sources': self.preparation()}

    @admitted
    def sync(self, key, provider='SEC'):
        if provider != 'SEC':
            raise ValueError('CATALOGUE_NOT_IMPLEMENTED')
        now = self.data.clock()
        claimed, current = self.store.claim(key, provider, now)
        if not claimed:
            return current
        config = self.preparation()[0]
        if config['state'] != 'READY_TO_FETCH':
            return self.store.finish(key, config['state'], now, reason=config['reason'])
        rights = CATALOG['A09'].rights
        if not all((rights.access_allowed, rights.storage_allowed, rights.display_allowed)):
            return self.store.finish(key, 'RIGHTS_RESTRICTED', now, reason='Derechos SEC no habilitados.')
        with Session(self.data.engine) as s, s.begin():
            s.connection().exec_driver_sql('BEGIN IMMEDIATE')
            blocked = reserve(s, now)
        if blocked:
            return self.store.finish(key, 'RATE_LIMITED', now, reason='Presupuesto SEC compartido: una consulta/segundo y hasta 60/minuto.', next_allowed_at=blocked)
        try:
            raw = self.http.fetch_sec()
            body = json.loads(raw)
            rows = parse_catalogue(provider, body)
            return self.store.apply_snapshot(key, provider, rows, SEC_DIRECTORY, hashlib.sha256(raw).hexdigest(), self.data.clock())
        except FetchError as error:
            if error.state == 'RATE_LIMITED':
                with Session(self.data.engine) as s, s.begin():
                    backoff(s, self.data.clock(), error.retry_after)
            return self.store.finish(key, error.state, self.data.clock(), reason='La fuente no pudo actualizarse; se conserva el catálogo anterior.', http_status=error.status)
        except (ValueError, KeyError, TypeError, IndexError):
            return self.store.finish(key, 'INVALID_PAYLOAD', self.data.clock(), reason='Respuesta rechazada por inconsistencias; catálogo anterior conservado.')
