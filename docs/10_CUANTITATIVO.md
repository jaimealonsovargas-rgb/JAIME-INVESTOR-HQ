# Quant Lab, señales y construcción de cartera

Pipeline: universo point-in-time → datos históricos autorizados → limpieza/ajustes → features → señales → pesos → costes → backtest → walk-forward → revisión riesgo → propuesta.

Familias iniciales: momentum/trend, calidad/valor, reversión prudente, macro-regímenes, factor allocation, cash/defensive, duración de bonos, escenarios de spread crediticio y rebalanceo. No prometer alfa ni sobreajustar.

Métricas con muestras suficientes: retorno, volatilidad, Sharpe con risk-free/frecuencia coherentes, Sortino, max drawdown, hit rate, turnover, exposición, costes, benchmark y DD duration. Evitar lookahead, leakage, survivorship bias, sesgo de publicación, cambios de universo y precios ajustados incompatibles con fills. Versionar dataset, código, calendario, parámetros y costes.

El comité recibe evidencias y objeciones. Riesgos tiene veto final. Backtest ≠ resultados reales ni prueba de rentabilidad futura.
