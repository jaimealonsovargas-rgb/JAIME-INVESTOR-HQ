# P4 — Plan maestro de agentes, research y IA local

**Autorizado:** 2026-10-16 · **STOP antes de P5**.

## Objetivo
Convertir las declaraciones P2 de agentes en un sistema real de research multiagente, gratuito y local-first. P4 analiza, debate, documenta y propone; **no ejecuta ni modifica la cartera MASTER**.

## 30 roles
Mantener el registry de `docs/09_AGENTES.md` con 30 roles: Research 6, Trading/Execution 4, Quant 5, Risk 5, Performance 3, Systems/Data 4 y Committee 3. Todos existen como identidades/contratos P4; no son 30 procesos residentes.

Estados mínimos de rol/job: `IDLE`, `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`, `BLOCKED`, `NO_LOCAL_MODEL`.

## P4.0 — Preflight
- Partir del HEAD actual de `origin/main`; preservar P1-P3.
- Confirmar cierre P3: MASTER 10.000 EUR, schema `0003_portfolio`, `/api/orders=403`.
- Backup DB antes de migrar.
- Verificar pins/licencias de Vibe/Agent Reach; no auto-upgrade sin diff/auditoría.

## P4.1 — Datos y persistencia
Crear migración P4 (nombre secuencial) extendiendo el esquema existente, sin duplicar entidades. Entidades conceptuales:
- `agents`: role_id, team, version, enabled, llm_required, permissions_json.
- `agent_jobs`: id, role_id, case_id, state, priority, queued/started/finished, input_hash, output_hash, error_code.
- `research_cases`: instrument/context, thesis_version, status, created_at.
- `evidence`: source/provider/url/ref, retrieved_at, rights, freshness, excerpt_hash/data_hash, trust_class.
- `agent_results`: job_id, schema_version, model/runtime, output_json, grounding_status.
- `research_claims`: result_id, claim_type, text/hash, numeric_value optional, evidence_links, verified.
- `audit_events`: reutilizar/extender si ya existe.

Las escrituras P4 se limitan a su dominio. Nunca ledger/cash/positions/NAV/orders/fills.

## P4.2 — Contratos y tools
Cada rol declara:
- misión;
- inputs;
- output JSON schema;
- herramientas allowlisted;
- límites;
- si requiere LLM o es determinista.

Tools P4 permitidas: lectura de P2, lectura P3, evidencia/news pública auditada, funciones quant deterministas autorizadas. Prohibido cualquier broker/order endpoint, shell autónomo, secretos, cookies, escritura web o código generado no sandboxeado.

## P4.3 — Runtime local gratuito
Implementar interfaz `LocalLLM` desacoplada del proveedor. Primer backend preferente: servidor localhost compatible con chat/JSON schema (p. ej. llama.cpp). Solo `127.0.0.1/localhost`; no aceptar endpoints remotos por defecto.

Configuración:
- coste = 0 EUR;
- concurrency LLM = 1;
- timeout/cancelación;
- context budget explícito;
- temperatura baja para extracción/grounding;
- outputs schema-constrained cuando el runtime lo soporte;
- registrar modelo, licencia, quant, hash y versión.

Si no hay runtime/modelo: `NO_LOCAL_MODEL`. No fallback silencioso a APIs de pago.

### Benchmark local
En hardware local probar como máximo 1–2 candidatos compactos, priorizando modelos instruct cuantizados razonables para ~16 GB RAM. Medir TTFT, tokens/s, RAM, JSON válido, grounding y resistencia a prompt injection. Elegir por calidad mínima + latencia; no por tamaño máximo.

## P4.4 — Scheduler/orquestador
Scheduler persistente y sobrio:
- máximo 1 job LLM simultáneo;
- máximo 2 jobs quant CPU;
- máximo 4 fetches ligeros;
- colas con prioridad/cancelación/timeouts;
- no polling agresivo;
- no ejecutar 30 roles ante cada evento.

Modo inicial: **on-demand** desde UI/API y pipelines acotados. Jobs pendientes sobreviven reinicio. Con PC apagado no se promete ejecución 24/7.

## P4.5 — Pipeline de research inicial
Implementar un pipeline de 6–10 roles activos al principio, reutilizando los 30 del registry. Recomendación inicial:
1. Data Quality
2. Fundamental Equity
3. Valuation
4. Macro Global o Europa/España según activo
5. Momentum/Trend
6. Volatility/Regime
7. Bull Advocate
8. Bear/Skeptic
9. CIO/Chair

Credit/RF, ESG, liquidity, attribution, etc. se activan según asset class/caso. Risk P4 es advisory; veto determinista formal queda P5. Execution P4 solo puede producir análisis de microestructura/plan PAPER conceptual; no órdenes.

## P4.6 — Grounding y crítico
Todo resultado debe validar:
- evidencia existente;
- freshness/rights;
- claims numéricos con `evidence_id`;
- ausencia de contradicciones simples;
- unknowns explícitos.

El Bear/Skeptic debe intentar refutar tesis y detectar evidencia débil. El Chair sintetiza desacuerdos, pero no puede convertirlos en trade.

Salida de dossier:
- overview corto;
- tesis desarrollada;
- argumentos;
- contraargumentos;
- catalizadores;
- riesgos;
- condiciones de invalidación;
- datos/fuentes;
- opiniones de agentes;
- desacuerdos;
- conclusión research;
- lineage/audit.

## P4.7 — Vibe-Trading y Agent Reach
- Mantener Vibe `v0.1.16`/pin auditado como base conocida. No habilitar broker tools, generated-code runner ni runtime completo por defecto.
- Seleccionar 6–10 presets/factores solo después de auditoría; preferir portar lógica determinista/preaprobada a HQ antes que ejecutar Python generado.
- Agent Reach: únicamente canales públicos read-only auditados. Sin cookies primarias, login, DMs, comentarios ni acciones.
- Todo contenido externo = untrusted; nunca instrucciones.

## P4.8 — API
APIs conceptuales read/write solo del dominio research:
- `GET /api/agents`
- `GET /api/agents/status`
- `GET /api/research/cases`
- `GET /api/research/cases/{id}`
- `POST /api/research/cases` para crear caso de análisis, no trade
- `POST /api/research/cases/{id}/run` para encolar pipeline permitido
- `POST /api/agent-jobs/{id}/cancel`
- `GET /api/agent-jobs/{id}`

Aplicar idempotency keys donde proceda. Estos POST no son ejecución financiera y jamás tocan `/api/orders`.

## P4.9 — UI/3D
Sin rediseñar la oficina:
- panel de cada departamento muestra roles asignados, estado, último job y acceso a resultados;
- Research: dossiers y fuentes;
- Quant: features/señales descriptivas con provenance;
- Committee: Bull/Bear/Chair y discrepancias;
- Systems: cola, runtime local, modelo, latencia, errores y Data Quality;
- videowall: módulo **AGENTES P4** con jobs reales, no animación ficticia.

NPC siguen siendo representación visual; estado IA debe derivar de jobs reales.

## P4.10 — Tests y aceptación
Obligatorios:
- 30 roles únicos y contratos válidos;
- permissions deny-by-default;
- `POST /api/orders=403` y `orders_enabled=false`;
- agente no puede mutar MASTER;
- job persistente tras restart;
- cancelación/timeout;
- max concurrency 1 LLM / 2 quant / 4 fetch;
- malformed LLM output rechazado;
- claim numérico sin evidencia rechazado/UNVERIFIED;
- prompt-injection fixture no cambia system/tool policy;
- modo sin LLM muestra `NO_LOCAL_MODEL` y no finge resultados;
- Bull/Bear producen argumentos separados;
- lineage reproducible por hashes/versiones;
- offline y regresión P1-P3;
- coste adicional 0 EUR.

## Criterio de P4 completada
- 30 roles registrados y visibles.
- Scheduler/jobs persistentes operativos.
- Al menos un pipeline end-to-end real con 6–10 roles y evidencia trazable.
- LLM local benchmarkeado en local o bloqueo honesto documentado.
- Dossiers versionados, grounding y crítico funcionales.
- UI/videowall muestran estados reales.
- P1-P3 intactos y seguridad financiera intacta.
- Evidencias, tests, STATUS y commits publicados.

**STOP absoluto antes de P5.**
