# Quant Lab, señales y construcción de cartera

Pipeline: universo point-in-time → datos históricos autorizados → limpieza/ajustes → features → señales → pesos → costes → backtest → walk-forward → revisión riesgo → propuesta.

Familias iniciales: momentum/trend, calidad/valor, reversión prudente, macro-regímenes, factor allocation, cash/defensive, duración de bonos, escenarios de spread crediticio y rebalanceo. No prometer alfa ni sobreajustar.

Métricas con muestras suficientes: retorno, volatilidad, Sharpe con risk-free/frecuencia coherentes, Sortino, max drawdown, hit rate, turnover, exposición, costes, benchmark y DD duration. Evitar lookahead, leakage, survivorship bias, sesgo de publicación, cambios de universo y precios ajustados incompatibles con fills. Versionar dataset, código, calendario, parámetros y costes.

El comité recibe evidencias y objeciones. Riesgos tiene veto final. Backtest ≠ resultados reales ni prueba de rentabilidad futura.

## Contrato futuro de preparación P5 (diseño, no implementación)

Separar `RESEARCH_READY`, `BACKTEST_READY` y `EXECUTION_SIM_READY` por dataset, universo, instrumento y uso permitido. El histórico P2 actual no certifica por sí solo universo point-in-time, exclusiones y bajas, fecha de publicación/disponibilidad de fundamentales, revisiones, corporate actions, calendarios, bid/ask ni costes. Un backtest debe rechazar datos conocidos únicamente después de la fecha simulada. Registrar `period_end`, `published_at`, `available_to_strategy_at`, revisión, derechos y procedencia cuando existan; ausencia significa capacidad no verificada.

El futuro Strategy Genome será una especificación validada, nunca Python arbitrario ejecutado desde un LLM. Registrar cada hipótesis y ensayo, también los descartados, con hashes de datos/código/configuración, genealogía y uso de OOS. Python calculará señales, métricas, costes y pruebas adversariales. Bull/Bear/Chair revisarán solo candidatos que superen filtros deterministas y con evidencia suficiente. Ver `docs/ARQUITECTURA_AUTONOMIA_P4_P5.md`; **P5 sigue sin autorización de implementación**.
