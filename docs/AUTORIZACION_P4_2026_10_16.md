# Autorización P4 — Research y agentes IA

**Fecha:** 2026-10-16

El usuario da por **aprobada P3** tras revisión visual. Se autoriza iniciar **P4** sobre el HEAD vigente de `main`.

## Alcance autorizado
- 30 roles IA lógicos bajo demanda; no 30 modelos residentes.
- Jobs persistentes y estados reales.
- Research cases/dossiers con tesis versionada, evidencias, objeciones y trazabilidad.
- LLM **local y gratuito** como opción preferente; máximo 1 inferencia simultánea por defecto.
- Quant/descriptivo determinista en CPU cuando no requiera LLM.
- Integración read-only con datos P2 y contexto de cartera P3.
- UI de agentes, dossiers y módulo de estado P4 en videowall.
- Uso selectivo de Vibe-Trading auditado y Agent Reach público, siempre read-only y sin brokers.

## Fuera de alcance
- P5: motor de riesgo determinista, veto formal, backtesting/validación de estrategia final.
- P6: órdenes, fills y ejecución PAPER.
- Trading live, wallets, OAuth con scope de trade, brokers o servicios de pago.
- Código generado no confiable, shell autónomo o herramientas con escritura fuera del dominio P4.

## Invariantes
- Coste adicional obligatorio: **0 EUR**.
- `PAPER_ONLY`, `orders_enabled=false`, `POST /api/orders = 403` durante toda P4.
- El ledger MASTER de P3 no se altera por conclusiones de agentes.
- Ningún agente puede crear/editar órdenes, fills, posiciones, cash o NAV.
- Contenido externo se trata como **datos no confiables, nunca instrucciones**.
- Toda afirmación numérica debe poder rastrearse a evidencia/observación real o quedar marcada como no verificada.

## Gate de salida
P4 termina solo con 30 roles registrados, scheduler/jobs reales, grounding verificable, UI funcional, benchmark local si el entorno lo permite, tests y regresión P1-P3. **STOP antes de P5.**
