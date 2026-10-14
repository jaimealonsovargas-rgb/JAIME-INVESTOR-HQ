"""Catálogo cerrado. Un preset útil por modalidad; ninguna URL suministrada por UI."""
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from app.data_contracts import Rights, DataKind

VERIFIED = datetime(2026, 10, 14, tzinfo=timezone.utc)

def rights(name: str, url: str, scope='open', access=True, display=True, storage=True, redistribution=True):
    return Rights(license=name, source=url, checked_at=VERIFIED, scope=scope,
                  access_allowed=access, display_allowed=display, storage_allowed=storage,
                  redistribution_allowed=redistribution, attribution=name)

@dataclass(frozen=True)
class Source:
    id: str
    provider: str
    name: str
    url: str | None
    parser: str | None
    kind: DataKind
    feed: str
    rights: Rights
    docs: str
    country: str | None = None
    asset_class: str = 'MACRO_SERIES'
    venue: str = 'STATISTICS'
    params: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    credentials: tuple[str, ...] = ()
    auth: str = ''
    method: str = 'GET'
    payload: object = None
    ttl: int = 86400
    limit: int = 5
    window: int = 60
    quota_note: str = 'Presupuesto local conservador; límite oficial no publicado.'
    block: str | None = None
    read_timeout: int = 12

    @property
    def implemented(self):
        return bool(self.url and self.parser)

SOURCES = (
    Source('A01','ECB','BCE','https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A','sdmx_csv','fx_reference','EXR/D.USD.EUR.SP00.A',rights('BCE · atribución','https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html'),'https://data.ecb.europa.eu/help/api/data',country='EU',asset_class='FX',params={'lastNObservations':'5'},headers={'Accept':'text/csv'}),
    Source('A02','BDE','Banco de España','https://app.bde.es/bierest/resources/srdatosapp/favoritas','bde','macro_series','D_1NBAF472',rights('Banco de España · atribución','https://www.bde.es/wbe/es/pie/aviso-legal/'),'https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html',country='ES',params={'idioma':'es','series':'D_1NBAF472'}),
    Source('A03','INE','INE','https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/50902','ine','macro_series','50902',rights('INE · CC BY 4.0','https://www.ine.es/datosabiertos/'),'https://www.ine.es/dyngs/DAB/index.htm?cid=1100',country='ES',params={'nult':'1'}),
    Source('A04','EUROSTAT','Eurostat','https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_midx','jsonstat','macro_series','prc_hicp_midx',rights('Eurostat · atribución','https://ec.europa.eu/eurostat/en/help/copyright-notice'),'https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started',country='ES',params={'geo':'ES','coicop':'CP00','unit':'I15','lastTimePeriod':'3'}),
    Source('A05','OECD','OCDE','https://sdmx.oecd.org/public/rest/v1/data/OECD.SDD.STES,DSD_STES@DF_CLI/.M.LI...AA...H','sdmx_csv','macro_series','DSD_STES@DF_CLI',rights('OCDE Data Terms · atribución','https://www.oecd.org/en/about/terms-conditions.html'),'https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html',params={'startPeriod':'2026-07','endPeriod':'2026-09','dimensionAtObservation':'AllDimensions','format':'csvfilewithlabels'}),
    Source('A06','WORLD_BANK','Banco Mundial','https://api.worldbank.org/v2/country/ES/indicator/NY.GDP.MKTP.CD','worldbank','macro_series','WDI/NY.GDP.MKTP.CD',rights('Banco Mundial · CC BY 4.0','https://datacatalog.worldbank.org/public-licenses'),'https://datahelpdesk.worldbank.org/knowledgebase/articles/889392',country='ES',params={'format':'json','per_page':'5','mrv':'5'}),
    Source('A07','BIS','BIS','https://stats.bis.org/api/v1/data/WS_EER/M.N.B.ES','sdmx_csv','macro_series','WS_EER/M.N.B.ES',rights('BIS estadísticas · atribución','https://data.bis.org/help/legal'),'https://stats.bis.org/api-doc/v2/',country='ES',params={'startPeriod':'2026-07','endPeriod':'2026-09'},headers={'Accept':'text/csv'}),
    Source('A08','TREASURY','Tesoro de Estados Unidos','https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml','treasury','yield_curve','daily_treasury_yield_curve',rights('US Treasury · datos públicos','https://www.copyright.gov/title17/92chap1.html#105'),'https://home.treasury.gov/treasury-daily-interest-rate-xml-feed',country='US',asset_class='SOVEREIGN_BOND',params={'data':'daily_treasury_yield_curve','field_tdr_date_value_month':'202609'}),
    Source('A09','SEC','SEC EDGAR','https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json','sec','fundamental_fact','companyfacts/CIK0000320193',rights('SEC · datos públicos EDGAR','https://www.sec.gov/about/webmaster-frequently-asked-questions'),'https://www.sec.gov/search-filings/edgar-application-programming-interfaces',country='US',asset_class='EQUITY',credentials=('sec_contact',),auth='sec',limit=2,quota_note='Fair access: 10 req/s; local 2/min.'),
    Source('A10','BLS','BLS v1','https://api.bls.gov/publicAPI/v1/timeseries/data/CUUR0000SA0','bls','macro_series','CUUR0000SA0',rights('BLS · dominio público','https://www.bls.gov/opub/copyright-information.htm'),'https://www.bls.gov/developers/api_FAQs.htm',country='US',limit=20,window=86400,quota_note='25 consultas/día v1; local 20/día.'),
    Source('A11','IMF','FMI DataMapper','https://www.imf.org/external/datamapper/api/v2/NGDP_RPCH/ESP','imf','macro_series','WEO/NGDP_RPCH/ESP',rights('FMI Data · investigación no comercial; atribución','https://www.imf.org/en/about/copyright-and-terms',scope='personal',redistribution=False),'https://www.imf.org/external/datamapper/api/',country='ES',params={'periods':'2024,2025,2026'},quota_note='Consulta selectiva documentada DataMapper; no descarga masiva. SDMX beta separado.'),
    Source('A12','ESMA','ESMA FIRDS índice','https://registers.esma.europa.eu/solr/esma_registers_firds_files/select','firds_index','instrument_metadata','FIRDS/publication_index',rights('ESMA · índice oficial; display pendiente','https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files',display=False,storage=False,redistribution=False),'https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files',asset_class='MULTI',venue='EU',params={'q':'*','fq':'publication_date:[2026-10-13T00:00:00Z TO 2026-10-13T23:59:59Z]','wt':'xml','start':'0','rows':'3'},quota_note='Índice machine-to-machine oficial, 3 enlaces; ningún ZIP masivo.'),
    Source('A13','KRAKEN','Kraken Public','https://api.kraken.com/0/public/Trades','kraken','market_quote','Trades/XBTUSD',rights('Kraken · uso local; redistribución no autorizada','https://www.kraken.com/legal',scope='internal',display=False,storage=False,redistribution=False),'https://docs.kraken.com/api/docs/rest-api/get-recent-trades/',asset_class='CRYPTO',venue='KRAKEN',params={'pair':'XBTUSD','count':'1'},ttl=60),
    Source('A14','BINANCE','Binance data-only','https://data-api.binance.vision/api/v3/aggTrades','binance','market_quote','aggTrades/BTCUSDT',rights('Binance · acceso público, display pendiente','https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md',scope='internal',display=False,storage=False,redistribution=False),'https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints',asset_class='CRYPTO',venue='BINANCE',params={'symbol':'BTCUSDT','limit':'1'},ttl=60),
    Source('A15','COINPAPRIKA','CoinPaprika Free','https://api.coinpaprika.com/v1/tickers/btc-bitcoin','paprika','market_quote','aggregate/btc-bitcoin',rights('CoinPaprika · personal no comercial','https://coinpaprika.com/api/pricing/',scope='personal',redistribution=False),'https://docs.coinpaprika.com/',asset_class='CRYPTO',venue='AGGREGATED',ttl=300,limit=5,quota_note='20.000/mes; presupuesto local 5/min.'),
    Source('A16','COINGECKO','CoinGecko Public','https://api.coingecko.com/api/v3/simple/price','coingecko','market_quote','aggregate/bitcoin',rights('CoinGecko · atribución; display pendiente','https://www.coingecko.com/en/api_terms',scope='personal',display=False,storage=False,redistribution=False),'https://docs.coingecko.com/docs/keyless-public-api',asset_class='CRYPTO',venue='AGGREGATED',params={'ids':'bitcoin','vs_currencies':'usd','include_last_updated_at':'true'},ttl=300,limit=3),
    Source('A17','GDELT','GDELT DOC','https://api.gdeltproject.org/api/v2/doc/doc','gdelt','news_metadata','DOC/artlist',rights('GDELT · solo metadatos y enlaces','https://www.gdeltproject.org/about.html'),'https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/',asset_class='MULTI',venue='NEWS',params={'query':'economy sourcelang:spanish','mode':'artlist','format':'json','maxrecords':'5','timespan':'6h'},ttl=900,limit=1,read_timeout=25),
    Source('A18','COINBASE','Coinbase Exchange Public','https://api.exchange.coinbase.com/products/BTC-USD/ticker','coinbase','market_quote','ticker/BTC-USD',rights('Coinbase Market Data · interno; sin redistribución','https://www.coinbase.com/legal/market_data',scope='internal',redistribution=False),'https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-ticker',asset_class='CRYPTO',venue='COINBASE',ttl=60),
    Source('A19','OPENFIGI','OpenFIGI público','https://api.openfigi.com/v3/mapping','openfigi','instrument_metadata','mapping',rights('OpenFIGI · MIT Open Symbology','https://www.openfigi.com/about/faq'),'https://www.openfigi.com/api/documentation',asset_class='MULTI',venue='MAPPING',method='POST',payload=[{'idType':'ID_ISIN','idValue':'US0378331005'}],limit=10,quota_note='25/min, 10 jobs/petición sin clave; local 10/min.'),
)

OPTIONAL = (
 Source('B01','FRED','FRED','https://api.stlouisfed.org/fred/series/observations','fred','macro_series','DGS10',rights('FRED/DGS10 · Federal Reserve H.15, atribución','https://fred.stlouisfed.org/series/DGS10'),'https://fred.stlouisfed.org/docs/api/fred/series_observations.html',country='US',params={'series_id':'DGS10','file_type':'json','sort_order':'desc','limit':'5'},credentials=('fred_api_key',),auth='query:api_key'),
 Source('B02','BEA','BEA','https://apps.bea.gov/api/data/','bea','macro_series','NIPA/T10101',rights('BEA · estadísticas públicas','https://www.bea.gov/about/using-bea-statistics'),'https://www.bea.gov/resources/for-developers',country='US',params={'method':'GetData','datasetname':'NIPA','TableName':'T10101','Frequency':'A','Year':'2025','ResultFormat':'JSON'},credentials=('bea_api_key',),auth='query:UserID'),
 replace(SOURCES[9],id='B03',name='BLS v2',url='https://api.bls.gov/publicAPI/v2/timeseries/data/',method='POST',payload={'seriesid':['CUUR0000SA0'],'startyear':'2025','endyear':'2025'},credentials=('bls_api_key',),auth='bls',limit=20,window=86400,quota_note='Registro gratuito: hasta 500/día según BLS; local 20/día compartido con v1.'),
 Source('B04','ALPACA','Alpaca Basic IEX','https://data.alpaca.markets/v2/stocks/AAPL/bars','alpaca','market_quote','IEX/daily/AAPL',rights('Alpaca Basic IEX · display pendiente','https://docs.alpaca.markets/us/docs/about-market-data-api',scope='internal',display=False,storage=False,redistribution=False),'https://docs.alpaca.markets/us/reference/stockbars',country='US',asset_class='EQUITY',venue='IEX',params={'timeframe':'1Day','start':'2026-09-01T00:00:00Z','end':'2026-09-08T00:00:00Z','limit':'5','feed':'iex','adjustment':'raw'},credentials=('alpaca_api_key','alpaca_secret_key'),auth='alpaca',quota_note='Basic 200/min; consulta exclusivamente IEX, nunca SIP.',ttl=86400),
 Source('B05','TRADING212','Trading 212 DEMO metadata','https://demo.trading212.com/api/v0/equity/metadata/instruments','t212','instrument_metadata','demo/instruments',rights('Trading 212 · catálogo demo, interno','https://docs.trading212.com/api',scope='internal',redistribution=False),'https://docs.trading212.com/api',asset_class='MULTI',venue='T212_DEMO',credentials=('trading212_api_key','trading212_api_secret'),auth='t212',limit=1,window=60,quota_note='GET catálogo: 1/min; sin cuentas, posiciones u órdenes.'),
 Source('B06','TWELVE','Twelve Data Basic','https://api.twelvedata.com/symbol_search','twelve','instrument_metadata','symbol_search/AAPL',rights('Twelve Basic · derechos display pendientes','https://twelvedata.com/pricing',scope='internal',display=False,storage=False,redistribution=False),'https://twelvedata.com/docs#symbol-search',asset_class='MULTI',venue='SEARCH',params={'symbol':'AAPL','outputsize':'5'},credentials=('twelve_data_api_key',),auth='query:apikey',limit=5,quota_note='Basic 8 créditos/min, 800/día; local 5/min.'),
 Source('B07','ALPHA_VANTAGE','Alpha Vantage Free EOD','https://www.alphavantage.co/query','alpha','market_quote','TIME_SERIES_DAILY/IBM/raw',rights('Alpha Vantage · derechos display pendientes','https://www.alphavantage.co/terms_of_service/',scope='personal',display=False,storage=False,redistribution=False),'https://www.alphavantage.co/documentation/',country='US',asset_class='EQUITY',venue='US_EOD',params={'function':'TIME_SERIES_DAILY','symbol':'IBM','outputsize':'compact'},credentials=('alpha_vantage_api_key',),auth='query:apikey',limit=20,window=86400,quota_note='25/día; compacto gratuito, full/realtime no utilizados.'),
 replace(SOURCES[15],id='B08',name='CoinGecko Demo',credentials=('coingecko_demo_api_key',),auth='header:x-cg-demo-api-key',limit=5,quota_note='Demo con registro; respetar cuota del panel de usuario.'),
 replace(SOURCES[18],id='B09',name='OpenFIGI con clave',credentials=('openfigi_api_key',),auth='header:X-OPENFIGI-APIKEY',limit=10,quota_note='Clave aumenta cuota; presupuesto local 10/min compartido.'),
 Source('B10','EIA','EIA v2','https://api.eia.gov/v2/petroleum/pri/spt/data/','eia','macro_series','petroleum/pri/spt',rights('EIA · datos públicos con atribución','https://www.eia.gov/about/copyrights_reuse.php'),'https://www.eia.gov/opendata/documentation.php',country='US',params={'frequency':'daily','data[0]':'value','facets[series][]':'RWTC','sort[0][column]':'period','sort[0][direction]':'desc','length':'5'},credentials=('eia_api_key',),auth='query:api_key'),
 Source('B11','FINNHUB','Finnhub',None,None,'instrument_metadata','profile2',rights('Finnhub · endpoint gratis pendiente','https://finnhub.io/pricing',access=False,display=False,storage=False,redistribution=False),'https://finnhub.io/docs/api',asset_class='EQUITY',venue='US',block='PLAN_REQUIRED'),
 Source('B12','FMP','Financial Modeling Prep Free','https://financialmodelingprep.com/stable/profile','fmp','instrument_metadata','profile/AAPL',rights('FMP Basic · interno; display pendiente','https://site.financialmodelingprep.com/faqs',scope='internal',display=False,storage=False,redistribution=False),'https://site.financialmodelingprep.com/developer/docs',country='US',asset_class='EQUITY',venue='REFERENCE',params={'symbol':'AAPL'},credentials=('fmp_api_key',),auth='query:apikey',limit=200,window=86400,quota_note='250/día Basic; local 200/día; entitlement real pendiente.'),
 Source('B13','MASSIVE','Massive Basic','https://api.massive.com/v1/marketstatus/now','massive','instrument_metadata','marketstatus/now',rights('Massive Basic · personal, display pendiente','https://massive.com/knowledge-base/article/does-massive-have-a-market-holiday-or-status-page',scope='personal',display=False,storage=False,redistribution=False),'https://massive.com/docs/rest/stocks/market-operations/market-status',country='US',asset_class='MULTI',venue='MARKET_STATUS',credentials=('massive_api_key',),auth='query:apiKey',limit=4,quota_note='Basic 5/min; market status gratuito, no realtime quote.'),
 Source('B14','TIINGO','Tiingo Starter','https://api.tiingo.com/tiingo/daily/AAPL','tiingo','instrument_metadata','daily/AAPL/metadata',rights('Tiingo Starter · uso personal interno','https://www.tiingo.com/about/pricing',scope='personal',redistribution=False),'https://www.tiingo.com/documentation/end-of-day',country='US',asset_class='EQUITY',venue='REFERENCE',credentials=('tiingo_api_key',),auth='tiingo',limit=40,window=3600,quota_note='Starter $0: 50/h, 1000/día, 500 símbolos/mes, 1 GB/mes.'),
 Source('B15','NASDAQ','Nasdaq Data Link',None,None,'macro_series','dataset license pending',rights('Nasdaq · dataset gratis no confirmado','https://docs.data.nasdaq.com/',access=False,display=False,storage=False,redistribution=False),'https://docs.data.nasdaq.com/',block='PLAN_REQUIRED'),
)
CATALOG = {s.id:s for s in (*SOURCES,*OPTIONAL)}
