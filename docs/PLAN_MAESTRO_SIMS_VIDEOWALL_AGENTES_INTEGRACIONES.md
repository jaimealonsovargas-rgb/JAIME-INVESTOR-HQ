# PLAN MAESTRO — JAIME INVESTOR HQ · Oficina estilo Los Sims, videowall, 16 NPC, 30 agentes e integraciones

> **Aprobación de diseño por el usuario: 2026-10-14.** Le gusta la referencia **minimalista, tipo Los Sims, vista isométrica elevada** y solicita una **pantalla panorámica ENORME en la parte superior** con cartera, operaciones, mercados y noticias. También pidió decidir número de bots/agentes y estudiar la integración de **Liquid Co-Invest, Agent Reach y HKUDS/Vibe-Trading** en el momento apropiado, con **0 EUR y PAPER ONLY**. **Este archivo es una especificación para Codex, NO una implementación ni prueba de conectividad.** Sustituye los requisitos anteriores de cámara «detrás del avatar» y giro con flechas cuando sean incompatibles. **La autorización de ejecución actualmente vigente sigue siendo corregir P1 + completar P2; STOP antes de P3** hasta una autorización posterior. Este plan define P3–P7 para no rehacer arquitectura.

## 0. Decisiones ejecutivas (no abrir debate de diseño de nuevo)

1. **Vista principal:** isométrica/3/4 elevada estilo Los Sims, cámara estable con seguimiento suave del avatar; **NO tercera persona a la espalda**. Personaje visible de cuerpo entero y recorrido accesible. Mantener opción de vista global de planta; cámara manual no necesaria.
2. **Controles:** solo flechas ↑ arriba de pantalla / ↓ abajo / ← izquierda / → derecha, movimiento **screen-relative**, diagonales normalizadas y velocidad por delta. **No** flechas para girar el rumbo, **no** WASD, ratón ni OrbitControls para caminar; avatar gira **automáticamente hacia la dirección del desplazamiento**. Al abrir panel se desactiva movimiento; Escape cierra. Sin rotaciones de cámara que inviertan direcciones.
3. **Escenografía:** una planta, diseño limpio premium, **más Los Sims y menos render hiperrealista**, paleta marfil/roble claro/azul marino/plantas/metal discreto, iluminación cálida, paredes interiores recortables/cutaway para que el jugador vea siempre. Fuera sofás Recepción, fuera cristales obstructivos. Pasillos amplios; Performance y Sistemas funcionales. Usar la **última imagen aprobada por el usuario como referencia estética**, nunca como captura de app implementada.
4. **Videowall gigante:** franja de pantallas oscura en la **pared superior/norte**, visualmente protagonista desde la vista isométrica, con 5–7 módulos y acceso a **«Ver panel completo»** en DOM; no colocar números falsos ni texturas financieras precocinadas. El centro de control NO sustituye el mundo 3D como pantalla inicial.
5. **NPC visibles:** **16 humanos profesionales** como presupuesto máximo inicial, sentados trabajando de forma **ambiental** (no 16 procesos IA), con LOD y calidad ajustada al Intel integrado. Distribución: Recepción 1, Trading 3, Research 3, Quant 2, Riesgos 2, Ejecución 1, Comité 1, Performance 1, Sistemas 2 = **16**. Uno es agente principal por cada una de las 9 salas; 7 secundarios. Si la medición no permite 16 con FPS aceptable, **reducir detalle/animación y LOD antes que el número**, y registrar honestamente si no es viable.
6. **Agentes IA lógicos:** **30 roles especializados definidos en P4**, no 30 LLM ejecutándose ni 30 suscripciones. **Presets de equipos:** estudiar los ~30 swarm presets anunciados por Vibe-Trading en una release de 2026; importar/adaptar solo presets auditados y útiles. El catálogo puede mostrar hasta 30 configuraciones **si están realmente verificadas**; ejecutar como máximo 1 trabajo LLM local a la vez por defecto, 2 jobs cuantitativos CPU y 4 tareas ligeras de datos, con límites configurables y cancelación.
7. **Integraciones externas:** Agent Reach **lectura pública segura** desde P2 cuando pase auditoría; Vibe-Trading **investigación de compatibilidad/contratos P2** y backtesting/factores/swarms **P4–P5**; Liquid **solo metadatos públicos si existen y son autorizados**, sin OAuth estándar porque su token incluye **read + trade**; modo paper Liquid NO justifica conceder scope trade. Bloqueado hasta read-only demostrable sin credenciales de ejecución.
8. **Fases:** P1 diseño/navegación/NPC/videowall con estados honestos; P2 datos y noticias públicas; P3 ledger MASTER 10.000 EUR ficticios; P4 agentes reales y estrategias; P5 riesgo/comité/backtesting; P6 operaciones PAPER exclusivamente; P7 QA. **NO anticipar cifras de fases futuras**.
9. **0 EUR adicional**, secretos solo backend, licencias verificadas, NO live, NO wallets, NO órdenes a Liquid, ninguna operación en P2. La única «operación» visible antes de P6 será estado NO DISPONIBLE o eventos paper **realmente** existentes en el ledger autorizado.

## 1. Referencia visual y layout

### 1.1 Distribución

- **Mantener 9 departamentos canónicos y 9 paneles funcionales** con IDs existentes: `reception`, `trading`, `research`, `quant`, `risk`, `execution`, `committee`, `performance`, `systems`. No romper rutas, contratos, tests ni triggers por cambiar señalética.
- Recrear la **sensación de oficinas laterales + eje central abierto** de la imagen aprobada. Vestíbulo de entrada en primer plano, recepción en centro, gran pantalla en la pared superior, comité cerca del centro/norte, trading y quant a la derecha, research y macro a la izquierda, performance/sistemas accesibles y bien amueblados.
- «Macroeconomía», «Fundamental», «ESG» y «Legal/Compliance» pueden aparecer como **pods o subdivisiones VISUALES** dentro de Research/Risk/Committee, **NO nuevos departamentos de backend ni cuatro paneles extra obligatorios** en P1. «Ejecución» debe seguir existiendo aunque la imagen conceptual no lo rotule.
- Puede modificarse la geometría 3×3 de 34×28 m para obtener mejor circulación, **siempre conservando los nueve departamentos y 9 triggers**; documentar el nuevo mapa, anchors y coordenadas. No reconstruir el repositorio ni sustituir todo el código 3D sin justificación.
- Todos los NPC sentados en mesas, mirando monitores, manos alineadas; una mesa y silla físicamente accesibles para cada agente principal. Evitar cristales que bloqueen rutas, puertas falsas, clipping, muros que tapen salas y sofás en recepción.
- La arquitectura puede usar paredes recortadas/ocultas por cámara (cutaway/roof hiding) y sombras horneadas; nada de 16 skinned meshes con sombras costosas si afecta Intel. El gran videowall usa 1–3 superficies eficientes y contenido DOM accesible.

### 1.2 Cámara y navegación — CAMBIO DE REQUISITO EXPLÍCITO

**Cámara:** ortográfica o perspectiva larga con FOV estrecho, azimut isométrico fijo (p. ej. 35–45°), elevación 40–55°, seguimiento suave amortiguado en XZ, avatar siempre visible y techo/oclusores atenuados u ocultos. El videowall debe ser legible desde la vista global; al recorrer zonas se puede mostrar una versión mini/fija de los indicadores en HUD sin tapar al jugador. Vista global con botón DOM «Vista general», Escape para volver.

**Flechas:** el usuario quiere moverse en las cuatro direcciones **tal como se ven en pantalla**. Convertir vectores de teclado al plano XZ usando base proyectada de la cámara; ↑/↓/←/→ trasladan, no rotan cámara ni avatar en vacío. Avatar interpola su yaw hacia el vector de movimiento; animación idle/walk/turn sincronizada con desplazamiento y foot sliding mínimo. Al abrir overlay/inputs, suspender eventos; no scroll del navegador. No requerir mouse-look ni teclas E/WASD.

**Interacción:** 9 paneles se abren automáticamente por acercarse al **NPC principal** de cada sala, radio inicial ~2,0 m y rearme ~2,8 m, más chequeo de departamento y línea de paso; no activar a través de tabiques. Si el usuario cierra un panel, no reaparece hasta alejarse. **El videowall es una excepción explícita:** botón DOM «Ver centro de control» o acercamiento al área central; no forzar acercamiento a un NPC para consultar resumen global. Accesibilidad teclado y foco.

### 1.3 Presupuesto de calidad

- Referencia Windows 11, Intel Core 5 120U, 16 GB RAM, Intel Graphics 1920×1080. **Objetivo 45–60 FPS en modo equilibrado, ideal 60; mínimo sostenido 30**; medir en movimiento, no solo en vista estática. Nunca inventar FPS.
- DPR adaptativo (p. ej. 0.75–1), shadow map limitada, instancing, GLB comprimidos si herramientas locales, texture atlases, LOD de NPC, desactivar microanimación fuera de cámara, no crear un render loop de React por ticker.
- Estética Sims premium **estilizada**, no fotorealismo extremo ni muñecos rígidos; priorizar legibilidad, circulación y fluidez. Mostrar capturas **reales de navegador** del nuevo modo isométrico, vista general y al menos 4 departamentos.

## 2. Gran videowall: contrato funcional, no ilustración engañosa

**Composición visual sugerida, de izquierda a derecha:**
1. Identidad JAIME + etiqueta permanente **«SIMULACIÓN · PAPER ONLY»** y hora de último dato.
2. **Cartera MASTER EUR**: NAV, caja, variación diaria, P&L acumulado, rentabilidad %; datos exclusivamente del ledger P3.
3. **Posiciones/exposición**: top holdings, pesos, sector/país/activo y concentración; desde ledger + cotizaciones P2 autorizadas.
4. **Operaciones**: últimas órdenes paper, fills/rechazos, pendientes, estado de conciliación; **P6**, nunca inventar actividad.
5. **Mercados**: índices/FX/tipos/cripto realmente autorizados por P2, fecha, venue, retraso, divisa; no precios falsos.
6. **Noticias y alertas**: 3–5 titulares con URL/fecha/autor y relevancia; P2 RSS/GDELT/Agent Reach si legal; riesgos críticos P5.
7. **Agentes y sistemas**: número real de jobs P4 en ejecución/espera/error, salud de proveedores P2 y avisos de riesgo.

**Estados por fase:**
- **P1:** gran pantalla instalada, contenido real de `/health` si disponible, reloj local, «Cartera: pendiente de P3», «Operaciones: pendiente de P6», «Agentes: pendiente de P4», «Mercados: pendiente de P2». **Ninguna cifra de ejemplo de la imagen generada**.
- **P2:** añadir mercados/noticias con fuente+timestamp+derechos; cartera sigue NO DISPONIBLE, no crear 10.000 EUR hasta P3.
- **P3:** crear **una sola vez** ledger MASTER con 10.000,00 EUR ficticios, NAV inicial y caja derivada; cuentas demo de brókeres **no** se suman.
- **P4–P5:** jobs/tesis/alertas y límites solo si eventos reales registrados.
- **P6:** órdenes y fills **paper realmente registrados** y reconciliados; ninguna conexión live.

**Arquitectura:** `GET /api/hq/overview` (o ruta local equivalente) agrega datos de **solo lectura** de P2/P3/P4/P5/P6 según disponibilidad, con `sections[]` cada una con `state`, `as_of`, `source`, `value`, `reason`, `quality` y `links`. No crear tablas de cartera en P1/P2. Renderizar en DOM (React), opcional portal/Html en mundo 3D sin pixeles ilegibles; modo pantalla completa accesible, actualizaciones desacopladas del FPS y cache acorde a cuotas. La vista de planta puede conservar una banda reducida de KPIs sin tapar escenas. No permitir trading desde videowall.

**Invariantes de pruebas:** si no hay ledger, NO se muestra NAV=0 ni NAV=10000; si no hay fills, «Sin operaciones paper» solo cuando el ledger existe y ha sido consultado correctamente, en otro caso «No disponible». Precios stale deben estar marcados. Si P0/servidor offline, no dejar última cotización como «en directo». Tests de permisos, fuente, divisa, timestamps, offline, focus y no fake numbers.

## 3. Exactamente 16 NPC VISUALES ≠ 30 AGENTES DE TRABAJO

### 3.1 Reparto de NPC (aceptación P1)

| Sala canónica | NPC visibles | Principales |
|---|---:|---:|
| Recepción | 1 | 1 |
| Trading | 3 | 1 |
| Research (incl. macro/fundamental/ESG) | 3 | 1 |
| Quant | 2 | 1 |
| Riesgos | 2 | 1 |
| Ejecución | 1 | 1 |
| Comité | 1 | 1 |
| Performance | 1 | 1 |
| Sistemas | 2 | 1 |
| **Total** | **16** | **9** |

NPC con pose sentada y microanimaciones de trabajo ambiental; nunca mostrar `WORKING` si no hay job real P4. En P4 se puede asignar un NPC principal a un rol lógico, pero **el estado visual «tecleando» no significa que un modelo esté ejecutándose**. No renderizar un personaje por cada rol lógico. Mantener los 9 triggers y panels.

### 3.2 30 roles lógicos de P4 (definición, no ejecución continua)

| Equipo | Roles | Cantidad |
|---|---|---:|
| **Research** | Fundamental Equity; Valuation; Macro Global; Macro Europa/España; Crédito/Renta Fija; ESG/Regulación | 6 |
| **Trading & Execution** | Market Structure; Liquidity/Slippage; Execution Planning PAPER; Paper Operations/Reconciliation | 4 |
| **Quant** | Momentum/Trend; Value/Quality; Mean Reversion; Volatility/Regime; Portfolio Optimization | 5 |
| **Risk** | Market Risk; Credit/Counterparty; Liquidity Risk; Concentration; Compliance/Kill-Switch | 5 |
| **Performance** | NAV/Attribution; Benchmark/FX; Reporting/Postmortem | 3 |
| **Systems & Data** | Data Quality; Provider Orchestration; News/Social Intelligence; Observability/Security | 4 |
| **Investment Committee** | CIO/Chair; Bull Advocate; Bear/Skeptic | 3 |
| **TOTAL** | **30 roles definidos, instanciados solo si hay capacidad** | **30** |

**Ejecución responsable:** registry declarativo `role_id`, equipo, herramientas permitidas, inputs, output schema, dependencias, costes, timeout, evidencias, job_id, versión de modelo y prompt, estados reales. DAG/orquestador pequeño, colas locales SQLite, **idempotencia y reanudación**, sin 30 procesos residentes. Default 1 inferencia local, 2 trabajos cuantitativos CPU, 4 fetches de datos; límites de CPU/RAM/tokens y botón detener. LLM local gratuito opcional solo si instalado y probado en este PC; si no, reglas y cálculos deterministas, roles que requieran LLM `NO DISPONIBLE`. Nunca usar APIs de modelos de pago automáticamente.

**Flujo de inversión**: universo y datos P2 → análisis Research/Quant → crítica Bear/Bull → Comité → validación determinista Risk con veto → propuesta PAPER P6 → registro append-only P3 → reconciliación → Performance/Postmortem. **Nunca permitir que un LLM anule el veto de riesgos, cree fondos, edite ledger directamente ni ejecute órdenes live.**

## 4. Vibe-Trading — integración gradual, no instalar todo a ciegas

**Fuente:** https://github.com/HKUDS/Vibe-Trading (MIT), https://github.com/HKUDS/Vibe-Trading/releases y https://github.com/HKUDS/Vibe-Trading/blob/main/SECURITY.md. Una release 0.1.12 anunciaba **30 swarm presets, 462 alphas y múltiples motores de backtest**; **verificar la release exacta/pin SHA y sus dependencias**, porque las cifras y los nombres cambian. **30 presets ≠ 30 agentes activos** y no garantizan utilidad ni rentabilidad.

**P2 — gate VT-0/VT-1:** inventario técnico y SBOM: licencia MIT + NOTICE de terceros, versión/commit, dependencias y CVEs, requerimientos Windows/Intel/16 GB, endpoints y coste. No instalar el paquete entero en el entorno principal. Si procede, entorno `.venv-vibe` separado (no versionado) y **solo lectura** de fuentes de datos ya verificadas, sin duplicar conectores P2 ni aceptar Yahoo/yfinance como fuente de producción sin derechos. Probar fixture de mercado y benchmark reproducible con input canónico; si instalación falla o rompe presupuesto, mantener adaptador deshabilitado y documentar.

**P4 — gate VT-2:** adoptar selectivamente herramientas cuantitativas/factores deterministas auditados (momentum, value, quality, volatility, macro, credit) con test point-in-time y licensing; mapear los presets upstream a `TeamPreset` en catálogo **hasta 30 si se verifican**. Activar inicialmente **6–10 presets útiles** (screening, fundamental, macro, quant, adversarial, risk review, allocation, postmortem); el resto solo disponible en catálogo tras validación. Ejecutar presets bajo el scheduler local, no disparar 30 swarms simultáneos.

**P5 — gate VT-3:** backtest reproducible con costes, spreads, FX, survivorship/lookahead, splits, walk-forward y stress. **Aviso de seguridad upstream:** estrategias Python generadas pueden ejecutar código local y el subprocess de backtest puede tener red. **No ejecutar Python generado o no confiable** en host con secretos ni en sandbox improvisada; usar estrategias preaprobadas/deterministas o sandbox de SO realmente aislada con FS/red restringidos y pruebas. Si no existe sandbox robusta en Windows, desactivar generated-code runner y usar factores deterministas propios.

**P6:** jamás habilitar plugins de brokers, trading live, ejecución, claves, cron live ni wallet de Vibe; solo se puede reutilizar el resultado de un análisis como **propuesta** a la tubería PAPER local con riesgo/veto y ledger propio.

## 5. Agent Reach — inteligencia de noticias y redes sociales

**Fuente:** https://github.com/Panniantong/agent-reach y https://github.com/Panniantong/agent-reach/blob/main/docs/install.md (MIT). La herramienta instala/gestiona canales; algunos son públicos y otros usan cookies de sesión completas o automatización de navegador. **No equivale a «acceso seguro a todas las redes» ni autoriza saltarse TOS**.

**P2 — gate AR-0/AR-1:**
1. Auditar repositorio oficial, pin commit/tag y dependencias. Ejecutar `--dry-run` y `--safe` si las opciones están presentes en versión comprobada. **No ejecutar directamente scripts remotos sin inspeccionarlos**, no `--channels=all`, `--system`, sudo ni cambios globales sin aprobación específica.
2. Activar **solo canales públicos y legales** con lectura: RSS/Atom de fuentes financieras, publicaciones de reguladores y emisores, GitHub público, YouTube metadata/subtítulos públicos donde derechos permitan. GDELT del P2 es fuente base; Agent Reach puede añadir canales con `source_url`, fecha, autor, licencia, estado.
3. **X, Reddit, Instagram, Facebook, LinkedIn, XiaoHongShu**: si exigen cookies/sesión/automatización, **NO** extraer cookies del navegador principal, no pedir al usuario que las pegue en Codex ni dar acceso a cuentas personales. Marcar `AUTH_REQUIRED`/`TERMS_RESTRICTED` hasta que exista mecanismo oficial/autorizado con cuenta secundaria explícita y aislamiento. No publicar, comentar, dar like, enviar DMs ni modificar perfiles.
4. Noticias y contenido social son **señales de baja confianza**, no precios ni hechos auditados; deduplicar, registrar URL/hora/autor, identificar fuente primaria, separar rumor/confirmado, mitigar prompt injection y propaganda. Nunca enviar contenido no confiable como instrucciones a herramientas o sistema. Respetar robots, licencias y cuotas.

**P4:** el rol News/Social Intelligence resume con citas y nivel de confianza; triangulación con SEC/IR/medios verificables. No ejecutar estrategias por un rumor ni dar privilegios a contenidos de redes.

## 6. Liquid Co-Invest — NO OAuth con scope de trading en PAPER ONLY

**Fuente oficial:** https://www.liquid.trade/coinvest-docs (consultada 2026-10-14). El OAuth estándar concede **dos scopes: read y trade**, y el servicio incluye operaciones live y un modo paper que puede volver a live. Por tanto **NO conectar el MCP OAuth estándar ni wallet/cuenta** en esta arquitectura PAPER ONLY, aunque la suscripción del conector sea gratuita. Esto no es un «pendiente técnico» que Codex pueda resolver quitando botones: el permiso de trading existe en el token.

**P2 — gate LQ-0:** estudiar si hay **endpoints de mercado públicos, sin cuenta, con derechos de visualización, 0 EUR y solo lectura** (p. ej. funding, OI, liquidaciones). Si los hay, crear adaptador aislado con GET allowlist y pruebas; si no, `BLOCKED_TRADE_SCOPE`/`NO_PUBLIC_READ_ONLY_API`, **no instalar ni conectar el MCP**. Se pueden mostrar enlaces oficiales de investigación sin importación de datos.

**P3/P4/P6:** solo reconsiderar si Liquid ofrece **credenciales con scope read-only verificable y revocable** o un sandbox completamente segregado con garantías verificadas de no live, sin wallet y sin capacidades de orden. **No usar el paper mode de Liquid como fuente de cartera MASTER**; la cartera maestra es el ledger local de 10.000 EUR, no el balance de otro simulador (Liquid habla de 10.000 USD paper). Si no hay garantías, permanecer bloqueado indefinidamente. **No conectar Liquid «porque las otras APIs están conectadas».**

## 7. Checkpoints ejecutables y gates (no todo en un único cambio)

| Hito | Resultado verificable | Condición de paso |
|---|---|---|
| **P1.S0** | Preflight git local, capturas baseline y FPS, referencias/contratos | Sin pérdida de cambios; seguridad P0 intacta |
| **P1.S1** | Oficina Sims isométrica, plano accesible, 9 departamentos y videowall P1 sin datos falsos | Capturas reales, vista global y FPS |
| **P1.S2** | Flechas screen-relative, avatar natural, cámara estable, cutaway/colisiones | Test de ↑↓←→ en cada orientación de cámara, sin WASD/mouse-look |
| **P1.S3** | 16 NPC sentados y 9 triggers a NPC principal | 9/9 paneles, no cross-wall ni reapertura, animación/LOD |
| **P1.S4** | Pulido visual Intel y QA P1 | Check/audit/build/E2E, 45–60 FPS objetivo, evidencia de <30 si ocurre |
| **P2.0–P2.2** | Núcleo de fuentes del plan P2 existente | Contracts/rights/cache/Decimal/UTC |
| **P2.3a/b/c** | Conexión máxima legal de públicas A; Agent Reach público AR-0/AR-1 | HTTP real por fuente cuando permitido; noticia con procedencia |
| **P2.4a/b/c** | Fuentes opcionales B; VT-0/VT-1 compatibilidad; Liquid LQ-0 investigación | NO_CREDENTIALS/BLOCKED honestos; no OAuth trade |
| **P2.5** | Sistemas/Data Quality + videowall mercado/noticias | Fuente/hora/derechos, placeholders cartera/operaciones |
| **P2.6** | QA offline/online/P0, STATUS, licencias, entregables | **STOP ANTES DE P3** |
| **P3** *(futuro)* | Ledger MASTER 10.000 EUR ficticios, eventos append-only, NAV, FIFO, FX, fees, coupons | Reconciliación y separación cuentas demo |
| **P4** *(futuro)* | Registry 30 roles, jobs reales, 6–10 presets VT probados, noticias AR con citas | 1 inferencia LLM por defecto; no jobs inventados |
| **P5** *(futuro)* | Riesgos deterministas/veto, comité adversarial, backtests VT auditados | No lookahead, sandbox o sin código generado |
| **P6** *(futuro)* | Ejecución y blotter **PAPER exclusivamente** | Kill switch, idempotencia, UNKNOWN sin retry ciego |
| **P7** *(futuro)* | QA integral, seguridad, rendimiento, backups, instalación Windows | Evidencias reproducibles y no prometer beneficios |

**Orden de implementación recomendado para no gastar tokens:** primero preservar versión LOCAL, reusar escena, cambiar cámara/controles y layout por componentes, videowall DOM con states; después 16 NPC con LOD; luego P2. No cargar toda la investigación de P4–P7 al contexto hasta el hito. Un commit por gate, test por gate, STATUS con hechos comprobados y pendientes; si no se puede terminar, checkpoint de reanudación.

## 8. Arquitectura de módulos y contratos (propuesta, adaptar a código LOCAL)

`frontend/src/world/`: `IsometricFollowCamera`, `ScreenRelativeControls`, `CutawayWalls`, `SeatedNPC`, `NPCRegistry`, `AgentProximityTriggers`, `HQVideowall` y `WorldPerformanceMode`. Mantener los componentes existentes cuando sea posible, **no duplicar una segunda escena**.

`frontend/src/components/hq/`: `VideowallOverview`, `VideowallFullscreen`, `ProviderBadge`, `PaperOnlyLabel`, `EmptySection`. React DOM y TanStack Query; no poner texto financiero como texture JPG estática.

`backend/app/`: extender servicios P2 de `provider_registry`, `market_data`, `news_ingestion` y `hq_overview` sin crear ledger P3 antes de tiempo. Integraciones opt-in detrás de feature flags: `agent_reach_public_enabled`, `vibe_data_adapter_enabled`, `liquid_public_readonly_enabled` (false por defecto hasta verificación); `liquid_oauth_enabled` **NO DEBE EXISTIR en P2**. Más adelante `agent_roles`, `team_presets`, `job_queue` y `backtest_runner`, todos con gates.

**Esquema de `HQSection`:** `section_id`, `phase_required`, `status` (`AVAILABLE`/`EMPTY`/`NOT_IMPLEMENTED`/`OFFLINE`/`STALE`/`BLOCKED`), `as_of_utc`, `source`, `currency`, `value`, `items`, `reason`, `rights`. **No inferir `0` de `null`**. Si no hay derechos de display, usar solo estado/enlace. Cualquier resultado financiero derivado debe poder rastrearse hasta fuente y versión de ledger.

**Conectores aislados:** procesos sin privilegios y env separado; la app no hereda cookies del navegador, credenciales de bróker ni API keys de modelos. No instalar dependencias de terceros no auditadas en el venv principal. En Windows usar permisos de usuario normales y permitir desinstalar/revertir integraciones sin afectar P0/P1/P2.

## 9. QA profesional — matriz de pruebas

- **Visual:** screenshot de la cámara Sims aprobada (no screenshot de concepto), 9 salas identificables, videowall grande visible, 16 NPC sentados, recepción sin sofás, Performance/Sistemas, cristales no obstructivos.
- **Navegación:** flechas screen-relative en diagonales, colisiones y paredes recortables, 9 NPC principales activan sus 9 paneles a ~2m, no panel de otra sala, Escape/histéresis, foco teclado.
- **Rendimiento:** Chrome/Windows Intel, 1920×1080, baseline vs final FPS promedio/p95 frame time, GPU calls/triángulos cuando accesibles, 16 NPC idle/walk, videowall activo; sin métricas inventadas.
- **P0/P2:** /health PAPER_ONLY, orders_enabled=false, /api/orders 403; proveedor 401/403/429/timeout/offline; P2 no crea saldo/trades ni abre sesiones live.
- **Videowall:** no cartera P1/P2; NAV 10.000 solo tras ledger P3; operaciones solo tras ledger+P6; datos stale/rights/offline etiquetados; fullscreen accesible; render no fuerza 60 peticiones/segundo.
- **Integraciones:** Agent Reach sin cookies personales y sin escritura; Vibe sin broker tools ni ejecución de Python no confiable; Liquid OAuth jamás conectado con trade scope; tests de allowlist, URL SSRF, secretos, subprocess/FS/red.
- **P4/P5 futuros:** 30 roles registrados pero jobs solo reales, coste medido, kill/cancel, 30 presets solo si upstream verificados, 6–10 activados, determinismo y walk-forward.
- **Entregables:** `docs/evidencias/P1_SIMS/` capturas reales, `docs/INTEGRACIONES_TERCEROS_VERIFICACION.md` con versión/licencia/permisos/estado, `STATUS.md` con checkpoints y FPS, tests, commits y límites. **Una imagen generada no prueba implementación.**

## 10. Fuentes verificadas de esta decisión

- Vibe-Trading MIT, releases, presets y avisos de generated Python: https://github.com/HKUDS/Vibe-Trading ; https://github.com/HKUDS/Vibe-Trading/releases ; https://github.com/HKUDS/Vibe-Trading/blob/main/SECURITY.md .
- Agent Reach MIT, modos de instalación y advertencias cookies: https://github.com/Panniantong/agent-reach ; https://github.com/Panniantong/agent-reach/blob/main/docs/install.md .
- Liquid Co-Invest OAuth `read+trade`, paper que puede volver live, costes de operaciones: https://www.liquid.trade/coinvest-docs .
- Infraestructura y fuentes de datos P2: [PLAN_P2_CHECKPOINTS.md](PLAN_P2_CHECKPOINTS.md) y [P2_CATALOGO_MAXIMO_FUENTES.md](P2_CATALOGO_MAXIMO_FUENTES.md).

**Conclusión operativa:** la visión está aprobada; **16 NPC visuales, 30 roles IA y hasta 30 presets auditados**, pero solo se activan recursos cuando sean seguros, gratuitos y verificables. Integración de Agent Reach y Vibe por gates, Liquid bloqueado hasta auténtico read-only. **Codex puede empezar P1 correctivo + P2 ya; STOP antes de P3.**
