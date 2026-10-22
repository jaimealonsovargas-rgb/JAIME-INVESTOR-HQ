# P4 — Research y agentes IA | autorizado 2026-10-16

**STOP antes de P5.** Fuente ejecutable: `docs/PLAN_P4_AGENTES_RESEARCH_LOCAL_AI.md`.

La dirección aprobada el 2026-10-23 requiere que P4 prepare research iniciado por eventos además de casos iniciados por preguntas. `AutonomyEvent`/`ResearchTask` tendrán contrato y procedencia propios; no se convertirán en backtests ni órdenes. El modo ordinario usa Python y, como máximo, una síntesis local opcional; el modo profundo activa explícitamente Bull/Bear/Chair con presupuesto y abstención. Ver `docs/ARQUITECTURA_AUTONOMIA_P4_P5.md` y `docs/P4_PROFUNDIDAD_Y_CIERRE.md`. Los 30 `role_id` permanecen estables.

Implementar **30 roles IA lógicos** bajo demanda, no 30 LLM residentes. Registry, permisos deny-by-default, jobs persistentes, research cases, evidencia, claims, resultados versionados y auditoría.

Runtime preferente: IA **local y gratuita**, máximo 1 inferencia simultánea; 2 jobs quant CPU y 4 fetches ligeros. Benchmark local de 1–2 modelos compactos cuantizados; si no son utilizables, mostrar `NO_LOCAL_MODEL` y mantener modo determinista sin fingir outputs.

Pipeline inicial de 6–10 roles: Data Quality, Fundamental, Valuation, Macro, Momentum, Regime/Volatility, Bull, Bear/Skeptic y CIO/Chair según caso. Los otros roles se activan por asset class y contexto.

Dossiers: overview, tesis, argumentos, contraargumentos, catalizadores, riesgos, invalidación, evidence IDs, claims numéricos trazables, unknowns, opiniones de agentes y síntesis del Chair. Contenido externo es `UNTRUSTED_CONTENT` y nunca instrucciones.

Vibe-Trading permanece sin brokers/generated-code; usar solo presets/factores auditados y preferir lógica determinista preaprobada. Agent Reach solo público/read-only sin cookies/cuentas personales.

UI: roles/estado/jobs reales por departamento, dossiers Research, Quant con provenance, Bull/Bear/Chair en Comité, runtime/cola en Sistemas y módulo AGENTES P4 del videowall.

Invariantes: **0 EUR**, PAPER ONLY, `orders_enabled=false`, `/api/orders=403`, ningún agente muta ledger/cash/positions/NAV/orders/fills. P5 riesgo formal/backtests y P6 ejecución siguen fuera de alcance.

## Checkpoint P4 avanzado · 19–20 de octubre

Implementados objetivos tipados, EvidencePack, contratos separados de debate, abstención, validación de referencias cruzadas y HUD con históricos reales. Caso BCE informativo de cuatro roles y caso de abstención verificados por HTTP. Clic en nueve NPC, responsive y modo offline comprobados. Detalle: [validación avanzada](../docs/P4_AVANZADO_VALIDACION.md).

**Gate semántico pendiente:** los dos Qwen existentes y Llama 3.2 3B Q4 (autorizado explícitamente en el nuevo prompt del usuario) no superan el benchmark de debate. No se considera P4 avanzada completa. JSON válido y extractos verificados no equivalen a razonamiento financiero válido. Vibe continúa metadata-only; no hay cierres diarios suficientes para ejecutar los factores inspeccionados. No habilitar P5/P6.

## Cierre acotado del Goal · 22-10-2026

Entrega **PARTIAL**, por instrucción del usuario de detener intentos indefinidos. P4 no se marca terminada: debate suficiente no aceptado y FPS bajo carga por debajo del objetivo. [Informe y evidencia](../docs/evidencias/P4/cierre-20261022/README.md). 212 pytest +54 Vitest, TypeScript/build/audit y restart correctos. Próximo paso: esperar instrucciones; P5/P6 siguen prohibidos.
