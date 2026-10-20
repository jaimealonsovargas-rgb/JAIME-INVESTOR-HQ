"""Transporte externo P2. No tiene capacidad de acceder a cuentas ni operar."""
import ipaddress
import json
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from math import ceil
from urllib.parse import urlsplit
import httpx
from app.data_catalog import CATALOG, Source
from app.data_config import DataSettings
from app.data_windows import request_window

MAX_BYTES = 8 * 1024 * 1024
READ_POSTS = {('api.openfigi.com','/v3/mapping'),('api.bls.gov','/publicAPI/v2/timeseries/data/')}

def retry_seconds(value: str, now=None):
    if value.isdigit():return min(86400,int(value))
    try:
        date=parsedate_to_datetime(value)
        if date.tzinfo is None:return 60
        return min(86400,max(0,ceil((date-(now or datetime.now(timezone.utc))).total_seconds())))
    except (ValueError,TypeError,OverflowError):return 60

@dataclass
class FetchError(Exception):
    state: str
    status: int | None = None
    retry_after: int = 0

def validate_request(source: Source, method: str, url: str, payload=None):
    registered=CATALOG.get(source.id)
    target=urlsplit(url)
    if registered != source or url != source.url or target.scheme != 'https' or target.username or target.password or target.port or target.query or target.fragment:
        raise FetchError('CONFIG_REQUIRED')
    if method != source.method or method not in ('GET','POST'):
        raise FetchError('CONFIG_REQUIRED')
    if method == 'GET' and payload is not None:
        raise FetchError('CONFIG_REQUIRED')
    if method == 'POST':
        if (target.hostname,target.path) not in READ_POSTS:
            raise FetchError('CONFIG_REQUIRED')
        if target.hostname=='api.openfigi.com':
            if not isinstance(payload,list) or not 1 <= len(payload) <= 10 or any(not isinstance(job,dict) or set(job)-{'idType','idValue','exchCode','currency'} or job.get('idType') not in {'ID_ISIN','ID_CUSIP','ID_BB_GLOBAL','TICKER'} or not isinstance(job.get('idValue'),str) or not 1<=len(job['idValue'])<=120 for job in payload):
                raise FetchError('CONFIG_REQUIRED')
        else:
            if not isinstance(payload,dict) or set(payload)-{'seriesid','startyear','endyear','registrationkey'} or not isinstance(payload.get('seriesid'),list) or not 1<=len(payload['seriesid'])<=10 or any(not isinstance(v,str) or not v.isalnum() or len(v)>40 for v in payload['seriesid']):raise FetchError('CONFIG_REQUIRED')
            start,end=payload.get('startyear',''),payload.get('endyear','')
            if any(not isinstance(v,str) or len(v)!=4 or not v.isdigit() for v in (start,end)) or not 1900<=int(start)<=int(end)<=2100 or int(end)-int(start)>1:raise FetchError('CONFIG_REQUIRED')
        if len(json.dumps(payload))>8192:
            raise FetchError('CONFIG_REQUIRED')

def public_dns(host: str):
    addresses=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(entry[4][0]).is_global for entry in addresses):
        raise FetchError('CONFIG_REQUIRED')

class SafeDataHttp:
    def __init__(self, settings: DataSettings, transport=None, resolver=public_dns):
        self.settings=settings
        self.transport=transport
        self.resolver=resolver
        # A mock is never an actual verified connection.
        self.real = transport is None

    def fetch(self, source: Source):
        params,payload=request_window(source,datetime.now(timezone.utc))
        headers={'User-Agent':'JAIME-Investor-HQ-P2/0.1 (local read-only data)',**source.headers}
        secrets=[self.settings.secret(key) for key in source.credentials]
        if source.credentials and not all(secrets):
            raise FetchError('CONFIG_REQUIRED' if source.auth=='sec' else 'NO_CREDENTIALS')
        if source.auth=='sec':
            if '@' not in secrets[0] or any(c in secrets[0] for c in '\r\n'):
                raise FetchError('CONFIG_REQUIRED')
            headers['User-Agent']='JAIME-Investor-HQ '+secrets[0]
        elif source.auth=='alpaca':
            headers.update({'APCA-API-KEY-ID':secrets[0],'APCA-API-SECRET-KEY':secrets[1]})
        elif source.auth=='t212':
            import base64
            headers['Authorization']='Basic '+base64.b64encode((':'.join(secrets)).encode()).decode()
        elif source.auth.startswith('header:'):
            headers[source.auth.split(':',1)[1]]=secrets[0]
        elif source.auth.startswith('query:'):
            params[source.auth.split(':',1)[1]]=secrets[0]
        elif source.auth=='bls':
            payload={**payload,'registrationkey':secrets[0]}
        elif source.auth=='tiingo':
            headers['Authorization']='Token '+secrets[0]
        validate_request(source,source.method,source.url,payload)
        started=time.monotonic()
        try:
            self.resolver(urlsplit(source.url).hostname)
            with httpx.Client(transport=self.transport, timeout=httpx.Timeout(source.read_timeout,connect=5), follow_redirects=False, trust_env=False) as client:
                with client.stream(source.method,source.url,params=params,headers=headers,json=payload) as response:
                    status=response.status_code
                    if status != 200:
                        retry=response.headers.get('Retry-After','0')
                        raise FetchError({401:'AUTH_FAILED',403:'RIGHTS_RESTRICTED',429:'RATE_LIMITED'}.get(status,'ERROR'),status,retry_seconds(retry))
                    chunks=[];size=0
                    for chunk in response.iter_bytes():
                        size+=len(chunk)
                        if time.monotonic()-started>30:raise FetchError('TIMEOUT',status)
                        if size>MAX_BYTES:
                            raise FetchError('INVALID_PAYLOAD',status)
                        chunks.append(chunk)
                    return b''.join(chunks),status
        except FetchError:
            raise
        except httpx.TimeoutException:
            raise FetchError('TIMEOUT') from None
        except (httpx.HTTPError,OSError):
            raise FetchError('OFFLINE') from None
