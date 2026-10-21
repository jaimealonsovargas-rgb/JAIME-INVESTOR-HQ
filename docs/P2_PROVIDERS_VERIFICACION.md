# P2 · Verificación de proveedores

## Actualización verificada 20-10-2026

Catálogo actual: **36 modalidades / 31 proveedores / 34 adaptadores**. Se añade A21 del proveedor CoinPaprika existente, no un proveedor nuevo. La tabla histórica inferior conserva sus fechas; no representa disponibilidad actual. La pasada completa y los errores/restricciones posteriores están en `P2_REFRESH_Y_PERSISTENCIA.md`.

| Acceso | Prueba HTTP real | Evidencia / alcance | Derechos |
|---|---|---|---|
| A21 · CoinPaprika diario | 200, 2026-10-20T14:45:15.887871Z, 8712 ms | 90 instantáneas diarias; 60 puntos visibles comparables. GET `/v1/tickers/btc-bitcoin/historical`, ventana móvil; no OHLCV ni precio ejecutable | [IA personal local](https://coinpaprika.com/api/agents), [sin redistribución](https://coinpaprika.com/api/licensing); Powered by CoinPaprika |
| A15 · CoinPaprika spot | 200, 2026-10-20T14:45:07.129833Z, 1071 ms | Una observación agregada, feed separado; TTL 900 s | Mismo permiso personal local; no valoración MASTER |
| A04 · Eurostat | 200, prueba real en `docs/evidencias/P4/datos-20261020/eurostat-ecoicop2-real.json` | Preset ECOICOP2 `prc_hicp_minr`, I25; sin empalmar base antigua | Fuente oficial reutilizable bajo sus condiciones |
| A18 · Coinbase | Acceso bloqueado antes de HTTP | `RIGHTS_RESTRICTED` aunque la tabla histórica contenga un 200 anterior | Condiciones actuales prohíben operación/evaluación IA sin consentimiento escrito |

## Matriz histórica de 14-10-2026

35 modalidades de acceso / 31 proveedores distintos (catálogo original de 34 más RSS oficial BCE). La documentación acredita un endpoint o derecho; **solo un HTTP 200 con respuesta válida acredita conexión**. Mocks, 401/403, cuerpos inválidos y existencia de documentación no cuentan. Uso exclusivo local; no redistribuir feeds personales/internos. No se han creado cuentas ni contratado planes.

Esta matriz describe un preset acotado por adaptador, no cobertura universal. Catálogo ejecutable: `backend/app/data_catalog.py`. Último smoke: 2026-10-14T23:10:20.937175+00:00. Latencia incluye DNS/TLS/descarga real; no se inventa retraso del feed.

| ID / proveedor | Endpoint de consulta | Dato / mercado | Auth / cuota | Adaptador / HTTP / usable | Última comprobación / latencia |
|---|---|---|---|---|---|
| A01 · BCE | GET `https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A` · [documentación](https://data.ecb.europa.eu/help/api/data) | fx_reference / STATISTICS / EU | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T23:09:46.279487Z / 20791 ms |
| A02 · Banco de España | GET `https://app.bde.es/bierest/resources/srdatosapp/favoritas` · [documentación](https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html) | macro_series / STATISTICS / ES | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:18:46.427990Z / 7398 ms |
| A03 · INE | GET `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/50902` · [documentación](https://www.ine.es/dyngs/DAB/index.htm?cid=1100) | macro_series / STATISTICS / ES | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:19:12.391282Z / 23685 ms |
| A04 · Eurostat | GET `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_midx` · [documentación](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started) | macro_series / STATISTICS / ES | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:19:17.752198Z / 4943 ms |
| A05 · OCDE | GET `https://sdmx.oecd.org/public/rest/v1/data/OECD.SDD.STES,DSD_STES@DF_CLI/.M.LI...AA...H` · [documentación](https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html) | macro_series / STATISTICS / global | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:19:29.083538Z / 11106 ms |
| A06 · Banco Mundial | GET `https://api.worldbank.org/v2/country/ES/indicator/NY.GDP.MKTP.CD` · [documentación](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) | macro_series / STATISTICS / ES | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:19:39.299372Z / 7968 ms |
| A07 · BIS | GET `https://stats.bis.org/api/v1/data/WS_EER/M.N.B.ES` · [documentación](https://stats.bis.org/api-doc/v2/) | macro_series / STATISTICS / ES | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:29:00.664697Z / 755 ms |
| A08 · Tesoro de Estados Unidos | GET `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml` · [documentación](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) | yield_curve / STATISTICS / US | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:20:02.200162Z / 12748 ms |
| A09 · SEC EDGAR | GET `https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json` · [documentación](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | fundamental_fact / STATISTICS / US | sec_contact · Fair access: 10 req/s; local 2/min. | sí / — / no · CONFIG_REQUIRED | sin petición / — |
| A10 · BLS v1 | GET `https://api.bls.gov/publicAPI/v1/timeseries/data/CUUR0000SA0` · [documentación](https://www.bls.gov/developers/api_FAQs.htm) | macro_series / STATISTICS / US | público · 25 consultas/día v1; local 20/día. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:23:33.888388Z / 6228 ms |
| A11 · FMI DataMapper | GET `https://www.imf.org/external/datamapper/api/v2/NGDP_RPCH/ESP` · [documentación](https://www.imf.org/external/datamapper/api/) | macro_series / STATISTICS / ES | público · Consulta selectiva documentada DataMapper; no descarga masiva. SDMX beta separado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:31:00.144469Z / 2432 ms |
| A12 · ESMA FIRDS índice | GET `https://registers.esma.europa.eu/solr/esma_registers_firds_files/select` · [documentación](https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files) | instrument_metadata / EU / global | público · Índice machine-to-machine oficial, 3 enlaces; ningún ZIP masivo. | sí / 200 / no · RIGHTS_RESTRICTED | 2026-10-14T19:27:40.893398Z / 20371 ms |
| A13 · Kraken Public | GET `https://api.kraken.com/0/public/Trades` · [documentación](https://docs.kraken.com/api/docs/rest-api/get-recent-trades/) | market_quote / KRAKEN / global | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / no · RIGHTS_RESTRICTED | 2026-10-14T19:23:41.205136Z / 6395 ms |
| A14 · Binance data-only | GET `https://data-api.binance.vision/api/v3/aggTrades` · [documentación](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints) | market_quote / BINANCE / global | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / no · RIGHTS_RESTRICTED | 2026-10-14T19:23:56.365226Z / 15097 ms |
| A15 · CoinPaprika Free | GET `https://api.coinpaprika.com/v1/tickers/btc-bitcoin` · [documentación](https://docs.coinpaprika.com/) | market_quote / AGGREGATED / global | público · 20.000/mes; presupuesto local 5/min. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:24:15.130114Z / 18621 ms |
| A16 · CoinGecko Public | GET `https://api.coingecko.com/api/v3/simple/price` · [documentación](https://docs.coingecko.com/docs/keyless-public-api) | market_quote / AGGREGATED / global | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / no · RIGHTS_RESTRICTED | 2026-10-14T19:24:26.335714Z / 11106 ms |
| A17 · GDELT DOC | GET `https://api.gdeltproject.org/api/v2/doc/doc` · [documentación](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) | news_metadata / NEWS / global | público · Presupuesto local conservador; límite oficial no publicado. | sí / — / no · TIMEOUT | 2026-10-14T23:10:20.715316Z / 15093 ms |
| A18 · Coinbase Exchange Public | GET `https://api.exchange.coinbase.com/products/BTC-USD/ticker` · [documentación](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-ticker) | market_quote / COINBASE / global | público · Presupuesto local conservador; límite oficial no publicado. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:25:14.360144Z / 40482 ms |
| A19 · OpenFIGI público | POST `https://api.openfigi.com/v3/mapping` · [documentación](https://www.openfigi.com/api/documentation) | instrument_metadata / MAPPING / global | público · 25/min, 10 jobs/petición sin clave; local 10/min. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T19:25:30.871156Z / 15517 ms |
| B01 · FRED | GET `https://api.stlouisfed.org/fred/series/observations` · [documentación](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) | macro_series / STATISTICS / US | fred_api_key · Presupuesto local conservador; límite oficial no publicado. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B02 · BEA | GET `https://apps.bea.gov/api/data/` · [documentación](https://www.bea.gov/resources/for-developers) | macro_series / STATISTICS / US | bea_api_key · Presupuesto local conservador; límite oficial no publicado. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B03 · BLS v2 | POST `https://api.bls.gov/publicAPI/v2/timeseries/data/` · [documentación](https://www.bls.gov/developers/api_FAQs.htm) | macro_series / STATISTICS / US | bls_api_key · Registro gratuito: hasta 500/día según BLS; local 20/día compartido con v1. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B04 · Alpaca Basic IEX | GET `https://data.alpaca.markets/v2/stocks/AAPL/bars` · [documentación](https://docs.alpaca.markets/us/reference/stockbars) | market_quote / IEX / US | alpaca_api_key, alpaca_secret_key · Basic 200/min; consulta exclusivamente IEX, nunca SIP. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B05 · Trading 212 DEMO metadata | GET `https://demo.trading212.com/api/v0/equity/metadata/instruments` · [documentación](https://docs.trading212.com/api) | instrument_metadata / T212_DEMO / global | trading212_api_key, trading212_api_secret · GET catálogo: 1/min; sin cuentas, posiciones u órdenes. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B06 · Twelve Data Basic | GET `https://api.twelvedata.com/symbol_search` · [documentación](https://twelvedata.com/docs#symbol-search) | instrument_metadata / SEARCH / global | twelve_data_api_key · Basic 8 créditos/min, 800/día; local 5/min. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B07 · Alpha Vantage Free EOD | GET `https://www.alphavantage.co/query` · [documentación](https://www.alphavantage.co/documentation/) | market_quote / US_EOD / US | alpha_vantage_api_key · 25/día; compacto gratuito, full/realtime no utilizados. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B08 · CoinGecko Demo | GET `https://api.coingecko.com/api/v3/simple/price` · [documentación](https://docs.coingecko.com/docs/keyless-public-api) | market_quote / AGGREGATED / global | coingecko_demo_api_key · Demo con registro; respetar cuota del panel de usuario. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B09 · OpenFIGI con clave | POST `https://api.openfigi.com/v3/mapping` · [documentación](https://www.openfigi.com/api/documentation) | instrument_metadata / MAPPING / global | openfigi_api_key · Clave aumenta cuota; presupuesto local 10/min compartido. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B10 · EIA v2 | GET `https://api.eia.gov/v2/petroleum/pri/spt/data/` · [documentación](https://www.eia.gov/opendata/documentation.php) | macro_series / STATISTICS / US | eia_api_key · Presupuesto local conservador; límite oficial no publicado. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B11 · Finnhub | GET `Endpoint pendiente` · [documentación](https://finnhub.io/docs/api) | instrument_metadata / US / global | público · Presupuesto local conservador; límite oficial no publicado. | no / — / no · PLAN_REQUIRED | sin petición / — |
| B12 · Financial Modeling Prep Free | GET `https://financialmodelingprep.com/stable/profile` · [documentación](https://site.financialmodelingprep.com/developer/docs) | instrument_metadata / REFERENCE / US | fmp_api_key · 250/día Basic; local 200/día; entitlement real pendiente. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B13 · Massive Basic | GET `https://api.massive.com/v1/marketstatus/now` · [documentación](https://massive.com/docs/rest/stocks/market-operations/market-status) | instrument_metadata / MARKET_STATUS / US | massive_api_key · Basic 5/min; market status gratuito, no realtime quote. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B14 · Tiingo Starter | GET `https://api.tiingo.com/tiingo/daily/AAPL` · [documentación](https://www.tiingo.com/documentation/end-of-day) | instrument_metadata / REFERENCE / US | tiingo_api_key · Starter $0: 50/h, 1000/día, 500 símbolos/mes, 1 GB/mes. | sí / — / no · NO_CREDENTIALS | sin petición / — |
| B15 · Nasdaq Data Link | GET `Endpoint pendiente` · [documentación](https://docs.data.nasdaq.com/) | macro_series / STATISTICS / global | público · Presupuesto local conservador; límite oficial no publicado. | no / — / no · PLAN_REQUIRED | sin petición / — |
| A20 · BCE · noticias RSS / Agent Reach auditado | GET `https://www.ecb.europa.eu/rss/press.html` · [documentación](https://www.ecb.europa.eu/home/html/rss.en.html) | news_metadata / PUBLISHER / EU | público · Canal público auditado; 2/min local, cache 30 min. Sin artículos completos, cookies ni sesión. | sí / 200 / sí · AVAILABLE_VERIFIED | 2026-10-14T23:10:05.543793Z / 18939 ms |

## Derechos por modalidad

D = visualización local; C = cache local; R = redistribución. “Sí” depende del ámbito indicado y atribución; nunca licencia comercial implícita. Una clave no amplía automáticamente estos permisos.

| ID | Derecho / ámbito | D / C / R | Prueba documental |
|---|---|---|---|
| A01 | BCE · atribución / open | sí / sí / sí | [2026-10-14](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html) |
| A02 | Banco de España · atribución / open | sí / sí / sí | [2026-10-14](https://www.bde.es/wbe/es/pie/aviso-legal/) |
| A03 | INE · CC BY 4.0 / open | sí / sí / sí | [2026-10-14](https://www.ine.es/datosabiertos/) |
| A04 | Eurostat · atribución / open | sí / sí / sí | [2026-10-14](https://ec.europa.eu/eurostat/en/help/copyright-notice) |
| A05 | OCDE Data Terms · atribución / open | sí / sí / sí | [2026-10-14](https://www.oecd.org/en/about/terms-conditions.html) |
| A06 | Banco Mundial · CC BY 4.0 / open | sí / sí / sí | [2026-10-14](https://datacatalog.worldbank.org/public-licenses) |
| A07 | BIS estadísticas · atribución / open | sí / sí / sí | [2026-10-14](https://data.bis.org/help/legal) |
| A08 | US Treasury · datos públicos / open | sí / sí / sí | [2026-10-14](https://www.copyright.gov/title17/92chap1.html#105) |
| A09 | SEC · datos públicos EDGAR / open | sí / sí / sí | [2026-10-14](https://www.sec.gov/about/webmaster-frequently-asked-questions) |
| A10 | BLS · dominio público / open | sí / sí / sí | [2026-10-14](https://www.bls.gov/opub/copyright-information.htm) |
| A11 | FMI Data · investigación no comercial; atribución / personal | sí / sí / no | [2026-10-14](https://www.imf.org/en/about/copyright-and-terms) |
| A12 | ESMA · índice oficial; display pendiente / open | no / no / no | [2026-10-14](https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files) |
| A13 | Kraken · uso local; redistribución no autorizada / internal | no / no / no | [2026-10-14](https://www.kraken.com/legal) |
| A14 | Binance · acceso público, display pendiente / internal | no / no / no | [2026-10-14](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md) |
| A15 | CoinPaprika · personal no comercial / personal | sí / sí / no | [2026-10-14](https://coinpaprika.com/api/pricing/) |
| A16 | CoinGecko · atribución; display pendiente / personal | no / no / no | [2026-10-14](https://www.coingecko.com/en/api_terms) |
| A17 | GDELT · solo metadatos y enlaces / open | sí / sí / sí | [2026-10-14](https://www.gdeltproject.org/about.html) |
| A18 | Coinbase Market Data · interno; sin redistribución / internal | sí / sí / no | [2026-10-14](https://www.coinbase.com/legal/market_data) |
| A19 | OpenFIGI · MIT Open Symbology / open | sí / sí / sí | [2026-10-14](https://www.openfigi.com/about/faq) |
| B01 | FRED/DGS10 · Federal Reserve H.15, atribución / open | sí / sí / sí | [2026-10-14](https://fred.stlouisfed.org/series/DGS10) |
| B02 | BEA · estadísticas públicas / open | sí / sí / sí | [2026-10-14](https://www.bea.gov/about/using-bea-statistics) |
| B03 | BLS · dominio público / open | sí / sí / sí | [2026-10-14](https://www.bls.gov/opub/copyright-information.htm) |
| B04 | Alpaca Basic IEX · display pendiente / internal | no / no / no | [2026-10-14](https://docs.alpaca.markets/us/docs/about-market-data-api) |
| B05 | Trading 212 · catálogo demo, interno / internal | sí / sí / no | [2026-10-14](https://docs.trading212.com/api) |
| B06 | Twelve Basic · derechos display pendientes / internal | no / no / no | [2026-10-14](https://twelvedata.com/pricing) |
| B07 | Alpha Vantage · derechos display pendientes / personal | no / no / no | [2026-10-14](https://www.alphavantage.co/terms_of_service/) |
| B08 | CoinGecko · atribución; display pendiente / personal | no / no / no | [2026-10-14](https://www.coingecko.com/en/api_terms) |
| B09 | OpenFIGI · MIT Open Symbology / open | sí / sí / sí | [2026-10-14](https://www.openfigi.com/about/faq) |
| B10 | EIA · datos públicos con atribución / open | sí / sí / sí | [2026-10-14](https://www.eia.gov/about/copyrights_reuse.php) |
| B11 | Finnhub · endpoint gratis pendiente / open | no / no / no | [2026-10-14](https://finnhub.io/pricing) |
| B12 | FMP Basic · interno; display pendiente / internal | no / no / no | [2026-10-14](https://site.financialmodelingprep.com/faqs) |
| B13 | Massive Basic · personal, display pendiente / personal | no / no / no | [2026-10-14](https://massive.com/knowledge-base/article/does-massive-have-a-market-holiday-or-status-page) |
| B14 | Tiingo Starter · uso personal interno / personal | sí / sí / no | [2026-10-14](https://www.tiingo.com/about/pricing) |
| B15 | Nasdaq · dataset gratis no confirmado / open | no / no / no | [2026-10-14](https://docs.data.nasdaq.com/) |
| A20 | BCE · atribución; metadatos RSS propios / open | sí / sí / sí | [2026-10-14](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html) |

## Límites y pendientes

- SEC: necesita contacto real en `SEC_CONTACT`; no se ha inventado un email.
- FMI: DataMapper/WEO permite una consulta selectiva; incluye estimaciones/proyecciones, explícitamente etiquetadas. SDMX beta requiere investigación separada; no se usa la antigua API como si siguiera operativa.
- ESMA: índice machine-to-machine oficial implementado, tres enlaces; no se han descargado todos los ZIP ni se presume permiso de redistribución de referencias.
- Finnhub / Nasdaq: candidatura gratuita condicionada; no se contabiliza adaptador sin endpoint gratuito útil confirmado.
- Fuentes con clave: pruebas mock, estado NO_CREDENTIALS hasta configuración local; sin signup ni pago.
- Kraken/Binance/CoinGecko/Alpaca/Twelve/Alpha/FMP/Massive: derechos de visualización pendientes; el transporte puede comprobar acceso público/documentado pero no publica valores.
- España y UE: atribución y fidelidad obligatorias. Eurostat/OCDE/Banco Mundial pueden incluir terceros: solo el preset revisado, no permiso para todo el catálogo.
- BLS: atribución con fecha de acceso y aviso de que BLS no avala análisis posteriores. GDELT: solo metadatos y enlaces; jamás cuerpos o imágenes de artículos.
- Fixing BCE ≠ spot; curva Treasury ≠ bono; agregado cripto ≠ exchange; IEX ≠ SIP; EOD ≠ realtime. Todas las observaciones tienen execution_eligible=false.

## Fuentes especializadas

CNMV, BoE y Fed: investigación pendiente de endpoints y permisos. FINRA/CBOE/CME y bonos corporativos: no se presume un feed gratuito. Yahoo/Google/TradingView/Investing/Stooq: sin scraping ni endpoints internos.
