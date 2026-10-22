# P6 — ejecución autónoma PAPER | diseño futuro, NO AUTORIZADO

La primera implementación autorizada en su momento deberá ser un `InternalPaperBroker` reproducible y un OMS separado de research/LLM. Flujo previsto: estrategia validada → objetivo de cartera → intención → riesgo determinista → OMS → fill PAPER → ledger MASTER → conciliación. El LLM, la oficina y los NPC no tienen permiso de enviar órdenes ni mutar cartera.

La máquina de estados incluirá idempotencia, fills parciales, cancelación, rechazo y `UNKNOWN`; tras `UNKNOWN` se bloquean reenvíos hasta conciliación. Cualquier discrepancia en posiciones/caja detiene nuevas órdenes. Un adaptador externo futuro solo puede ser PAPER con credenciales aisladas y nueva autorización; disponibilidad, licencias y costes deben verificarse entonces. No existe switch PAPER/LIVE.

Hasta autorización P6: `orders_enabled=false`, `POST /api/orders=403`, ningún broker de ejecución conectado y MASTER ficticio sin cambios por P4. Véase `docs/ARQUITECTURA_AUTONOMIA_P4_P5.md`.
