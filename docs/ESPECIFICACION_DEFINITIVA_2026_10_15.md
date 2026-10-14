# JAIME INVESTOR HQ — ESPECIFICACIÓN DEFINITIVA Y RESOLUCIÓN DE REQUISITOS

**Fecha:** 2026-10-15. **Naturaleza:** diseño aprobado y contrato de implementación, NO código ni conexiones verificadas.
**Misión:** plataforma local-first de investigación y gestión de una cartera de **10.000 EUR virtuales** con datos de mercado **reales y trazables**, decisiones multiagente, compras/ventas **PAPER**, seguimiento y evaluación. **Solo el dinero y los fills son simulados**, nunca las fuentes o los resultados. **Coste adicional 0 EUR; no trading live.**

**Precedencia:** seguridad PAPER ONLY/0 EUR > últimas decisiones del usuario (oficina Sims + videowall + 16 NPC + 30 roles) > este documento > [plan maestro](PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md) > [planes P1/P2](PLAN_EJECUCION_P1_P2.md) > instrucciones históricas. **Autorización actual P1 correctivo + P2 completo; STOP antes de P3**. Especificar P3–P7 no significa ejecutarlas.

## 1. Imagen aprobada: incorporarla de verdad

**PRINCIPAL:** `assets/reference_images/JAIME_HQ_SIMS_VIDEOWALL_APROBADA.png` (PNG 1672×941; SHA-256 `4e07c5f1ea91b598ce8e3fcbcc1e73da6332b64006f8c03a21df7fa7a515ef92`), generada el 2026-10-14 después de pedir una pantalla enorme. **SECUNDARIA:** `assets/reference_images/JAIME_HQ_SIMS_BASE.png` (1672×941; SHA-256 `69101f7a18a0d48908b3e3a060e64ffeb1c89a2a975ccb085ac9bdf6dfd83347`), concepto anterior estilo Sims.

**Entrega honesta:** estos PNG **no están todavía en GitHub**; los originales están incluidos en el **ZIP de handoff de esta conversación**. Codex debe copiarlos del ZIP a `assets/reference_images/`, comprobar hash y versionarlos. No decir que están en el repo hasta verificar el blob. El SVG `assets/PLANO_SIMS_VIDEOWALL.svg` es **solo un plano esquemático**, NO la imagen aprobada. [Manifiesto exacto](../assets/REFERENCIA_APROBADA_MANIFIESTO.md).

**Copiar del render:** composición luminosa/isométrica Los Sims, vestíbulo frontal, recepción central, comité visible, oficinas a los lados, madera clara/marfil, plantas, mesas con varios monitores, NPC profesionales, **VIDEOWALL OSCURO GIGANTE DE EXTREMO A EXTREMO EN PARED SUPERIOR**. No copiar literalmente cifras, P&L, noticias, gráficos, número de salas o barreras de cristal. La imagen contiene rótulos Macro/Fundamental/ESG que deben tratarse como pods visuales de 9 departamentos, no como 13 departamentos backend. Recepción sin sofás, pasillos sin cristales obstructivos.

## 2. Experiencia 3D P1: decisiones finales y razones

- **Vista principal:** isométrica/3/4 elevada **tipo Los Sims**, seguimiento suave, orientación fija, paredes/techos cutaway. No cámara detrás del avatar ni OrbitControls/mouse-look. Vista general opcional.
- **Controles:** SOLO flechas ↑ arriba de pantalla, ↓ abajo, ← izquierda, → derecha. Traslación relativa a pantalla en plano XZ, diagonales normalizadas, delta-time. El avatar gira automáticamente hacia la dirección de movimiento. No flechas para girar sobre sí mismo, no WASD.
- **Escenario:** 9 departamentos reales y 9 monitores/paneles existentes: Recepción, Trading, Research, Quant, Riesgos, Ejecución, Comité, Performance, Sistemas. Layout reorganizable para parecerse al render sin romper IDs. Macro/Fundamental/ESG/Legal como pods visuales dentro de las nueve salas. Performance y Sistemas con puestos y recorridos funcionales.
- **NPC:** exactamente **16 humanos profesionales sentados** como objetivo inicial: Recepción 1, Trading 3, Research 3, Quant 2, Riesgos 2, Ejecución 1, Comité 1, Performance 1, Sistemas 2. 9 principales + 7 secundarios. Animaciones de teclear/leer ambientales, NO evidencia de jobs IA. LOD, instancing, sombras limitadas.
- **Interacción:** 9 paneles DOM abiertos automáticamente al acercarse al **NPC principal de su sala**, no al monitor. Entrada inicial ~2,0m y rearme ~2,8m, comprobación de sala/oclusiones, Escape cierra, no reapertura inmediata; secundarios no disparan otro panel.
- **Rendimiento:** PC Windows 11, Intel Core 5 120U, 16GB, Intel Graphics, 1920×1080; objetivo 45–60 FPS, mínimo sostenido 30, **medir** con escena activa. DPR adaptativo, LOD, draw calls, cutaway, texturas con licencia. Capturas **reales** desde navegador, no renders conceptuales.

**Por qué 16 NPC y 30 agentes:** los 16 hacen creíble el espacio y pueden renderizarse con presupuesto Intel; los 30 son roles lógicos de análisis que no consumen GPU ni LLM si están inactivos. **Nunca** crear 30 LLM residentes ni representar animaciones ambientales como trabajo financiero real.

## 3. Videowall enorme — centro de control y fuente de verdad

La pantalla superior debe dominar visualmente la planta, ser legible y abrir un **fullscreen DOM** con botón independiente de los NPC. Los paneles de cada sala siguen existiendo. Módulos:
1. Marca JAIME, etiqueta permanente **SIMULACIÓN · PAPER ONLY**, estado/hora.
2. **Cartera MASTER EUR P3:** NAV, caja, P&L realizado/no realizado, rentabilidad diaria/acumulada, curva equity y drawdown.
3. **Posiciones P3:** top holdings, pesos, sectores, divisas, países, concentración.
4. **Operaciones P6:** propuestas, órdenes paper, fills/rechazos, pendientes, costes y reconciliación.
5. **Mercados P2:** acciones/ETFs, índices, FX, tipos/curvas, macro, crédito, commodities y cripto **solo si fuente y derechos lo permiten**, con venue, moneda, retraso, timestamp y procedencia.
6. **Noticias P2:** titulares con URL, autor, fecha, fuente, idioma y nivel de confirmación; Agent Reach público cuando auditado.
7. **Riesgo/comité P5:** alertas, límites, concentración, veto y explicaciones.
8. **Agentes/sistemas P2/P4:** proveedores, stale, cuotas, jobs reales, errores y último refresh.

**Sin falsificaciones:** P1 muestra placeholders honestos; P2 activa solo mercados/noticias con datos válidos; P3 crea ledger una vez; P4 jobs; P5 riesgo; P6 operaciones. Los números de la imagen generada son decorativos y NO se copian. `NAV=null` no significa `NAV=0`; «Sin operaciones paper» solo si existe ledger consultado; si no, «Pendiente de P6». Fuente/derechos/fecha obligatorios; stale/offline visibles. React DOM para texto y polling con TTL, no 60 peticiones/segundo. Propuesta de endpoint solo lectura `GET /api/hq/overview` con secciones `id,status,phase_required,as_of_utc,source,currency,value,items,quality,rights,reason`. No romper `/health` ni contrato P0.

## 4. Máxima conectividad P2, sin scraping ni promesas falsas

El usuario quiere el **máximo posible de páginas/fuentes**, pero el objetivo profesional es **máximo de fuentes realmente utilizables**, no 30 stubs. Catálogo existente: **~31 proveedores distintos / 34 modalidades candidatas**, no 31 conexiones comprobadas. [Catálogo](P2_CATALOGO_MAXIMO_FUENTES.md), [checkpoints](PLAN_P2_CHECKPOINTS.md).

- **P2.3a:** BCE/ECB, Banco de España, INE, Eurostat, OCDE.
- **P2.3b:** Banco Mundial, BIS, US Treasury, SEC EDGAR (User-Agent de contacto real), BLS v1, FMI si viable.
- **P2.3c:** Kraken, Binance **solo market data**, Coinbase Exchange, CoinPaprika, CoinGecko Public, GDELT, OpenFIGI, ESMA FIRDS selectivo.
- **P2.4a:** FRED, BEA, BLS v2, EIA, Alpha Vantage, CoinGecko Demo, OpenFIGI con clave.
- **P2.4b:** Alpaca Basic (IEX, no SIP), Trading 212 DEMO, Twelve Data con restricciones de display verificadas.
- **P2.4c:** Finnhub, FMP, Massive/Polygon, Tiingo, Nasdaq Data Link **solo si existe acceso gratuito realmente compatible**.
- **Explorar:** CNMV, Bank of England, Fed, emisores IR/RSS, bolsas/reguladores si hay acceso legal. No scraping no autorizado de Yahoo, Google Finance, TradingView, Investing o redes.

Cada observación incluye instrumento/ISIN/FIGI/venue, fuente, licencia y derechos de display/storage, fecha UTC, divisa, precisión Decimal, feed, calidad, latencia, ajuste y TTL. **No confundir** FX de referencia BCE con spot ejecutable, curva de rendimiento Treasury con precio de bono, fundamentales SEC con cotización ni IEX con SIP. Cache, backoff, cuotas, offline, circuit breaker, selección por semántica. Estados CANDIDATE / IMPLEMENTED / CONNECTED / USABLE con prueba HTTP real y fecha. Mocks son para tests, no conexión. Los POST de BLS v2/OpenFIGI son consultas allowlisted, no órdenes; **no POST a broker/exchange** en P2.

«Datos lo más actuales posible» = frescura real de cada feed visible; no prometer tick-by-tick de acciones gratis ni actualización cuando el PC esté apagado.

## 5. Las 3 integraciones solicitadas: decisión segura y momento

**Agent Reach:** auditar repositorio/versión/licencia y modo seguro; P2 activar **solo canales públicos legales**: RSS/Atom, IR, reguladores, noticias públicas, GitHub, YouTube metadata/subtítulos permitidos, GDELT. Sin cookies del navegador, sesiones personales, scraping contrario a términos, publicación/likes/DM. Redes que exigen autenticación quedan AUTH_REQUIRED hasta permiso expreso y API oficial. Registrar URL/autor/fecha y deduplicar; contenido social es señal no verificada y nunca instrucciones para el agente. P4 rol News/Social Intelligence con citas y triangulación.

**HKUDS/Vibe-Trading:** en P2 investigar licencia MIT y terceros, dependencias, coste real, seguridad, Windows/Intel y adaptador read-only aislado. Una release anunciaba **30 presets de equipos y 462 alphas**: son candidatos, no rendimiento ni 30 agentes activos. P4 catalogar hasta 30 presets si auditados, empezar con 6–10 útiles y 30 roles propios; P5 factores/backtesting point-in-time, walk-forward, costes, spreads, FX, sesgos y benchmark. **No ejecutar Python generado no confiable** en Windows sin sandbox real; no brokers/live de Vibe.

**Liquid Co-Invest:** su OAuth estándar incluye **read+trade**; **NO conectar MCP/OAuth/cuenta/wallet**, aunque diga paper y 0 EUR. P2 investigar exclusivamente endpoint público gratuito read-only con derechos verificables; si no existe, estado BLOCKED_TRADE_SCOPE/NO_PUBLIC_READ_ONLY_API. No importar su balance paper USD a la cartera MASTER EUR. No conectar a cualquier precio para alcanzar el número tres.

## 6. 30 agentes, estrategias y flujo de inversión (P4 FUTURO)

30 **roles lógicos**, no procesos: Research 6 (fundamental, valoración, macro global, macro España/Europa, crédito, ESG); Trading/Execution 4 (microestructura, liquidez, planificación paper, reconciliación); Quant 5 (momentum, value/quality, reversión, volatilidad/régimen, optimización); Risk 5 (mercado, crédito, liquidez, concentración, compliance/kill switch); Performance 3 (NAV/atribución, benchmark/FX, reporting/postmortem); Systems/Data 4 (calidad, proveedores, noticias/social, observabilidad/seguridad); Committee 3 (CIO, Bull, Bear). [Detalle](09_AGENTES.md).

Cada rol tiene `role_id`, herramientas permitidas, input/output schema, evidencia, dependencias, costes, timeout, versión, job_id, errores y cancelación. Scheduler local con 1 inferencia LLM gratuita local por defecto **solo si instalada y comprobada**, 2 jobs CPU cuantitativos, 4 fetches ligeros. Si no hay LLM gratuito viable, análisis deterministas y roles LLM NO DISPONIBLES; nunca comprar tokens automáticamente.

**Estrategias a estudiar:** momentum/trend, value/quality, mean reversion, regímenes macro/volatilidad, asignación factorial, duración/curva (analítica), rotación, cash defensivo, rebalanceo, eventos fundamentales y noticias confirmadas. Cada hipótesis exige cobertura, universo, horizonte, señales point-in-time, costes, benchmark, riesgo, tests fuera de muestra y motivo de no operar. No prometer alfa.

**Flujo:** P2 datos → Data Quality → Research/Quant/News → crítica Bull/Bear → Comité → **riesgo determinista con veto** → propuesta paper → P6 ejecución paper → P3 ledger → Performance/postmortem. Ningún LLM crea dinero, edita fills, elimina riesgo ni envía órdenes live.

## 7. Cartera, instrumentos, ejecución y evaluación (P3/P5/P6 FUTUROS)

**P3:** ledger MASTER **una sola semilla de 10.000,00 EUR ficticios**, Decimal, UTC, eventos append-only (cash, reservas, fills, fees, FX, dividendos, cupones, splits, ajustes), NAV, P&L, atribución, reconciliación, backups. Las cuentas demo Alpaca/T212 son separadas, no se suman. **P1/P2 no crean saldo/NAV/órdenes**.

**Cobertura de investigación:** acciones, ETFs, bonos, tipos, FX, materias primas, cripto, macro/noticias según feeds. **Universo ejecutable inicial P6:** acciones líquidas y ETFs compatibles con el simulador, más efectivo EUR; sin apalancamiento, cortos, opciones, futuros, CFD, perpetuos ni derivados. Bonos individuales/cripto solo si existe valoración/fills/costes/derechos robustos y autorización futura. Un dato disponible no implica instrumento negociable.

**P5:** límites parametrizados y conservadores por posición/sector/divisa/liquidez/rotación, stop de pérdida y drawdown, controles de spread/volatilidad/stale, kill switch y veto determinista. No imponer porcentajes arbitrarios sin validación. Backtests sin lookahead/survivorship, walk-forward, benchmark, costes, slippage, TWR/MWR/Sharpe/Sortino/max DD/turnover con muestras suficientes.

**P6:** simulación de compra/venta con **precio de mercado verificable**, horario, bid/ask, spread, slippage, comisiones, lotes, divisa y liquidez; los fills son estimaciones paper, no ejecuciones bursátiles. Alpaca PAPER/T212 DEMO solo con credenciales/hosts paper aislados y gate de seguridad. Idempotencia, estados, reconciliación; UNKNOWN no se reintenta a ciegas. En P1/P2 `/api/orders` permanece 403 y `orders_enabled=false`.

**15 días de prueba:** mostrar qué habría ocurrido con dinero real, pero **15 días positivos no prueban robustez**; medir benchmark, volatilidad, drawdown, costes, datos ausentes y tamaño muestral. **NUNCA pasar automáticamente a live** por resultados, por una flag o por pedirlo al agente. Una eventual fase real necesitaría nuevo mandato, revisión legal y arquitectura independiente.

## 8. Tecnología, coste, privacidad y operación

Stack existente **React/TS/Vite/R3F/Three + FastAPI/SQLite/Alembic**, local-first, Windows/VS Code/Codex. No reconstruir proyecto ni sobrescribir código LOCAL no subido. Dependencias/modelos/3D con licencia y atribución; no pagar servicios, servidores, modelos ni cuotas. Claves solo backend `.env` ignorado; no en frontend/GitHub/prompts/logs/capturas. Allowlists de dominios/rutas/métodos, prevención SSRF/prompt injection, límites de red/CPU/memoria, auditoría de dependencias, sandbox real para código de terceros o runner deshabilitado.

No afirmar vigilancia 24/7 si el PC está apagado. La app puede trabajar mientras el equipo esté encendido y los feeds lo permitan; no instalar servicios en segundo plano no autorizados. Mantener guardas P0 PAPER ONLY, tests y datos de diagnóstico.

## 9. Fases, límites y aceptación

| Fase | Autorizada ahora | Qué debe comprobarse |
|---|---|---|
| P1.S0 | SÍ | Git LOCAL intacto, referencia PNG real y hash, baseline |
| P1.S1 | SÍ | Sims isométrico, 9 salas, videowall enorme, sin números falsos |
| P1.S2 | SÍ | Flechas screen-relative, avatar/cámara/colisiones |
| P1.S3 | SÍ | 16 NPC sentados, 9 paneles por NPC principal/histéresis |
| P1.S4 | SÍ | Capturas navegador, FPS Intel, pulido, QA |
| P2.0–2.2 | SÍ | Registry, derechos, instrumentos, normalización/cache/cuotas |
| P2.3a/b/c | SÍ | Fuentes públicas máximas y Agent Reach público auditado |
| P2.4a/b/c | SÍ | Gratis con clave opcional; Vibe auditado; Liquid sin OAuth |
| P2.5–2.6 | SÍ | Data Quality/videowall mercados/noticias; pruebas/STATUS |
| P3 | **NO** | Ledger 10.000 EUR, cartera/NAV |
| P4 | **NO** | 30 roles/jobs y presets/factores Vibe |
| P5 | **NO** | Riesgo/comité/backtest y veto |
| P6 | **NO** | Órdenes y fills exclusivamente paper |
| P7 | **NO** | QA integral/seguridad/instalación |

**P1+P2 pueden ejecutarse en la misma sesión de Codex por checkpoints; P2 backend aislado en paralelo si no interfiere, UI P2 tras estabilizar P1.** Pruebas: `python scripts/manage.py check`, `python scripts/manage.py audit`, `git diff --check`, build frontend/backend, unit/integration/E2E, P0 security, red offline/429/403, fuentes reales, screenshot y FPS. **No declarar resultados sin ejecutarlos**. Commits separados, `STATUS.md` con qué está terminado/bloqueado y por qué, evidencia y siguiente paso. **STOP antes de P3**.

## 10. Handoff y referencias

**Leer primero:** `AGENTS.md` → `STATUS.md` → este documento → [plan maestro](PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md) → [prompt Codex completo](PROMPT_CODEX_EJECUCION_COMPLETA_P1_P2.md) → P1/P2 checkpoints. No cargar todos los documentos en cada turno.

**Referencia visual:** PNG original principal y secundario del ZIP de handoff, [manifiesto de hashes](../assets/REFERENCIA_APROBADA_MANIFIESTO.md). [Plano SVG secundario](../assets/PLANO_SIMS_VIDEOWALL.svg).

**Planes existentes:** [P1+P2](PLAN_EJECUCION_P1_P2.md), [P2 detallado](PLAN_P2_CHECKPOINTS.md), [fuentes máximas](P2_CATALOGO_MAXIMO_FUENTES.md), [integraciones externas](INTEGRACIONES_TERCEROS_VERIFICACION.md), [ledger](07_CARTERA_LEDGER.md), [agentes](09_AGENTES.md), [quant](10_CUANTITATIVO.md), [aceptación](16_TESTS_ACEPTACION.md). Issues #1, #2 y #3.

**Regla final:** cuando el render contradiga el producto (rótulos extra, cristales bloqueantes, precios falsos), mantener la estética del render pero cumplir las reglas de producto. No volver a preguntar decisiones ya aprobadas; solo bloquear por pérdida de código, permisos, licencia o coste.
