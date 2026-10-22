# Realineación de JAIME INVESTOR HQ: fondo cuantitativo autónomo local

**Fecha:** 2026-10-23. **Estado:** decisión de arquitectura y plan de trabajo; **NO autoriza código P5/P6 ni órdenes**.

## 1. Propósito y límites

JAIME no es principalmente un chatbot financiero ni una gestora regulada. Es una **organización local de investigación y simulación cuantitativa**, supervisada desde la oficina 3D, cuyo objetivo es **trabajar por iniciativa propia mientras el backend esté encendido**: detectar cambios de datos, investigar, proponer hipótesis, ensayar estrategias de forma reproducible, descartar las frágiles, construir propuestas de cartera y, **solo cuando P6 se autorice**, gestionar una cartera PAPER con controles deterministas.

El usuario puede hacer preguntas y pedir investigaciones profundas; ese canal es **adicional**, no requisito para activar el ciclo autónomo. La oficina 3D es una interfaz de observación, intervención administrativa y explicación; no es el scheduler ni el motor de ejecución. El backend debe poder trabajar con la oficina cerrada, siempre que el proceso local permanezca activo. **No se promete servicio 24/7 con el PC apagado**.

Invariantes permanentes en el estado actual:
- **0 EUR de gasto obligatorio**, sin servicios o modelos de pago, ni nueva infraestructura facturable.
- Windows local, **16 GB RAM**, **1 LLM local** y como máximo 1 inferencia concurrente; 30 roles lógicos estables, no 30 modelos.
- **MASTER de 10.000 EUR ficticios**, sin operaciones reales; `orders_enabled=false`, `live_trading_enabled=false`, `POST /api/orders=403`.
- P4 solo puede escribir su dominio de research; no puede mutar cash, posiciones, NAV, órdenes o fills.
- **P5 y P6 no están autorizados**. Sus contratos en este documento son diseño futuro. Una autorización de documentación no habilita fases.
- No afirmar alfa, rentabilidad, ejecución, cobertura point-in-time, licencias o tests sin evidencia.

## 2. Dependencias: no bloquear P5 por un debate LLM

```text
                       P2 DATA PLATFORM
                        /            \
                       v              v
             P4 RESEARCH/AGENTS   P5 STRATEGY FACTORY
                       \              /
                        \            /
                         v          v
                    P5 PORTFOLIO + RISK
                              |
                       P3 LEDGER
                              |
                              v
                      P6 PAPER OMS/BROKER
                              |
                              v
                         SHADOW / QA
                              |
                              v
                    P8 LIVE (FUERA DE ALCANCE)
```

P4 sigue **PARTIAL**: los jobs deterministas funcionan, pero no se ha aceptado el debate profundo Bull/Bear/Chair. Eso **no debe convertirse en bloqueo arquitectónico** del futuro motor determinista P5. P5 necesitará autorización propia y datos válidos, pero podrá calcular y ensayar estrategias **sin LLM activo**. El LLM interpreta y propone hipótesis estructuradas; **Python es propietario de hechos, cálculos, backtests, métricas y límites de riesgo**.

Se conservan los 30 `role_id` de `docs/09_AGENTES.md`. El router selecciona únicamente los necesarios. Bull, Bear y Chair se reservan principalmente para revisiones profundas o promoción de supervivientes, **después** de filtros baratos y validaciones estadísticas. No se obliga a que toda consulta ordinaria termine en debate completo.

## 3. P4: canal autónomo por eventos (propuesta, NO implementada)

No eliminar `ResearchCase` ni reinterpretar sus preguntas o expedientes históricos. Introducir un **dominio de eventos y tareas separado**, enlazable a un `ResearchCase` cuando corresponda:

```json
{
  "schema_version": "autonomy-event.v1",
  "event_id": "uuid",
  "trigger_type": "SCHEDULED_RESEARCH",
  "created_at": "UTC ISO-8601",
  "objective": "DISCOVER_STRATEGY",
  "subject": {"asset_class": "EQUITY", "universe_id": "EXAMPLE_PIT"},
  "priority": 40,
  "reason_code": "scheduled_cycle",
  "parent_event_id": null,
  "idempotency_key": "deterministic-key"
}
```

Los valores del ejemplo **no significan que exista hoy un universo `EXAMPLE_PIT` utilizable**. Triggers propuestos: `SCHEDULED_RESEARCH`, `NEW_DATA_AVAILABLE`, `NEW_FILING`, `REGIME_CHANGE`, `STRATEGY_DEGRADATION`, `PAPER_FILL`, `RISK_LIMIT_APPROACHING`, `POSTMORTEM_DUE`. Solo habilitar un trigger si existen su fuente, permisos y semántica. Los eventos de P5/P6 no se emitirán operativamente antes de esas fases.

`AutonomyEvent -> ResearchRouter -> ResearchTask -> roles seleccionados -> evidencia estructurada`. Cada tarea requiere inputs disponibles, capacidades de datos, mandato, presupuesto de CPU/RAM/LLM, versionado, idempotencia, estado persistente, auditoría, recuperación tras reinicio y abstención explícita. No ejecutar código generado libremente por el LLM. No inferir que el scheduler P4 actual ya crea eventos autónomos: **hoy el dominio sigue centrado en `question`**.

**Primer gate futuro AUT:** con backend encendido y sin intervención en UI, un evento programado crea trabajo real; no duplica al reiniciar; con LLM apagado completa lo determinista o marca lo generativo como no disponible; con oficina cerrada continúa. No modificar el pipeline existente sin tests de regresión.

## 4. Recursos y profundidad adaptable

Propuesta de `ResourceGovernor` determinista, basada en mediciones de RAM/CPU, no en estimaciones del LLM:

| Perfil | Oficina | LLM | Quant | Política |
|---|---|---|---|---|
| Interactivo | Abierta | hasta 1 | hasta 1 | Posponer barridos largos |
| Investigación | Segundo plano | hasta 1 | 1–2 si RAM lo permite | Batches acotados |
| Batch | Cerrada o inactiva | preferiblemente 0 durante barridos | acotado por RAM | Experimentos Python y síntesis posterior |

Los límites son objetivos a validar, no capacidad medida ni promesa de rendimiento. En presión de memoria, posponer trabajos no críticos; nunca saltarse controles de seguridad. El PC apagado o backend detenido **no ejecuta tareas**; al volver, reconciliar agenda y evitar duplicados.

P4 ordinario: datos y features Python más **como máximo una síntesis LLM compacta opcional**. P4 profundo: especialistas pertinentes y comité secuencial, solo con evidencia suficiente, presupuesto explícito y revisión semántica. Mantener el estado PARTIAL hasta pruebas reales; no repetir benchmarks largos por defecto. Ver `docs/P4_PROFUNDIDAD_Y_CIERRE.md`.

## 5. P2: puertas de preparación de datos

La existencia de una cotización o histórico P2 **no demuestra** que se pueda backtestear una estrategia. Diseñar gates independientes por **instrumento, fuente, periodo y universo**:

- `RESEARCH_READY`: procedencia, derechos, calidad, unidades, UTC y frescura para la pregunta.
- `BACKTEST_READY`: historial suficiente, disponibilidad temporal point-in-time, calendario, universo histórico (incluidos delistings cuando corresponda), corporate actions, FX y ajustes compatibles con la estrategia.
- `EXECUTION_SIM_READY`: lo anterior más supuestos de costes, spread, liquidez, latencia, participación y semántica de fills suficientes para el simulador.

Para fundamentales y eventos, exigir conceptualmente `period_end`, `published_at`, `available_to_strategy_at`, `restatement_version`, `source`, `retrieved_at`, `rights`. **Nunca** usar en una fecha simulada un dato publicado después. Rechazar `NO_DATA` / `NOT_BACKTEST_READY` en vez de completar huecos con valores inventados.

Primero fixtures sintéticos deterministas y, más tarde, uno o dos datasets reales **autorizados** para comprobar mecánica. Esto no demuestra alfa ni cobertura multiactivo. No asumir que el archivo histórico actual cumple los tres gates.

## 6. P5: contratos futuros, NO implementados

Separar `StrategyService` y `StrategyStore` del dominio `ResearchService`/`ResearchStore`. Una `StrategyGenome` tipada y versionada define hipótesis, mecanismo económico, falsación, universo, señales, rebalanceo, restricciones, costes y ventanas temporales. Un compilador **allowlisted y determinista** valida schema, semántica y capacidades de datos antes de cualquier experimento. El LLM no escribe ni ejecuta scripts arbitrarios ni calcula retornos.

Registrar **cada intento** antes de ver el resultado en `HypothesisRegistry`, `StrategyRegistry`, `ExperimentRegistry` y `StrategyGraveyard`: IDs y genealogía, trials incluidos los fallidos, snapshots/hashes de datos, código y parámetros, muestras train/validation/untouched-OOS, exposición heredada a OOS, costes, métricas y motivos de rechazo. Nunca guardar solo los ganadores.

Gates baratos primero: integridad temporal, costes, robustez paramétrica, concentración, regímenes, walk-forward y OOS. PSR, DSR y PBO/CSCV **solo cuando su aplicación estadística sea válida**, con número de trials, dependencia entre variantes y tamaño muestral documentados. El comité Bull/Bear/Chair evalúa supervivientes, no miles de candidatos brutos. La aprobación cualitativa nunca sustituye veto de riesgo.

Criterios de prueba futuros: fixture exacto, detección de look-ahead y survivorship, costes reproducibles, registro completo de variantes, genealogía OOS y capacidad de correr sin LLM. **No hay backtest engine P5 implementado hoy.**

## 7. P6: contratos futuros, NO implementados

```text
Strategy -> PortfolioTarget -> TradeIntent -> RiskEngine determinista
-> ValidatedOrderIntent -> Paper OMS -> InternalPaperBroker
-> Fill -> P3 MASTER ledger -> Reconciliation -> Postmortem
```

`TradeIntent` **no es una orden**. Solo el OMS autorizado puede emitir órdenes PAPER. Debe existir idempotencia, control de caja, frescura, límites, partial fills, cancelación, rechazo, `UNKNOWN -> RECONCILIATION_HALT`, y veto por discrepancias. Un kill switch de nuevas órdenes **no implica liquidación automática**.

Orden de implementación, siempre previa autorización: **InternalPaperBroker** reproducible, después evaluar adaptadores externos **IBKR PAPER** y/o **Alpaca PAPER** según verificación vigente de APIs, acceso regional, permisos, tarifas y coste 0 €. No instalar ni conectar brokers ahora. El LLM no recibe credenciales ni acceso a `submit_order`; no existe switch simple PAPER/LIVE. LIVE queda fuera de P6 y requeriría fase/proceso/autorización independientes.

## 8. Gates y secuencia autorizable

| Orden | Entrega | Estado al 2026-10-23 | Autorización |
|---|---|---|---|
| 0 | Realinear visión, ADR, tasks y contratos | **Documentación** | Solicitada |
| 1 | P4 AutonomyEvent/Router mínimo + pruebas de restart/LLM-off | **Diseño** | Nueva instrucción P4 |
| 2 | P2 readiness point-in-time y fixtures | **Diseño** | Nueva instrucción P2 |
| 3 | P5A Genome, registry, graveyard, backtest determinista | **NO INICIADO** | **Autorización expresa P5** |
| 4 | P5B Red Team, OOS, estadística, portfolio/risk | **NO INICIADO** | Gate P5A y alcance aprobado |
| 5 | P6 OMS + InternalPaperBroker | **NO INICIADO** | **Autorización expresa P6** |
| 6 | Adaptador IBKR PAPER, shadow y QA | **NO INICIADO** | Gate P6 y autorización específica |
| 7 | LIVE | **FUERA DE ALCANCE** | Autorización futura separada |

El siguiente trabajo de implementación **no debe arrancar automáticamente** por haber fusionado esta documentación. Primero revisar el diff y aprobar un Goal acotado. Cada Goal deja evidencias, tests reales, actualización de `STATUS.md` y parada antes de otra fase.

## 9. Evidencia y afirmaciones pendientes

La auditoría recibida el 2026-10-23 y `docs/Plan_JAIME_P5_P6.md` son insumos de diseño. Sus afirmaciones sobre brokers, regulación, tarifas, modelos y bibliografía deben verificarse contra fuentes primarias **cuando sean necesarias**; no se importan como hechos operativos certificados. El estado técnico contrastado con el repositorio: P4 PARTIAL, paneles laterales compactos terminados, LLM integrado pero debate no aceptado, P5/P6 sin comenzar. Ninguna modificación documental equivale a ejecutar tests en el PC local.
