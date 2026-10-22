# P4 — Research y agentes IA | autorizado 2026-10-16

**STOP antes de P5.** Fuente ejecutable: `docs/PLAN_P4_AGENTES_RESEARCH_LOCAL_AI.md`.

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

## Realineación aprobada de visión · 23-10-2026 (solo documentación)

La meta ya no se limita a research por preguntas: el backend debe poder iniciar investigación por reloj, datos y eventos **mientras esté encendido**, incluso con la oficina 3D cerrada. El estado actual sigue centrado en `ResearchCase.question` y P4 sigue **PARTIAL**. La realineación **no implica** que ya exista autonomía operativa.

**Próximo Goal P4, solo tras instrucción del usuario:** diseñar/implementar un puente mínimo `AutonomyEvent` → `ResearchRouter` → `ResearchTask`, sin sustituir los expedientes históricos. Primera iteración con trigger programado y una ruta de trabajo determinista real; estados persistentes, idempotencia, restart, cancelación, abstención, límites de recursos, auditoría y ejecución sin UI. Los triggers de filing, riesgo, resultados P5/P6 y brokers permanecen deshabilitados hasta disponer de fuentes y fases autorizadas.

El planificador debe seleccionar roles pertinentes en vez de invocar nueve roles y Bull/Bear/Chair por defecto. Una investigación ordinaria conserva datos/features Python y opcionalmente una síntesis LLM corta; un debate profundo sigue siendo opt-in o gate de promoción futuro, con validación semántica intacta. **No** repetir el debate fallido ni marcar P4 terminada por un JSON válido.

Tests de aceptación propuestos: `AUT-01` evento sin pregunta/UI; `AUT-02` recuperación sin duplicados; `AUT-03` LLM apagado con trabajos Python útiles; `AUT-04` datos insuficientes = abstención; `SEC` órdenes403/MASTER inalterado; RAM y latencia medidas, no supuestas. Mantener 30 roles y 1 LLM. Ver [contrato de realineación](../docs/REALINEACION_FONDO_AUTONOMO_2026_10_23.md).

**P5/P6 siguen NO AUTORIZADOS.**
