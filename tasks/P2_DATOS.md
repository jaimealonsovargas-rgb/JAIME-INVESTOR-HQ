# P2 — Datos y capacidades | Codex por checkpoints

**Autorizado por el usuario (2026-10-14):** comenzar P2 en la misma ejecución que la corrección final P1, con checkpoints verificables y preservación del código LOCAL. **No habilitar órdenes; PAPER ONLY; coste adicional 0 EUR; STOP antes de P3.**

**Catálogo ampliado obligatorio:** [34 candidatas y estrategia de conexión](../docs/P2_CATALOGO_MAXIMO_FUENTES.md). **Guía técnica detallada:** [docs/PLAN_P2_CHECKPOINTS.md](../docs/PLAN_P2_CHECKPOINTS.md). **Coordinación con P1:** [docs/PLAN_EJECUCION_P1_P2.md](../docs/PLAN_EJECUCION_P1_P2.md). Leer solo el checkpoint activo, no todas las fases futuras.

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