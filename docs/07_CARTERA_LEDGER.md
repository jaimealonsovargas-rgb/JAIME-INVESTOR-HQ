# Ledger maestro EUR, rentabilidad y auditoría

> **P3 autorizado 2026-10-16.** Implementación vinculante: [PLAN_P3_LEDGER_CARTERA_Y_HUD.md](PLAN_P3_LEDGER_CARTERA_Y_HUD.md). STOP antes de P4.

Semilla maestra: 10.000,00 EUR **virtuales**, creada una sola vez mediante evento idempotente `DEPOSIT_VIRTUAL`. Las cuentas de Alpaca Paper y Trading 212 Demo son scopes separados y NO se suman como efectivo maestro. Decimal end-to-end, timestamps UTC, identificadores y referencias. Nunca `float` financiero.

## Eventos
DEPOSIT_VIRTUAL, ORDER_RESERVED, FILL_BUY, FILL_SELL, FEE, FX_CONVERSION, DIVIDEND, COUPON, INTEREST_ACCRUAL, BOND_REDEMPTION, SPLIT, MERGER, RECONCILIATION_ADJUSTMENT. Registrar asientos append-only; no sobrescribir historia. Cada evento debe ser idempotente y, cuando use doble entrada, cumplir débitos = créditos.

En P3, la cartera real del usuario solo necesita la aportación virtual y la valoración. BUY/SELL/FILL se preparan y prueban únicamente con fixtures aislados para P6; `POST /api/orders` sigue 403.

## Posiciones
Lotes FIFO, coste unitario y total, cantidad restante, fills parciales, costes, divisa nativa, FX de compra/venta y de valoración, precio fuente y timestamp. Separar P&L realizado/no realizado, efecto precio y efecto FX. No vender más cantidad de la disponible (sin short en V1). Preferir posiciones derivadas de lotes/ledger; cualquier materialización debe reconciliarse.

## NAV y rendimiento
NAV = caja EUR + valor EUR de posiciones + accruals aplicables − pasivos. No sumar P&L a NAV por segunda vez. La aportación inicial de 10.000 EUR es flujo externo, no beneficio. Retornos con tratamiento correcto de flujos y ventanas temporales; TWR/MWR solo con series suficientes. Si precio o FX es stale/falta, marcar valoración STALE/NO_DATA/ESTIMATED, nunca cero inventado. Reconcilia inventario y caja con shadow brokers sin mezclarlos.

## Historia por operación
Tesis/version, agentes, comité, veto, orden, fills, fechas, qty, coste, comisión, P&L EUR/% en cierres parciales/totales, invalidación y postmortem. Esta trazabilidad se activa completamente en P4–P6; P3 deja contratos y dominio listos sin fingir actividad.

## UI P3

- Rail izquierdo: Watchlist/Market Pulse con datos P2.
- Rail derecho: Cartera/Posiciones/Actividad/Mapa.
- Videowall: Cartera MASTER, Posiciones, NAV/caja/rentabilidad reales de simulación; Operaciones sigue P6 pendiente.

Ver criterios, endpoints, tests e invariantes en [PLAN_P3_LEDGER_CARTERA_Y_HUD.md](PLAN_P3_LEDGER_CARTERA_Y_HUD.md).
