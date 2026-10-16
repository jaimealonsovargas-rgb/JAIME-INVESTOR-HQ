# P4 — Research y agentes IA | autorizado 2026-10-16

**STOP antes de P5.** Fuente ejecutable: `docs/PLAN_P4_AGENTES_RESEARCH_LOCAL_AI.md`.

Implementar **30 roles IA lógicos** bajo demanda, no 30 LLM residentes. Registry, permisos deny-by-default, jobs persistentes, research cases, evidencia, claims, resultados versionados y auditoría.

Runtime preferente: IA **local y gratuita**, máximo 1 inferencia simultánea; 2 jobs quant CPU y 4 fetches ligeros. Benchmark local de 1–2 modelos compactos cuantizados; si no son utilizables, mostrar `NO_LOCAL_MODEL` y mantener modo determinista sin fingir outputs.

Pipeline inicial de 6–10 roles: Data Quality, Fundamental, Valuation, Macro, Momentum, Regime/Volatility, Bull, Bear/Skeptic y CIO/Chair según caso. Los otros roles se activan por asset class y contexto.

Dossiers: overview, tesis, argumentos, contraargumentos, catalizadores, riesgos, invalidación, evidence IDs, claims numéricos trazables, unknowns, opiniones de agentes y síntesis del Chair. Contenido externo es `UNTRUSTED_CONTENT` y nunca instrucciones.

Vibe-Trading permanece sin brokers/generated-code; usar solo presets/factores auditados y preferir lógica determinista preaprobada. Agent Reach solo público/read-only sin cookies/cuentas personales.

UI: roles/estado/jobs reales por departamento, dossiers Research, Quant con provenance, Bull/Bear/Chair en Comité, runtime/cola en Sistemas y módulo AGENTES P4 del videowall.

Invariantes: **0 EUR**, PAPER ONLY, `orders_enabled=false`, `/api/orders=403`, ningún agente muta ledger/cash/positions/NAV/orders/fills. P5 riesgo formal/backtests y P6 ejecución siguen fuera de alcance.
