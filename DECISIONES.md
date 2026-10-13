# Registro de decisiones arquitectónicas (ADR simplificado)
- D001: Local-first para 0 EUR obligatorios; no prometer servicio 24/7 con PC apagado.
- D002: React/R3F para 3D + FastAPI para datos y workers + SQLite WAL para persistencia local.
- D003: Maestro de 10.000 EUR virtuales separado de balances de cuentas demo.
- D004: Capacidad por instrumento y proveedor; no confundir investigación con ejecución.
- D005: Sol para implementación incremental; Astra para arquitectura/finanzas/riesgo/auditoría; cambio de modelo manual.
- D006: No se requiere LLM remoto: los trabajos deterministas tienen valor por sí mismos.
- D007: Las imágenes Runway son referencias, no GLB, y deben exportarse antes de uso offline.
- D008: La calidad visual 3D es criterio de aceptación de P1, no deuda técnica aplazada.
- D009: En P6, una orden de estado UNKNOWN nunca se reenvía sin conciliación.
