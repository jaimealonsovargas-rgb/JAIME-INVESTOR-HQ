# P2 · backend verificado; integración visual pendiente del gate P1

Catálogo base: **31 proveedores distintos / 34 modalidades**. **32 adaptadores útiles / 29 proveedores implementados**, con normalizadores y tests por modalidad. Finnhub y Nasdaq siguen como candidatos condicionados porque no se confirmó un endpoint gratuito útil con derechos suficientes; no hay clases vacías que cuenten como conectores.

Última comprobación local en `seguridad-api-local.json`: **17 modalidades / 17 proveedores con HTTP válido y datos normalizados**; **11 fuentes utilizables y frescas**. CoinPaprika y Coinbase funcionaron y sus derechos permiten uso local, pero su cache de precios ya caducó: no se cuentan como disponibles ahora. Cuatro modalidades con display restringido: ESMA, Kraken, Binance y CoinGecko público. Trece modalidades con clave ausente; SEC necesita un contacto real para User-Agent. No se han creado cuentas ni usado claves de demostración ajenas.

Conexiones reales comprobadas: BCE, Banco de España, INE, Eurostat, OCDE, Banco Mundial, BIS, Treasury, BLS v1, FMI DataMapper, ESMA FIRDS (índice de archivos), Kraken, Binance data-only, CoinPaprika, CoinGecko público, Coinbase y OpenFIGI público. **GDELT no se cuenta:** timeout en dos intentos acotados, también con un horizonte menor. La falta de un feed no detuvo los demás.

## Qué acredita cada archivo

- `smoke-real*.json`: peticiones reales mediante transporte seguro, fechas, latencia medida, estado HTTP, cantidad normalizada y hash cuando puede publicarse. Los valores de feeds personales/internos no se redistribuyen en estas evidencias. Las cifras de cada archivo describen ese momento y versión, no son acumulables.
- `P2_PROVIDERS_VERIFICACION.md` en `docs/`: matriz de los 34 candidatos, endpoints, autenticación, cuota, derechos y última prueba por modalidad.
- `calidad-actual.json`: lectura intermedia; `seguridad-api-local.json` es la comprobación posterior de la API local tipada, health P0 y órdenes 403.
- Los primeros intentos negativos se conservan: BIS inicialmente devolvió XML en vez de CSV; FMI devolvió un ámbito mayor que el solicitado, por lo que el parser limita explícitamente país/periodos y marca estimaciones/proyecciones WEO. Un HTTP 200 sin datos válidos no acredita una fuente. El registro final usa el último resultado por modalidad y no la bandera histórica incorrecta del primer intento vacío de BIS.

## Infraestructura y seguridad

Clientes HTTPS con endpoints cerrados, sin redirects ni URLs del frontend; DNS público, verificación TLS, límite de tamaño y tiempos de espera. GET por defecto. Solo se admiten los dos POST estadísticos documentados de OpenFIGI/BLS v2, con payloads y años acotados. No existe un transporte hacia cuentas, órdenes o transferencias de bróker/exchange. Binance usa únicamente `data-api.binance.vision`; Alpaca solo market data IEX; Trading 212 solo catálogo DEMO.

Normalización JSON/CSV/SDMX XML y CSV/XBRL; Decimal desde texto, UTC, periodos separados de publicación, fuente/feed/venue/unidad/hash/derechos. Cache SQLite con identidad de derechos, TTL por feed y límite de filas; cuotas compartidas por proveedor, Retry-After, estados de error y circuit breaker. La retirada de derechos impide mostrar la cache. Fallback solo si coinciden tipo, serie, feed, frecuencia/precisión, mercado, divisa y unidad.

Migración incremental `0002_data`, aplicada tras backup consistente de la DB de usuario. Registro de **98 instrumentos/series reales**, sin seeds; incluye series macro y referencias FX/cripto según las respuestas recibidas. Una curva no se registra como un bono individual. OpenFIGI sin currency verificada no inventa una identidad monetaria. No se promete cobertura de acciones/ETF/bonos/índices ni compatibilidad paper por existir un endpoint o mapping. Investigación, valoración y elegibilidad paper son capacidades separadas; ninguna habilita órdenes.

Todas las observaciones tienen `execution_eligible=false`. No se crean cartera, saldos, NAV, señales, trabajos de agentes ni ejecuciones. Salud/contratos P0 y `/?diagnostico=1` se conservan. Coste adicional de servicios: **0 EUR**.

## Uso local y pendientes

`python scripts/manage.py backend` y `python scripts/manage.py frontend`. GET `/api/data/quality` no consulta proveedores externos. GET `/api/data/sources/A01` consulta un único preset con cache/cuota/derechos. El mundo 3D sigue siendo la entrada. `DATA_PUBLIC_ENABLED=false` o `DATA_DISABLED_SOURCES=A01,A02` desactiva las consultas; claves opcionales solo en `.env`, nunca `VITE_*`. No configurar planes de pago.

`frontend/src/world/DataQuality.tsx` está preparado con contadores, cuatro filtros, estado real, pausa de consultas de la vista, selector de fuente, observaciones y procedencia. **No está montado en Sistemas ni revisado visualmente**, porque P1.F sigue por debajo de 30 FPS. P2.5 y el cierre integral P2.6 quedan pendientes de superar ese gate. No se declara P2 completada.

Para repetir pruebas: `python scripts/manage.py check`, `python scripts/manage.py audit`. Smoke de mantenimiento opcional: `.venv/Scripts/python.exe scripts/probe_p2.py --sources A01,A02`; no se ejecuta automáticamente al arrancar. No cuentan mocks ni documentación como conexiones.
