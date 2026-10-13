# Proveedores, límites y calidad de datos

## Alpaca PAPER
Trading paper en https://paper-api.alpaca.markets; datos en https://data.alpaca.markets. Comprobar credenciales, mercado, acceso, cobertura, IEX vs SIP, retrasos, órdenes y cuenta. Paper no equivale a ejecución real. Empezar en modo lectura; escritura PAPER solo en P6.

## Trading 212 DEMO
Endpoint demo conocido: https://demo.trading212.com/api/v0. La API puede estar en beta; comprobar versión, permisos, instrumentos, autenticación, límites y soporte demo actual. Nunca asumir idempotencia en creación de órdenes. Timeout de SUBMITTING → UNKNOWN → consultar antes de repetir.

## Twelve Data FREE
https://api.twelvedata.com. Verificar límites del plan y condiciones de uso/visualización; no publicar datos si los derechos no lo permiten. Caches, cuotas configurables, backoff y estado de límite alcanzado.

## Otras fuentes gratuitas
SEC EDGAR/CompanyFacts (con fair access), ECB Data API, FRED (clave cuando aplique), US Treasury, informes IR y reguladores, siempre según licencia. No confundir indicadores macro con precio ejecutable. Noticias con URL, fecha y permiso.

## Contrato de observación
instrument_id; provider; feed; observed_at; received_at; currency; bid/ask/last; volume; is_delayed; stale_after; rights; quality_flags; error; payload_hash. No hay ejecución con precio stale. Modo offline explícito; ausencia de claves no rompe la app. Nunca falsificar fuente ni timestamp.
