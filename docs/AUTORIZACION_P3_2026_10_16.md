# Autorización P3 — 2026-10-16

El usuario **autoriza iniciar P3** una vez cerradas las regresiones P1/P2 ya realizadas. Esta decisión sustituye únicamente el antiguo `STOP antes de P3` de documentos históricos; las invariantes de seguridad y coste siguen vigentes.

## Alcance autorizado

- Crear el **ledger MASTER de 10.000,00 EUR virtuales** en moneda base EUR.
- Implementar cartera, caja, posiciones derivadas, lotes FIFO, coste, NAV, P&L, FX, dividendos/cupones/corporate actions preparados, snapshots y rentabilidad con trazabilidad.
- Conectar la valoración **solo** a observaciones P2 válidas y con procedencia/frescura; nunca inventar precios.
- Integrar P3 en videowall y HUD lateral sin romper la oficina 3D ni P2.
- Reservar los paneles laterales negros para información profesional: **Watchlist/mercado a la izquierda** y **Cartera/actividad a la derecha**, con módulos futuros de órdenes/fills P6 claramente bloqueados hasta esa fase.
- Mantener `POST /api/orders = 403`, `orders_enabled=false`, PAPER ONLY y coste adicional 0 EUR.

## Fuera de alcance

- **P4:** agentes IA/scheduler/Vibe operativo.
- **P5:** motor de riesgo/comité/backtests operativos.
- **P6:** órdenes, fills o compraventas paper.
- Cualquier trading live, cuenta real, OAuth con permisos de trading o gasto de servicios.

**STOP antes de P4.** Fuente técnica vinculante: `docs/PLAN_P3_LEDGER_CARTERA_Y_HUD.md` y `tasks/P3_CARTERA.md`.
