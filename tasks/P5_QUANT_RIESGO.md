# P5 — Strategy Factory, validación adversarial, cartera y riesgo

**ESTADO: NO INICIADO / NO AUTORIZADO (2026-10-23).** Este ticket es una **especificación futura**, no una orden de implementación. Requiere autorización expresa y gates P2 de datos; la semántica LLM profunda P4 no debe ser hard blocker del núcleo determinista.

**Objetivo:** laboratorio autónomo de estrategias cuantitativas reproducibles, con registro de todas las pruebas y descarte riguroso de falsas señales. LLM opcional para hipótesis/crítica; **Python dueño de features, backtests, métricas, asignación y veto**. No 30 LLM, no scripts arbitrarios ni órdenes.

## P5A — núcleo científico (primera autorización futura)

1. `StrategyGenome v1` versionado, tipado y allowlisted: hipótesis/mecanismo/falsación, familia, universo, features, señal, pesos, rebalanceo, costes, límites y muestras.
2. Validadores de schema/semántica, `RESEARCH_READY`/`BACKTEST_READY` P2, integridad temporal y publicación `available_to_strategy_at`; rechazar datos insuficientes.
3. `HypothesisRegistry`, `StrategyRegistry`, `ExperimentRegistry`, `StrategyGraveyard` **separados** de `ResearchCase`; registrar TODOS los trials antes del resultado, incluidos fallidos, genealogy, hashes de dataset/código/config/parámetros y reason codes.
4. `BacktestEngine` Python determinista, interfaces de costes y métricas, muestras train/validation/untouched-OOS y genealogía de exposición a OOS. Primero fixtures sintéticos exactos; después una serie P2 autorizada. Ningún fixture prueba rentabilidad futura.
5. Spike acotado de dependencias numéricas gratuitas compatibles con Python local; no instalar framework de pago ni introducir dependencia pesada sin evidencia.

**Gate P5A:** tests exactos de reproducibilidad, rechazo de look-ahead/survivorship, costes reproducibles, todos los trials preservados, sin LLM y sin broker. `POST /api/orders=403` inalterado.

## P5B — Red Team adversarial (autorización/alcance posterior)

Costes 1x/1.5x/2x y escenarios severos, sensibilidad paramétrica, contribución por activo/año/trade, regímenes, leave-one-out, walk-forward, PSR/DSR/PBO-CSCV cuando estadísticamente aplicables, corrección de búsqueda múltiple y `untouched-OOS` sellado con genealogía. Registrar incertidumbre y rechazos, no solo métricas favorables. Bull/Bear/Chair solo sobre supervivientes.

**Gate P5B:** rechazos verificables por sesgo/costes/fragilidad/OOS, lineage OOS, tests con muestras insuficientes y pruebas de falsación. No prometer alfa.

## P5C — cartera y veto determinista (autorización/alcance posterior)

Constructor de cartera y límites de concentración, caja, liquidez, exposición, leverage=false, short=false, stale data, stress y drawdown. `RiskEngine` deny-by-default y kill switch determinista. El LLM nunca cambia límites ni produce órdenes.

**Gate P5C:** propuestas de cartera con evidencia, veto automático ante datos/riesgo insuficientes, sin mutación de MASTER ni fills. El puente futuro `TradeIntent` es **propuesta**, no ejecución.

## Seguridad, dependencias y STOP

- Windows local, 16 GB RAM, 0 EUR obligatorios, 1 LLM concurrente y ResourceGovernor futuro basado en mediciones.
- P2 debe certificar readiness point-in-time por universo/periodo; la existencia de historial P2 no basta.
- Preservar 30 `role_id`, P3 ledger MASTER ficticio 10.000 EUR, `orders_enabled=false`, `live_trading_enabled=false`, `POST /api/orders=403`.
- **NO P6, NO IBKR, NO broker, NO LIVE.** Detenerse en cada gate y pedir autorización para continuar.

Fuente rectora: [Realineación 2026-10-23](../docs/REALINEACION_FONDO_AUTONOMO_2026_10_23.md). Investigación extensa: [Plan P5/P6](../docs/Plan_JAIME_P5_P6.md).
