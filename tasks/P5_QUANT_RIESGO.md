# P5 — fábrica cuantitativa y riesgo determinista | diseño futuro, NO AUTORIZADO

La dependencia obligatoria es P2 con datos adecuados al uso y P3 para contabilidad; el LLM P4 es opcional. Una P4 generativa incompleta no debe invalidar ensayos Python reproducibles. Ninguna capacidad de este ticket se implementa antes de autorización expresa.

Al autorizarse, dividir la entrega en contratos y gates: (1) preparación point-in-time por universo y feed; (2) Strategy Genome tipado, registro previo de hipótesis y todos los experimentos, incluidos descartes; (3) backtest Python con datos/código/parámetros/costes versionados; (4) walk-forward, OOS intocable y genealogía, costes, sesgos, estabilidad, PSR/DSR/PBO cuando correspondan; (5) construcción de cartera y riesgo determinista con veto. Un backtest o una discusión LLM no demuestran alfa. Rechazar capacidades faltantes y no extrapolar un smoke test de una serie a todo el universo.

Bull/Bear/Chair revisan supervivientes con evidencia tras filtros baratos. El LLM no ejecuta código generado ni modifica límites de riesgo. Mantener dominio de estrategias/experimentos separado de ResearchCase y MASTER; ver `docs/ARQUITECTURA_AUTONOMIA_P4_P5.md`.
