# Realineación arquitectónica: research autónomo local

**Decisión de diseño aprobada el 2026-10-23.** JAIME aspira a trabajar mientras el PC/backend estén encendidos. P4 investiga y documenta; la oficina observa. Este documento no habilita P5, P6, brókeres ni órdenes. La auditoría aportada por el usuario es una propuesta de dirección; sus afirmaciones sobre proveedores, estadística y regulación requieren verificación primaria antes de implementarlas.

## Dependencias y puertas

```text
P2 datos + derechos ─┬─> P4 research y crítica ──┐
                    └─> P5 factory Python futura ─┼─> P6 PAPER futuro
P3 ledger ficticio ────────────────────────────────┘
```

- P2 distingue investigación de aptitud para backtesting point-in-time y simulación de ejecución. Una serie histórica aislada no certifica un universo ni ausencia de sesgos.
- P4 conserva 30 `role_id`, capacidad 1 LLM / 2 quant / 4 fetch y trabajos persistentes. Su resultado son hipótesis, evidencia y límites, nunca señales ejecutables. El modo ordinario determinista funciona sin LLM; Bull/Bear/Chair son una revisión profunda explícita y cara.
- P5 futuro tendrá StrategyStore/Service propios: genome validado, registro completo de ensayos y descartes, backtest Python, validación adversarial y veto de riesgo. Puede funcionar sin LLM; el LLM solo propone o critica después de gates deterministas. No se inicia con esta decisión.
- P6 futuro será un OMS e InternalPaperBroker aislados de los agentes; requiere una nueva autorización. `POST /api/orders=403` y MASTER ficticio sin mutaciones P4 siguen vigentes.
- La oficina 3D no agenda trabajos ni decide permisos. El backend informa actividad auténtica a la UI. PC apagado implica cero ejecución local.

## Contrato propuesto P4: eventos y tareas

`ResearchCase` manual y sus runs históricos conservan identidad y significado. El origen autónomo será una entidad adicional versionada, con política *deny by default*. Una tarea podrá apuntar a un caso P4 o a otro sujeto de investigación sin exigir texto introducido por una persona.

```json
{
  "schema_version": "autonomy-event.v1",
  "event_id": "uuid",
  "trigger_type": "SCHEDULED_RESEARCH | NEW_DATA_AVAILABLE | NEW_FILING | REGIME_CHANGE | STRATEGY_DEGRADATION | PAPER_RESULT | POSTMORTEM_DUE",
  "occurred_at": "UTC",
  "observed_at": "UTC",
  "source_ref": "referencia interna y hash verificables",
  "subject": {"kind": "INSTRUMENT | UNIVERSE | STRATEGY | DATASET", "id": "id verificado"},
  "idempotency_key": "hash estable del trigger, sujeto y ventana",
  "parent_event_id": null,
  "rights": "política de lectura comprobada",
  "status": "NEW | ROUTED | BLOCKED | CANCELLED"
}
```

```json
{
  "schema_version": "research-task.v1",
  "task_id": "uuid",
  "origin_event_id": "uuid",
  "objective": "DATA_QUALITY | DESCRIPTIVE_RESEARCH | HYPOTHESIS_REVIEW",
  "subject_ref": "id verificado",
  "depth": "ordinary | deep",
  "role_ids": ["data_quality"],
  "required_capabilities": ["P2_RESEARCH"],
  "evidence_refs": [],
  "priority": 10,
  "budget": {"llm_calls_max": 0, "deadline_seconds": 90},
  "state": "QUEUED | RUNNING | SUCCEEDED | INCOMPLETE | BLOCKED | CANCELLED"
}
```

El router determinista valida fuente, derechos, frescura, sujeto, capacidad, idempotencia y límites antes de crear jobs. Un evento sin datos adecuados se registra como `BLOCKED/NO_DATA`; nunca se rellena con un precio o señal imaginarios. Los triggers `STRATEGY_DEGRADATION` y `PAPER_RESULT` son solo tipos reservados: ningún productor P5/P6 existe ahora. No se configura un reloj que genere automáticamente análisis indiscriminados. El futuro scheduler debe ser local, de baja frecuencia, auditable y capaz de recuperar eventos sin duplicarlos tras reinicio.

## Persistencia futura y pruebas de aceptación

Antes de activar eventos, añadir migración posterior a `0005_data_history` para `autonomy_events` y `research_tasks`, con claves únicas de idempotencia, referencias al origen, versión, estados, timestamps y hashes. No mezclar con `agent_jobs` ni con el ledger financiero. Módulos futuros propuestos: `backend/app/autonomy_contracts.py`, `autonomy_store.py`, `research_router.py`, `autonomy_scheduler.py`; tests correspondientes por contrato, reinicio, duplicados, derechos, cuota, ausencia de modelo, abstención, aislamiento de MASTER y orden 403. La UI solo necesitará consultas de estado, sin generar el trabajo por renderizar o abrir paneles.

Gates P4: caso ordinario con datos reales y cálculo Python; ausencia de datos sin cifras inventadas; caso profundo explícito con Bull/Bear/Chair y validación financiera, o `INCOMPLETE/BLOCKED` honesto. Gates futuros P5/P6: point-in-time por universo; todos los ensayos registrados; OOS y genealogía; OMS idempotente y conciliación. No se trasladan estos gates futuros a tests falsamente superados en P4.

Referencia de diseño: [Plan_JAIME_P5_P6](Plan_JAIME_P5_P6.md). Las recomendaciones de IBKR, Alpaca, Binance y cualquier futura fase live no son integración ni aprobación vigente.
