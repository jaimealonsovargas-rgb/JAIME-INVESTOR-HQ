# P2 — Plan técnico y checkpoints: fuentes, instrumentos y calidad de datos

> Investigación técnica consolidada 2026-10-14. **Especificación, no código ni prueba de acceso real.** Fuentes de verdad: tasks/P2_DATOS.md, docs/04_INSTRUMENTOS.md, docs/06_DATOS_APIS.md, docs/11_CONTRATOS.md, docs/12_ESQUEMA_DATOS.md, docs/13_SEGURIDAD.md y backend P0. Autorización del usuario: comenzar P2 en la misma ejecución de Codex que las correcciones finales de P1. **PAPER ONLY; coste adicional 0 EUR; STOP antes de P3.**

## 0. Resultado y límites

P2 construye una **tubería de datos reales verificables**, NO cartera, saldo de 10.000 EUR, trading, NAV, P&L, señales, agentes ni jobs. Flujo: proveedor GET-only → validación de respuesta → normalización y procedencia → cache/cuotas → selección por derechos y frescura → API local → Sistemas/Data Quality. Si no hay fuente, licencia, credencial o permiso: **NO DISPONIBLE con motivo**, nunca número inventado.

**Backend remoto publicado P0, no necesariamente LOCAL:** backend/app/contracts.py ya define Instrument, ProviderCapability, Quote y ProviderStatus (status literal NO DISPONIBLE); backend/app/providers.py devuelve UnavailableProvider; backend/app/database.py tiene InstrumentRecord JSON y revisión 0001_instruments; backend/app/main.py ofrece GET /health, /api/providers/status, /api/instruments y POST /api/orders denegado. frontend/src/api.ts exige phase=P0, trading_mode=PAPER_ONLY, orders_enabled=false. **Extender, no reemplazar ni romper P0; la versión LOCAL prevalece.**

Distinguir siempre: (a) cotización bursátil market_quote, (b) fundamental_fact SEC, (c) macro_series FRED, (d) fx_reference ECB, (e) yield_curve Treasury, (f) metadata de instrumento. Un fixing ECB NO es FX ejecutable; curva Treasury NO es cotización de un bono; IEX NO es SIP consolidado. Los datos demo de pruebas nunca entran en la DB de usuario.

## 1. Secuencia de checkpoints y gates

| Hito | Implementación mínima | Gate para continuar |
|---|---|---|
| **P2.0** Preflight y derechos | Inspección Git/local, matriz de proveedores, licencias, endpoints, límites, claves, arquitectura | Sin cambios destructivos ni accesos no autorizados |
| **P2.1** Instrumentos | Registry existente ampliado, alias de proveedores, capabilities independientes, migración Alembic | Identidad única, migración conservadora y tests |
| **P2.2** Observaciones | Contratos Decimal/UTC, fuente, feed, derechos, cache, TTL, stale, cuotas, errores | Sin números huérfanos ni cuotas ignoradas |
| **P2.3** Fuentes oficiales | SEC EDGAR, ECB y US Treasury GET-only con parsers/fixtures y opt-in de red | Fuentes etiquetadas; sin inventar precios |
| **P2.4** Proveedores opcionales | Alpaca PAPER/IEX, Trading 212 DEMO, Twelve Data Basic, FRED; GET-only, mocks sin claves | Ningún live host ni secreto filtrado |
| **P2.5** Orquestación/UI | Selección de observación por derechos/calidad; API tipada; panel Sistemas real | No romper oficina 3D ni inventar cartera |
| **P2.6** QA y cierre | Tests offline, integración, seguridad P0, auditoría, evidencia y STATUS | No declarar verificado lo que no se comprobó |

**Ejecución:** checkpoints secuenciales con commits y STATUS. Puede prepararse P2.0/P2.1 backend de manera aislada durante la revisión visual P1, pero **no integrar P2.5 hasta cerrar P1**. No detener P2 entera por ausencia de credenciales: adaptadores con fixtures y estado NO_CREDENTIALS; acceso real pendiente. Si Codex agota contexto, dejar el siguiente checkpoint exacto sin repetir trabajo.

## 2. P2.0 — preflight, derechos y contratos

1. Antes de tocar código: `git status --short`, `git log -5 --oneline`, `git branch --show-current`, `git diff --stat`. Preservar cambios locales de P1, nunca reset/clean/force ni sobrescribir.
2. Leer AGENTS.md, STATUS.md, tasks/P2_DATOS.md, este plan, docs/04_INSTRUMENTOS.md, docs/06_DATOS_APIS.md, docs/11_CONTRATOS.md, docs/13_SEGURIDAD.md y solo módulos afectados. No cargar todo el repo.
3. Crear **docs/P2_PROVIDERS_VERIFICACION.md** con tabla por proveedor: URL y método exactos, clase de dato, mercado, auth, cuota, latencia/retraso, licencia de acceso, **derechos de visualización, cache y redistribución**, fecha de comprobación, fuente oficial, estado de cuenta real (comprobado/no comprobado) y motivo. Documentación pública ≠ cuenta del usuario habilitada.
4. Reutilizar Python/FastAPI/Pydantic/SQLAlchemy/Alembic/SQLite/HTTP client existentes. No SDKs pesados ni cloud. Variables opcionales en .env backend, nunca VITE_*, logs, issues o prompts. Conexiones reales externas **opt-in** por configuración; sin claves no crashea.
5. Matriz de riesgos: URLs/redirects SSRF, copyright/licencias, retraso, cuotas, ambigüedad ticker, errores 401/403/429, SEC User-Agent y T212 demo vs live.

**Aceptación:** diseño concreto, matriz honesta, P0 seguro, sin peticiones de red imprevistas.

## 3. P2.1 — registro de instrumentos y capacidades

- Conservar Instrument, InstrumentRecord, InstrumentRegistry y GET /api/instruments; migración incremental `0002_*` o siguiente revisión LOCAL desde 0001, nunca recrear/borrar tablas existentes. Actualizar SCHEMA_VERSION/check_database y pruebas de migración. Evitar dos fuentes de verdad entre JSON y columnas normalizadas.
- Identidad canónica **symbol + venue + currency + asset_class**, más ISIN/CUSIP/FIGI **solo verificados**. Alias por proveedor con provider_symbol, venue, currency, instrument_id, vigencia y fuente. Ejemplo conceptual: ticker T212 no es ticker Alpaca. No resolver símbolos ambiguos por intuición.
- Cuatro capacidades **RESEARCH, VALUATION, INTERNAL_PAPER, BROKER_PAPER** independientes por instrumento/proveedor/feed: checked_at UTC, licencia/derechos, fuente documental, motivo, expires_at si procede. Mantener contrato ProviderCapability o versionar con compatibilidad. **BROKER_PAPER es una declaración de elegibilidad verificada, NO permiso de enviar órdenes**; no marcar true por simple presencia en catálogo.
- Búsqueda local paginada por símbolo/mercado/moneda/identificador; GET existente conserva semántica. Ningún seed ficticio en DB de producción.

**Gate:** tests de identidad compuesta, alias, capacidades sin evidencia, caducidad, búsqueda ambigua, clase bono/ETF/FX, migración con datos preexistentes, rollback en DB de test, 0 POST a bróker.

## 4. P2.2 — observaciones, calidad, cache y cuotas

**Contrato recomendado (ajustar al local sin duplicar Quote):**

| Campo | Requisito |
|---|---|
| observation_id, instrument_id o series_id, data_kind | Identidad y categoría explícitas |
| provider, feed, venue, source_url/source_ref | Procedencia verificable |
| observed_at UTC, received_at UTC, published_at opcional | No confundir hora del dato con descarga |
| currency, unit, bid/ask/last o value | Decimal como cadena JSON, no float monetario; nulos válidos |
| delay_seconds, stale_after, quality_flags | Retraso/frescura y advertencias |
| rights, display_allowed, storage_allowed | Derechos comprobados, no inferidos de precio 0 EUR |
| payload_hash SHA-256, error_code | Dedupe/trazabilidad sin guardar secretos |

Validación: UTC aware, ISO currency, no NaN/Inf, no precio negativo/cero donde inválido, bid≤ask si ambos, timestamp futuro absurdo rechazado, ausencia ≠ 0. Fuente sin hora no puede mostrarse como precio actual. Evitar que el mismo dato se etiquete realtime si es retrasado o de mercado cerrado.

**Cache:** clave provider+feed+instrument/series+parámetros+rights, TTL configurable **por feed y tipo**, invalidación y límite de tamaño, no cachear contenido sin derechos; datos stale solo etiquetados histórico y **no elegibles como precio de ejecución**. Cache no convierte IEX en SIP ni retrasado en realtime.

**Rate limits:** presupuesto por proveedor/endpoint, token bucket o ventana conservadora, `Retry-After` y headers oficiales, 429→RATE_LIMITED, reintentos GET limitados con jitter, circuit breaker ante fallos repetidos. Nada de polling masivo por panel/NPC. HTTP exclusivamente backend, GET, HTTPS y hosts exactos allowlisted; redirects fuera de allowlist bloqueados, timeout y límite de tamaño, sin SSRF.

**Estados tipados:** AVAILABLE_VERIFIED, DELAYED, STALE, NO_DATA, NO_CREDENTIALS, AUTH_FAILED, RATE_LIMITED, RIGHTS_RESTRICTED, OFFLINE, TIMEOUT, INVALID_PAYLOAD, ERROR, NOT_IMPLEMENTED. Exponer estado y motivo en español; no declarar AVAILABLE por existir URL.

**Gate:** fixtures HTTP mock, Decimal/UTC, bid-ask, stale, cache hit/miss/expiry, 401/403/429/500/timeout, reloj simulado, cuota, no fuga de headers privados.

## 5. P2.3 — fuentes oficiales gratuitas

| Fuente | Adaptador read-only y tratamiento | Restricciones |
|---|---|---|
| **SEC EDGAR** | GET `https://data.sec.gov/submissions/CIK##########.json` y `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`; filings y fundamentales US; CIK de 10 dígitos, taxonomía/unidades/periodos/revisiones | Sin clave; **User-Agent identificable con contacto real configurado**; fair access oficial máximo 10 req/s, utilizar margen conservador; CORS SEC no permite navegador directo; no es feed de precios |
| **ECB SDMX** | GET `https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A` (ejemplo oficial); parser SDMX/CSV, cotización EUR/otra divisa, fechas y revisiones | FX **de referencia**, no spot ejecutable; declarar unidades/par; Accept MIME específico |
| **US Treasury** | Daily Treasury Rates, descarga oficial CSV/XML; curva par nominal/real y bill rates, tenor, fecha, convención y tipo de serie | Curva **no equivale** a precio OTC de bono; no mezclar descuento de letras y cupón equivalente; verificar URL exacta en página antes de fijarla |

Fuentes oficiales: https://www.sec.gov/search-filings/edgar-application-programming-interfaces ; https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data ; https://data.ecb.europa.eu/help/api/data ; https://data.ecb.europa.eu/help/api/content-negotiation ; https://home.treasury.gov/resource-center/data-chart-center/interest-rates .

**Implementar parsers con fixtures etiquetados y tests sin red**. Solo ejecutar smoke tests de red pública si opt-in y condiciones comprobadas; registrar resultado, hora y fuente. No inventar contacto SEC ni afirmar conectividad sin llamada real. Revisar derechos de almacenamiento/visualización de cada fuente antes de persistir valores.

**Gate:** CIK, unidades XBRL, ECB FX reference, Treasury tenor/fecha/serie, 304 y errores, formato inválido, no confusión de instrumentos.

## 6. P2.4 — proveedores gratuitos opcionales, SOLO GET

| Proveedor | Hechos de documentación oficial y decisión |
|---|---|
| **Alpaca Market Data / PAPER** | Basic gratuito: **IEX en tiempo real para acciones/ETF US, NO SIP consolidado**; documentación oficial indica 200 llamadas históricas/min y restricciones de datos recientes. Host market data `https://data.alpaca.markets`; cuenta paper `https://paper-api.alpaca.markets`. Cliente GET-only con claves backend, feed IEX explícito, sin prometer cobertura universal ni acceso de la cuenta. |
| **Trading 212 DEMO API v0** | Beta, host `https://demo.trading212.com/api/v0`; disponible según documentación para Invest/Stocks ISA; GET de metadata, account/positions; cuotas por endpoint y headers `x-ratelimit-*`. Preferir catálogo en P2; saldos/posiciones demo no son MASTER ni NAV P3. Nunca live, POST/DELETE ni seguir nextPagePath a otro host. |
| **Twelve Data Basic** | Página oficial: **8 créditos API/min, 800/día**; cada endpoint puede costar varios créditos, 429 al agotarlos; headers `api-credits-used`/`api-credits-left`, endpoint `/api_usage` consume crédito. Basic indica **internal non-display usage**: no asumir derecho a enseñar cotizaciones en UI. **display_allowed=false por defecto** hasta comprobar permiso concreto. Cache y no polling excesivo. |
| **FRED** | Series macro, API key registrada (v1 parámetro api_key, v2 Bearer); sin clave → NO_CREDENTIALS. No es feed de precio. Clave solo backend, sin URLs de clave en logs. |

Fuentes: https://docs.alpaca.markets/us/docs/about-market-data-api ; https://docs.alpaca.markets/us/docs/market-data-faq ; https://docs.trading212.com/api/positions ; https://docs.trading212.com/api/accounts ; https://twelvedata.com/pricing ; https://support.twelvedata.com/en/articles/5615854-credits ; https://support.twelvedata.com/en/articles/5713553-control-over-api-usage ; https://fred.stlouisfed.org/docs/api/api_key.html .

**No se ha verificado** cuenta, residencia, credenciales, permiso de API, derechos de display ni límites efectivos del usuario. Crear adaptadores con HTTP mock, sin conectarlos realmente si falta autorización/clave. P0 paper-host allowlist sigue estricta; data-host allowlist separada y GET-only.

**Gate:** auth en backend, no claves en frontend/logs, IEX vs SIP, paginación T212 sin host live, 429 y headers, cuotas, derechos, sin métodos de órdenes.

## 7. P2.5 — selección, API y UX de Sistemas

- Servicio de selección: usar solo feeds con capability comprobada, instrumento+venue+moneda coincidentes, clase de dato correcta, derechos suficientes y frescura adecuada; registrar `selection_reason`. Si ninguno: NO_DATA / STALE / RIGHTS_RESTRICTED, no estimar ni hacer fallback silencioso.
- Conservar GET /api/instruments y GET /api/providers/status; evolucionar ProviderStatus (actual literal NO DISPONIBLE) sin romper validadores. GET /health sigue `PAPER_ONLY` y `orders_enabled=false`. **No cambiar phase=P0 a P2 unilateralmente**, frontend lo valida de forma estricta; añadir campo opcional data_phase o endpoint separado, con tests de compatibilidad.
- Si se añaden GET /api/quotes, /api/data/series o /api/data/quality, respuesta Pydantic/TS validada con proveedor, feed, hora, unidad/divisa, retraso, calidad y derechos; **si display no autorizado, no incluir valor en payload visible**.
- Panel Sistemas/Data Quality: proveedor, estado real, cuota/latencia solo si medida, último check, razón, feed, licencia, stale, derechos. Opcional ficha de instrumento con metadatos P2 reales en Research/Trading, sin habilitar P3/P4/P6. No crear dashboard inicial ni activar NPC IA.
- Deduplicación y refetch controlado con TanStack Query; no un poller por monitor o NPC; backend offline no rompe oficina 3D.

**Gate:** panel real con respuestas tipadas, no datos inventados, derechos/latencia/fecha honestos, P1 3D estable, modal accesible y tests de frontend.

## 8. P2.6 — QA, evidencia y entrega

1. Alembic incremental desde 0001 con instrumentos existentes y DB vacía; no drop ni seed ficticio; rollback en DB de test.
2. Contratos Decimal, UTC, fuente, moneda/unidad, delay, rights, display, hash y quality flags; 0 no sustituye ausencia.
3. Mock HTTP: 200/204/304/400/401/403/404/429/500, timeout, desconexión, payload corrupto, timestamp ausente, cuota agotada; **no usar red para tests**.
4. SSRF, redirects, allowlists, GET-only, no host live, secretos en .env backend, no logs de auth; paper guard y POST /api/orders 403.
5. Frontend: nueve departamentos intactos, Sistemas muestra fuentes y motivos, backend desconectado sin crash, sin P&L/NAV/jobs ficticios, sin caída significativa por polling.
6. Ejecutar y anotar resultados REALES de `python scripts/manage.py check`, `python scripts/manage.py audit`, `git diff --check`, pruebas de navegador y benchmark de P1 cuando disponible.
7. Documentar matriz de proveedores en docs/P2_PROVIDERS_VERIFICACION.md, evidencias en docs/evidencias/P2/ si procede, commits por gate y STATUS.md con completado/pendiente/bloqueos. **STOP antes de P3**.

## 9. Mapa de archivos para Codex (no duplicar arquitectura local)

| Ruta | Acción |
|---|---|
| backend/app/contracts.py | Extender Quote, ProviderCapability, ProviderStatus; Observation/DataQuality si faltan |
| backend/app/database.py y backend/migrations/versions/0002_*.py | Registro, aliases, capabilities, observaciones, cache/cuotas y migración |
| backend/app/providers.py | Reutilizar protocolo P0; separar adaptadores GET-only solo si hace falta |
| backend/app/config.py | Claves opcionales backend, read-only opt-in, allowlist exacta |
| backend/app/main.py | Endpoints GET P2, Pydantic, P0 intacto |
| backend/app/security.py | Mantener bloqueo órdenes y separación host paper/data |
| backend/tests/ | Dominio, HTTP mock, permisos, cuota, migración, seguridad |
| frontend/src/api.ts + panel Sistemas local | Validación TS, fuentes/estado reales, sin dashboard de inicio |
| docs/P2_PROVIDERS_VERIFICACION.md + STATUS.md | Evidencia verificable y handoff |

**Regla de ahorro de tokens:** inspeccionar → diff mínimo → tests → gate → STATUS → siguiente. No leer P3–P7 salvo contrato puntual. No rehacer el mundo 3D. Guía de coordinación: [PLAN_EJECUCION_P1_P2.md](PLAN_EJECUCION_P1_P2.md).