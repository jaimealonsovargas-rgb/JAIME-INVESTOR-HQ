# P2 — Catálogo máximo de fuentes financieras: cobertura real y 0 EUR

> **Ampliación solicitada 2026-10-14.** Investigación y plan para Codex, **NO implementación ni conectividad verificada**. Meta: integrar **el máximo de fuentes independientes gratuitas y permitidas** que aporten datos útiles. El catálogo es de **34 candidatos diferenciados** (A01–A19, B01–B15), además de fuentes C para investigación. Nunca confundir número de candidatos con conectores operativos. Mantener PAPER ONLY, no órdenes, 0 EUR y STOP antes de P3.

## 1. Arquitectura: conectar muchas fuentes, no acumular nombres

El plan inicial de P2 tenía siete fuentes. **Se amplía** a un registry de proveedores, un núcleo compartido HTTP/parsers/validación/identidad/caché/cuotas/derechos y adaptadores modulares. Implementar primero las fuentes públicas que no necesitan clave; después las que requieren cuenta gratuita. **No bloquear toda P2 por una API sin credenciales**. Un adaptador vacío, un mock o una URL en el catálogo **no cuenta como conexión real**.

Estados separados por fuente:
- `CANDIDATE`: documentación encontrada, todavía sin código.
- `IMPLEMENTED`: adaptador y tests de parser/contrato, quizá sin acceso real.
- `CONNECTED`: HTTP real verificado desde el PC, fecha, endpoint y resultado, no solo tests mock.
- `USABLE`: además CONNECTED, derechos, tipo, cobertura, frescura y licencia compatibles con el uso concreto.
- `NO_CREDENTIALS`, `CONFIG_REQUIRED`, `RATE_LIMITED`, `RIGHTS_RESTRICTED`, `PLAN_REQUIRED`, `OFFLINE`, `ERROR` y `NOT_VERIFIED`: razones específicas.

**Política de activación:** para APIs públicas sin clave, comprobadas y legalmente utilizables, conexión **bajo demanda** habilitada por defecto cuando el usuario pide esos datos, con opción de desactivarla, cache y límites conservadores. No hacer 34 requests al arrancar, ni sondear cada NPC. SEC exige User-Agent con contacto real configurado, no inventarlo. Para APIs con key, preparar código y tests pero esperar a que el usuario añada su propia clave en el .env local; nunca registrar cuentas, pagar ni usar claves ficticias. Derecho de visualización distinto de acceso gratuito.

## 2. PRIORIDAD A — 19 fuentes públicas sin clave o con consulta pública

| ID | Fuente | Datos y uso | Referencia oficial / endpoint | Condiciones |
|---|---|---|---|---|
| A01 | **ECB / BCE** | FX referencia, tipos, series euro SDMX | https://data.ecb.europa.eu/help/api/data | Fixing ≠ spot negociable; par y fecha |
| A02 | **Banco de España BIEST** | España: tipos, crédito, deuda, depósitos, macro | https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html | JSON `app.bde.es/bierest`, series y fecha |
| A03 | **INE España** | IPC, empleo, PIB, estadísticas | https://www.ine.es/dyngs/DAB/index.htm?cid=1100 | JSON `servicios.ine.es/wstempus/js/`; CC BY 4.0 con atribución según portal |
| A04 | **Eurostat** | PIB, inflación, empleo, indicadores UE | https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/sdmx3.0 | SDMX, revisión y frecuencia |
| A05 | **OECD/OCDE** | CLI/LEI, tipos, crecimiento, comparativas | https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html | API SDMX gratuita con rate limiting |
| A06 | **World Bank** | Macro mundial, PIB, deuda, demografía | https://datahelpdesk.worldbank.org/knowledgebase/articles/889392 | API v2 sin key, JSON/paginación |
| A07 | **BIS** | Crédito, banca, deuda, estadísticas FX | https://stats.bis.org/api-doc/v2/ | SDMX, no precio spot |
| A08 | **US Treasury** | Curvas US, bills, TIPS y históricos | https://home.treasury.gov/resource-center/data-chart-center/interest-rates | Curva ≠ precio de bono ISIN |
| A09 | **SEC EDGAR** | XBRL, filings y fundamentales US | https://www.sec.gov/search-filings/edgar-application-programming-interfaces | Sin key pero requiere User-Agent identificable con contacto real; fair access |
| A10 | **BLS v1** | CPI, empleo, PPI USA | https://www.bls.gov/developers/api_FAQs.htm | Sin registro; **25 requests/día**, GET para consulta simple |
| A11 | **IMF/FMI** | Balanza de pagos, deuda y macro internacional | https://data.imf.org/en/Resource-Pages/IMF-API | SDMX 2.1/3.0; confirmar endpoint/portal antes de activar |
| A12 | **ESMA FIRDS** | Referencias de instrumentos europeos/ISIN | https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files | Ficheros grandes, ingesta incremental, no descarga masiva en arranque |
| A13 | **Kraken Public** | Cripto ticker, OHLC, profundidad por venue | https://support.kraken.com/articles/360000919986-public-endpoint-examples-you-can-try-them-directly-in-a-web-browser- | Sin cuenta; símbolos Kraken y cuotas |
| A14 | **Binance market-data-only** | Cripto spot ticker, velas, libro | https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md | Host `data-api.binance.vision`; nunca host trading, comprobar geografía |
| A15 | **CoinPaprika Free** | Cripto agregada, metadata, precios | https://docs.coinpaprika.com/ | Sin key; condiciones hobby/no comercial y límites |
| A16 | **CoinGecko Public** | Cripto agregada, volumen, metadata | https://support.coingecko.com/articles/5125303456-what-is-the-rate-limit-for-coingecko-api-public-plan | Público ~5–15 req/min según condiciones, Demo separado |
| A17 | **GDELT DOC** | Noticias por entidad, país, fecha, URL | https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/ | Solo metadata/título/enlace, no copiar artículos de terceros |
| A18 | **Coinbase Exchange Public** | Cripto ticker/velas por venue | https://docs.cdp.coinbase.com/exchange/rest-api/requests | Verificar endpoints públicos concretos; sin cuentas ni órdenes |
| A19 | **OpenFIGI sin key** | Identificadores ISIN/FIGI/ticker/venue | https://www.openfigi.com/api/documentation | **POST read-only** de mapping, 25 req/min y 10 jobs/request sin key; excepción controlada `5 |

**A no significa automáticamente USABLE**: antes de mostrar números comprobar licencia, retraso y derechos; A11/A18 necesitan concretar endpoint y A12 gestionar tamaño. Para SEC, sin contacto real, estado CONFIG_REQUIRED.

## 3. PRIORIDAD B — 15 APIs con registro gratuito o plan gratuito condicionado

| ID | Proveedor | Utilidad | Referencia y cautela |
|---|---|---|---|
| B01 | **FRED** | Series macro y revisiones | https://fred.stlouisfed.org/docs/api/api_key.html ; requiere key propia |
| B02 | **BEA USA** | PIB, PCE, cuentas nacionales | https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf ; UserID gratis por registro |
| B03 | **BLS v2** | Mayor cuota/volumen BLS | https://www.bls.gov/developers/api_FAQs.htm ; registro, POST de consulta para series múltiples (`5) |
| B04 | **Alpaca Basic Market Data** | Acciones/ETF US **IEX** | https://docs.alpaca.markets/us/docs/about-market-data-api ; clave, IEX ≠ SIP |
| B05 | **Trading 212 DEMO** | Catálogo/metadatos demo | https://docs.trading212.com/api/ ; solo GET, no cuentas live |
| B06 | **Twelve Data Basic** | Datos financieros según cuota | https://twelvedata.com/pricing ; clave, derechos display restringidos por defecto |
| B07 | **Alpha Vantage Free** | EOD/históricos e indicadores | https://www.alphavantage.co/support/ ; 25 requests/día para mayoría de datasets; realtime/delayed US premium |
| B08 | **CoinGecko Demo** | Cripto con cuota estable | https://www.coingecko.com/en/api/pricing ; registro, límites y licencia a verificar |
| B09 | **OpenFIGI con key** | Más volumen de mapping | https://www.openfigi.com/api/documentation ; clave opcional, A19 funciona sin |
| B10 | **EIA USA** | Petróleo, gas, energía | https://www.eia.gov/opendata/ ; confirmar clave y API v2 |
| B11 | **Finnhub** | Datos US y metadatos | https://finnhub.io/docs/api ; **verificar endpoints gratis**: muchos mercados y bonos son de pago |
| B12 | **Financial Modeling Prep** | Fundamentales/ratios | https://site.financialmodelingprep.com/developer/docs ; **verificar free tier vigente** |
| B13 | **Massive / Polygon.io** | Datos US por plan | https://massive.com/pricing ; verificar plan/host y derechos, no prometer realtime gratis |
| B14 | **Tiingo** | EOD/metadata | https://www.tiingo.com/documentation/general/overview ; confirmar registro gratis y licencia |
| B15 | **Nasdaq Data Link** | Datasets económicos/históricos | https://docs.data.nasdaq.com/ ; gratuidad depende del dataset, no generalizar |

**B11–B15 son candidatos condicionados:** no crear clientes vacíos ni gastar tokens en endpoints que no sean gratuitos. Si no hay acceso real a 0 EUR, marcar PLAN_REQUIRED y seguir.

## 4. PRIORIDAD C — investigación y descargas especializadas

- **CNMV** (https://www.cnmv.es/): registros IIC/gestoras/fondos, documentos, estadísticas; investigar URL y derechos de descarga oficial. No confundir registros con NAV intradía.
- **ESMA FITRS y otros registros** (https://www.esma.europa.eu/): referencias MiFID y transparencia; ingesta selectiva, sin ficheros gigantes.
- **Bank of England** (https://www.bankofengland.co.uk/boeapps/database/): series históricas y tipos; verificar acceso automatizado.
- **Federal Reserve Board** (https://www.federalreserve.gov/data.htm): tipos/estadísticas/series oficiales, CSV/RSS donde se permita.
- **IR de emisores y RSS de reguladores**: documentos, anuncios y hechos relevantes con URL/fecha y respeto a licencias; no copiar artículos.
- **FINRA TRACE, CBOE/CME, bonos corporativos individuales, opciones, fondos europeos y exchanges**: precios y derechos suelen ser restringidos; investigar cobertura, pero **no simular feeds gratuitos**.
- **Yahoo Finance, Google Finance, TradingView, Investing.com y Stooq**: sitios útiles para consultar manualmente, pero **NO scraping ni endpoints internos sin autorización**. Si no hay API oficial autorizada, solo enlaces, no fuente principal.

## 5. Excepción técnica de POST que es solo consulta de datos

Por defecto solo **GET**. Existen APIs de datos que usan POST **sin modificar nada**:
- OpenFIGI: `POST https://api.openfigi.com/v3/mapping`, mapping de identificadores, límite de jobs/payload.
- BLS: `POST https://api.bls.gov/publicAPI/v2/timeseries/data/`, consulta de series cuando se habilite v2; BLS v1 GET como alternativa.

Solo si Codex puede asegurar **allowlist exacta de host + path + verbo**, payload acotado, sin redirects y pruebas de que no se usan para operaciones. **PROHIBIDO todo POST/PUT/PATCH/DELETE hacia brókeres/exchanges, cuentas, órdenes, transferencias o trading**. `POST /api/orders` local siempre 403. No permitir URLs arbitrarias desde frontend. Si no puede garantizarse la separación, desactivar excepción y dejar estado pendiente. Esta excepción es **read-only por semántica**, no permiso de operar.

## 6. Fallback y prioridad por clase de activo

| Necesidad | Preferencia y alternativas | Prohibición |
|---|---|---|
| Precio US | Alpaca IEX si habilitada; EOD de Alpha Vantage, Twelve, Finnhub según licencia | IEX ≠ SIP; EOD ≠ realtime |
| Precio Europa | Feed europeo **verificado** con licencia, o solo metadata ESMA | ADR US ≠ acción española; no inventar BME |
| ISIN/FIGI | OpenFIGI y ESMA FIRDS; aliases por proveedor | Ticker ambiguo no identifica activo |
| Fundamentales US | SEC XBRL, IR emisor; terceros autorizados | No confundir hechos auditados con estimaciones |
| Macro España | INE, BdE, Eurostat, ECB | IPC general ≠ IPCA sin etiqueta |
| Macro global | World Bank, OECD, BIS, IMF, FRED | No mezclar unidad, país, fecha o revisión |
| Bonos y tipos | Treasury/ECB/BdE/FRED para curvas | Curva ≠ precio de bono corporativo individual |
| Cripto | Kraken/Binance/Coinbase por venue; CoinGecko/Paprika agregados | No afirmar que agregado es precio ejecutable |
| Noticias | GDELT metadata y RSS oficial con permiso | No reproducir artículos sin derechos |

Cada observación lleva fuente, feed, venue, divisa, fecha observada/recibida, retraso, derechos y calidad. Fallback **solo entre datos semánticamente equivalentes**, con explicación de selección. Si ninguno cumple, NO DATA. Evitar promedio opaco entre exchanges y usar fuente original cuando FRED replica otra serie.

## 7. Checkpoints ampliados (sin aumentar burocracia)

**P2.0:** crear matriz `docs/P2_PROVIDERS_VERIFICACION.md` de los 34 candidatos con endpoints/métodos, auth, límites, derechos, estado y evidencia. Arquitectura compartida y opt-in/activación lazy. **No hacer 34 llamadas en arranque**.

**P2.1–P2.2:** registro canónico/aliases, capacidades, observaciones Decimal/UTC, calidad, cache, cuotas, HTTP seguro, parser compartido SDMX/CSV/JSON/XBRL; test de contrato. Base común antes de múltiples adaptadores.

**P2.3a — España/Europa:** ECB, Banco de España, INE, Eurostat, OECD. **P2.3b — macro global/US:** World Bank, BIS, Treasury, SEC si contacto, BLS v1, IMF si endpoint viable. **P2.3c — identidad/cripto/noticias:** Kraken, Binance solo datos, Coinbase public, CoinPaprika, CoinGecko Public, GDELT, OpenFIGI (POST read-only allowlisted), ESMA FIRDS selectivo. Gate por proveedor: adapter + tests + smoke test HTTP real cuando se permita, fecha/estado; **si uno falla, seguir con el siguiente**, no bloquear lote.

**P2.4a — claves macro/identidad:** FRED, BEA, BLS v2, EIA, Alpha Vantage, CoinGecko Demo, OpenFIGI key. **P2.4b — mercado/broker solo lectura:** Alpaca Basic IEX, Trading 212 DEMO, Twelve Data Basic. **P2.4c — opcionales condicionados:** Finnhub, FMP, Massive, Tiingo, Nasdaq Data Link **solo si se confirma endpoint gratuito**; sin clave, tests y NO_CREDENTIALS, sin fingir conectividad.

**P2.5:** panel Sistemas/Data Quality con filtros y contadores **Candidatos / Implementados / Conectados realmente / Utilizables**; motivo, última prueba, latencia medida y cuota conocida. Panel Research puede usar datos realmente autorizados, sin inventar NAV/P&L/órdenes.

**P2.6:** pruebas por conector y contratos, offline, 401/403/429/timeout, cache, permisos, no secretos, no trading, tests P0, navegador P1, FPS y STATUS. **Objetivo máximo real**, no prometer 34 conexiones si hay claves/planes pendientes. STOP antes de P3.

## 8. Documentación consultada 2026-10-14

INE API y licencia: https://www.ine.es/datosabiertos/ ; BdE BIEST: https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html ; World Bank v2 sin clave: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392 ; OECD SDMX gratis: https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html ; BIS: https://stats.bis.org/api-doc/v2/ ; Eurostat: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/sdmx3.0 ; BLS: https://www.bls.gov/developers/api_FAQs.htm ; OpenFIGI: https://www.openfigi.com/api/documentation ; Kraken: https://support.kraken.com/articles/360000919986-public-endpoint-examples-you-can-try-them-directly-in-a-web-browser- ; Binance: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md ; CoinGecko: https://support.coingecko.com/articles/5125303456-what-is-the-rate-limit-for-coingecko-api-public-plan ; CoinPaprika: https://docs.coinpaprika.com/ ; Alpha Vantage: https://www.alphavantage.co/support/ ; SEC: https://www.sec.gov/search-filings/edgar-application-programming-interfaces ; ESMA FIRDS: https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files .

**Esta lista no acredita disponibilidad en el PC ni derechos de uso**. Codex debe comprobarlos y registrar evidencia por proveedor. Priorizar conectores que de verdad funcionan frente a 34 stubs.