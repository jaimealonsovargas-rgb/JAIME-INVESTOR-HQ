# Proveedores, límites y calidad de datos

## Alpaca PAPER
Trading paper en https://paper-api.alpaca.markets; datos en https://data.alpaca.markets. Comprobar credenciales, mercado, acceso, cobertura, IEX vs SIP, retrasos, órdenes y cuenta. Paper no equivale a ejecución real. Empezar en modo lectura; escritura PAPER solo en P6.

## Trading 212 DEMO
Endpoint demo conocido: https://demo.trading212.com/api/v0. La API puede estar en beta; comprobar versión, permisos, instrumentos, autenticación, límites y soporte demo actual. Nunca asumir idempotencia en creación de órdenes. Timeout de SUBMITTING → UNKNOWN → consultar antes de repetir.

## Twelve Data FREE
https://api.twelvedata.com. Verificar límites del plan y condiciones de uso/visualización; no publicar datos si los derechos no lo permiten. Caches, cuotas configurables, backoff y estado de límite alcanzado.

## Catálogo ampliado P2 — máxima cobertura

**Instrucción vigente:** [P2_CATALOGO_MAXIMO_FUENTES.md](P2_CATALOGO_MAXIMO_FUENTES.md) y [PLAN_P2_CHECKPOINTS.md](PLAN_P2_CHECKPOINTS.md). Además de los siete proveedores originales, evaluar 34 fuentes candidatas: BdE, INE, Eurostat, OECD, World Bank, BIS, IMF, BLS, BEA, EIA, OpenFIGI, ESMA, Kraken, Binance solo datos, Coinbase público, CoinGecko, CoinPaprika, GDELT, Alpha Vantage, Finnhub, FMP, Massive, Tiingo, Nasdaq Data Link, etc. Prioridad **conectores públicos sin clave y realmente verificables**, después free tiers con key. No confundir candidatos, implementados, conectados y utilizables. **POST de consulta read-only** únicamente para OpenFIGI/BLS v2 con allowlist exacta; jamás órdenes ni POST a brokers/exchanges.

## Otras fuentes gratuitas
SEC EDGAR/CompanyFacts (con fair access), ECB Data API, FRED (clave cuando aplique), US Treasury, informes IR y reguladores, siempre según licencia. No confundir indicadores macro con precio ejecutable. Noticias con URL, fecha y permiso.

## Contrato de observación
instrument_id; provider; feed; observed_at; received_at; currency; bid/ask/last; volume; is_delayed; stale_after; rights; quality_flags; error; payload_hash. No hay ejecución con precio stale. Modo offline explícito; ausencia de claves no rompe la app. Nunca falsificar fuente ni timestamp.
