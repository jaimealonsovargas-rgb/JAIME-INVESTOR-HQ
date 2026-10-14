# P2 · infraestructura y conexiones verificadas

Entrega local del 2026-10-15. **31 proveedores candidatos / 35 modalidades**: las 34 del catálogo original más RSS oficial BCE. **33 adaptadores útiles / 29 proveedores implementados**. No hay clases vacías contadas como conectores.

**18 modalidades / 17 proveedores** con HTTP real y respuesta válida. **12 fuentes frescas utilizables / 11 proveedores** en la última prueba del panel (23:27 UTC); son estados temporales, no una garantía de disponibilidad futura. A las 23:23 UTC eran 11 fuentes: el RSS había caducado y se actualizó mediante una consulta manual comprobada. Coinbase y CoinPaprika funcionaron pero sus precios ya caducaron; no cuentan como utilizables ahora. Cuatro restricciones de display: ESMA, Kraken, Binance y CoinGecko público. Trece modalidades sin credenciales; SEC sin contacto real. Finnhub/Nasdaq: PLAN_REQUIRED, sin endpoint gratuito útil y derechos confirmados, no implementados.

Proveedores realmente comprobados: BCE (referencia FX y RSS), Banco de España, INE, Eurostat, OCDE, Banco Mundial, BIS, Treasury, BLS v1, FMI DataMapper, ESMA FIRDS (índice de archivos), Kraken, Binance market-data-only, CoinPaprika, CoinGecko público, Coinbase y OpenFIGI público. **GDELT no cuenta:** timeout en tres intentos acotados, incluido el smoke final. La ausencia de una fuente no detuvo las demás.

## Evidencias

- `smoke-real*.json`: HTTP real, fecha UTC, latencia, estado y normalización; nunca mocks ni documentación contados como conexión. Los feeds personales/restringidos no redistribuyen valores en evidencias. El último resultado por modalidad prevalece; no se suman archivos.
- [Matriz de proveedores](../../P2_PROVIDERS_VERIFICACION.md): 35 modalidades, endpoints, auth, cuotas, derechos de acceso/display/cache/redistribución y última prueba.
- `seguridad-y-calidad-entrega.json`: health P0, PAPER_ONLY, schema 0002_data, órdenes deshabilitadas y POST local LIVE negativo 403. No se envió ninguna orden externa.
- `navegador-data-quality-entrega.json`: **35 filas**, filtros FX/ES/STATISTICS/noticias, fuente sin credenciales deshabilitada sin petición, pausa sin consulta automática, reanudación, RSS real y unidad BCE USD/EUR.
- `backend-offline-real.json`: backend propio realmente detenido, sin mocks; Sistemas y videowall NO DISPONIBLE, movimiento recuperado y foco CANVAS al cerrar. Capturas `backend-real-desconectado.png` y `videowall-backend-desconectado.png`.
- `sistemas-data-quality.png`, `sistemas-noticias.png`, `videowall-movil.png`: capturas auténticas del navegador. El videowall completo y sus nueve módulos están en [Sims](../P1_SIMS/README.md).
- [Auditoría de terceros](../../INTEGRACIONES_TERCEROS_VERIFICACION.md): pins, licencias, SBOM, doctor RSS, 30 presets Vibe exclusivamente METADATA_ONLY y Liquid bloqueado. Directorio `integraciones/` conserva resultados iniciales y finales, incluidos los negativos.

## Infraestructura

HTTPS con endpoints cerrados, TLS, DNS público, sin redirects, sin URLs arbitrarias del frontend, límite de cuerpo y tiempos de espera. GET por defecto; solo los POST read-only acotados OpenFIGI/BLS v2. Ningún transporte a cuentas, órdenes o transferencias de bróker/exchange. Binance solo `data-api.binance.vision`, Alpaca solo market data IEX y Trading 212 solo catálogo DEMO.

JSON/CSV/SDMX/XML/XBRL y RSS; Decimal desde texto, UTC, periodo separado de publicación, fuente/feed/venue/unidad/hash/derechos. XML con DTD/entidades o bytes nulos rechazado. Cache SQLite con identidad de parámetros/derechos y TTL por feed, cuotas compartidas por proveedor, Retry-After, errores 401/403/429/timeout, circuit breaker y sin reintentos automáticos. Fallback solo con semántica coincidente; no convierte fixing en spot, IEX en SIP ni curva en bono.

Migración incremental 0002_data aplicada tras backup consistente. **98 instrumentos/series reales**, sin seeds. Identidad/aliases y capacidades de investigación, valoración y elegibilidad paper separadas; ningún ISIN/FIGI/divisa adivinado. No se promete cobertura amplia de acciones, ETF o bonos individuales sin claves/identificadores verificables. Todas las observaciones son `execution_eligible=false`.

Sistemas monta Data Quality con siete contadores separados, filtros por activo/país/mercado/tipo, fuente/feed, comprobación original, cuota, latencia medida y derechos. Seleccionar una fuente consulta un único preset; pausa evita nuevas consultas automáticas. La consulta local de calidad y el resumen HQ no consultan proveedores externos. Backend offline no bloquea caminar. No hay cartera, NAV, posiciones, trades ni trabajos de agentes inventados.

## Comprobación local

Ejecutar en dos terminales `python scripts/manage.py backend` y `python scripts/manage.py frontend`; abrir `http://127.0.0.1:5173/`. La oficina 3D es la entrada. Flechas hasta el agente de Sistemas; Esc para cerrar. «Ver centro de control» abre el resumen global. `/?diagnostico=1` conserva P0.

`DATA_PUBLIC_ENABLED=false` o `DATA_DISABLED_SOURCES=A01,A02` desactiva consultas. `AGENT_REACH_PUBLIC_ENABLED=true` activa solo RSS BCE auditado; por defecto false en `.env.example`. Claves opcionales solo en `.env`, nunca VITE_*; sin claves los adaptadores muestran NO_CREDENTIALS. No signup ni compras.

Pruebas: `python scripts/manage.py check`, `python scripts/manage.py audit`. Smoke de mantenimiento opcional: `.venv/Scripts/python.exe scripts/probe_p2.py --sources A01,A02`; nunca automático al arrancar. Coste adicional de servicios **0 EUR**, PAPER ONLY. STOP antes de P3.
