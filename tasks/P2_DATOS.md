# P2 — Datos y capacidades | Codex por checkpoints

**Autorizado por el usuario (2026-10-14):** comenzar P2 en la misma ejecución que la corrección final P1, con checkpoints verificables y preservación del código LOCAL. **No habilitar órdenes; PAPER ONLY; coste adicional 0 EUR; STOP antes de P3.**

**Catálogo ampliado obligatorio:** [34 modalidades de ~31 fuentes y estrategia de conexión](../docs/P2_CATALOGO_MAXIMO_FUENTES.md). **Guía técnica detallada:** [docs/PLAN_P2_CHECKPOINTS.md](../docs/PLAN_P2_CHECKPOINTS.md). **Coordinación con P1:** [docs/PLAN_EJECUCION_P1_P2.md](../docs/PLAN_EJECUCION_P1_P2.md). Leer solo el checkpoint activo, no todas las fases futuras.

| Checkpoint | Objetivo | Gate |
|---|---|---|
| P2.0 | Preflight local, fuentes/derechos/licencias, opt-in de red y matriz de proveedores | No perder cambios locales, no credenciales expuestas |
| P2.1 | Registry multiactivo, aliases, capacidades RESEARCH/VALUATION/INTERNAL_PAPER/BROKER_PAPER | Alembic incremental, identidad no ambigua |
| P2.2 | Observaciones Decimal/UTC, procedencia, cache, cuotas, stale y errores | Sin precio huérfano, sin cuotas violadas |
| P2.3 | 19 candidatas públicas A por sublotes: España/Europa, macro mundial/US, cripto/identidad/noticias | Parsers/test mocks; fuente oficial etiquetada |
| P2.4 | 15 candidatas B con key/registro/free tier condicionado, por sublotes; sin clave NO_CREDENTIALS | Sin claves → NO_CREDENTIALS; sin live/órdenes/derechos supuestos; POST estadístico read-only solo OpenFIGI/BLS allowlisted |
| P2.5 | Selección de datos y panel Sistemas/Data Quality real | Sin NAV, P&L, cartera o actividad P4 ficticia |
| P2.6 | Tests, auditoría, seguridad, documentación y STATUS | P0 protegido; STOP antes de P3 |

**Regla:** sin credenciales, implementar adaptadores y mocks pero **no afirmar que hay feed real**. Datos públicos con fuente, fecha, unidades, licencia y calidad; los derechos de visualización y almacenamiento se verifican, no se presuponen. No confundir curva Treasury con precio de bono, FX de referencia ECB con spot, IEX con SIP ni cuentas demo con MASTER. Ejecutar check/audit/diff y documentar resultados reales.

## Ampliación de diseño para futura fábrica cuantitativa · 2026-10-23

**Este ticket P2.0–P2.6 es histórico; P3 ya se implementó y la instrucción «STOP antes de P3» no describe el estado vigente.** La nueva ampliación de datos point-in-time **no está implementada ni autorizada como Goal**. P5/P6 permanecen sin autorización.

Para un futuro Goal P2 de readiness, separar `RESEARCH_READY`, `BACKTEST_READY` y `EXECUTION_SIM_READY` por instrumento, fuente, universo y periodo. Historial P2 con procedencia y derechos **no** implica `BACKTEST_READY`.

Requisitos por estrategia: publicación y disponibilidad real (`period_end`, `published_at`, `available_to_strategy_at`, `restatement_version`, `source`, `retrieved_at`, `rights`), snapshots de universo histórico incluidos deslistados, calendarios, corporate actions, FX, ajustes compatibles con ejecución y costes/liquidez. Cada ausencia debe producir abstención `NOT_BACKTEST_READY`, no datos inventados.

**Tests futuros:** un dato publicado después de la fecha simulada es invisible; un delisted permanece en el universo de su fecha; los derechos y el hash del snapshot se respetan; el readiness se invalida si falta una capacidad requerida. Primero fixtures sintéticos; después fuentes reales autorizadas y sin afirmar alfa. Ver [realineación](../docs/REALINEACION_FONDO_AUTONOMO_2026_10_23.md).
