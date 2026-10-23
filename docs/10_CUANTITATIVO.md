# Quant Lab, señales y construcción de cartera

Pipeline: universo point-in-time → datos históricos autorizados → limpieza/ajustes → features → señales → pesos → costes → backtest → walk-forward → revisión riesgo → propuesta.

Familias iniciales: momentum/trend, calidad/valor, reversión prudente, macro-regímenes, factor allocation, cash/defensive, duración de bonos, escenarios de spread crediticio y rebalanceo. No prometer alfa ni sobreajustar.

Métricas con muestras suficientes: retorno, volatilidad, Sharpe con risk-free/frecuencia coherentes, Sortino, max drawdown, hit rate, turnover, exposición, costes, benchmark y DD duration. Evitar lookahead, leakage, survivorship bias, sesgo de publicación, cambios de universo y precios ajustados incompatibles con fills. Versionar dataset, código, calendario, parámetros y costes.

El comité recibe evidencias y objeciones. Riesgos tiene veto final. Backtest ≠ resultados reales ni prueba de rentabilidad futura.

## Contrato P5 futuro — no implementado ni autorizado

**Objetivo:** fábrica científica reproducible, no búsqueda de una estrategia «perfecta». El LLM solo propone hipótesis estructuradas; el motor Python ejecuta backtests, métricas y controles. Los 30 roles siguen siendo lógicos y se seleccionan por mandato; Bull/Bear/Chair revisan únicamente supervivientes tras gates deterministas.

**StrategyGenome v1** (diseño): hipótesis, mecanismo económico, falsación, familia, universo point-in-time, features, señales, rebalanceo, límites, costes, ventanas train/validation/untouched-OOS, versión y genealogía. Validación de schema, semántica y capacidades P2 antes de compilar un experimento allowlisted. Prohibidos scripts arbitrarios generados por el LLM.

**ExperimentRegistry / StrategyGraveyard** (diseño): registrar todos los trials **antes** de observar su resultado, incluidos fallos y variantes; preservar parent/child, dataset snapshot hash, code hash, parameter hash, modelo de costes, calendario, universo, métricas, razón de rechazo y exposiciones heredadas a OOS. Nunca conservar solo los ganadores ni reutilizar un OOS contaminado como virgen.

**Orden de filtros:** integridad temporal/universo → backtest fixture → fees/spread/slippage → estabilidad de parámetros y contribuciones → regímenes y leave-one-out → walk-forward → PSR/DSR/PBO-CSCV **si hay muestras y condiciones válidas** → untouched OOS → comité → cartera y veto determinista. No convertir Sharpe, PBO ni DSR en garantías.

**Métricas candidatas:** CAGR, volatilidad, Sharpe con risk-free/frecuencia, PSR/DSR/PBO aplicables, Sortino, Calmar, máximo drawdown y duración, turnover, hit rate, payoff, profit factor, exposiciones, beta, correlaciones, concentración por activo/trade/año, sensibilidad a costes, robustez de parámetros, regímenes y proxy de capacidad. Cada métrica exige definiciones, unidades y tamaños de muestra.

**Gates de datos:** `RESEARCH_READY`, `BACKTEST_READY`, `EXECUTION_SIM_READY` por instrumento/universo/periodo. Fundamentales necesitan `published_at` y `available_to_strategy_at`; universos históricos incluyen deslistados cuando corresponda; calendario, ajustes y corporate actions deben ser compatibles con el fill simulado. Un `NO_DATA` rechaza el experimento, no se imputa silenciosamente.

**Tests futuros:** fixtures matemáticos exactos, look-ahead intencional rechazado, delisting en universo histórico, sensibilidad a costes, registro completo de 500 variantes sintéticas, contaminación OOS heredada, ejecución sin LLM, repetición byte-equivalente o tolerancia numérica explícita. Un fixture sintético valida software, **no alfa**.

Referencias de diseño: [Realineación 2026-10-23](REALINEACION_FONDO_AUTONOMO_2026_10_23.md) y [Plan estratégico P5/P6](Plan_JAIME_P5_P6.md). **P5 NO INICIADO: autorización expresa requerida.**
