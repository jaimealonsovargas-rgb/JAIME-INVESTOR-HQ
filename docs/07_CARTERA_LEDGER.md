# Ledger maestro EUR, rentabilidad y auditoría

Semilla maestra: 10.000,00 EUR **virtuales**. Las cuentas de Alpaca Paper y Trading 212 Demo son scopes separados y NO se suman como efectivo maestro. Decimal end-to-end, timestamps UTC, identificadores y referencias.

## Eventos
DEPOSIT_VIRTUAL, ORDER_RESERVED, FILL_BUY, FILL_SELL, FEE, FX_CONVERSION, DIVIDEND, COUPON, INTEREST_ACCRUAL, BOND_REDEMPTION, SPLIT, MERGER, RECONCILIATION_ADJUSTMENT. Registrar asientos append-only; no sobrescribir historia.

## Posiciones
Lotes FIFO, coste unitario y total, cantidad restante, fills parciales, costes, divisa nativa, FX de compra/venta y de valoración, precio fuente y timestamp. Separar P&L realizado/no realizado, efecto precio y efecto FX. No vender más cantidad de la disponible (sin short en V1).

## NAV y rendimiento
NAV = caja EUR + valor EUR de posiciones + accruals aplicables − pasivos. No sumar P&L a NAV por segunda vez. Retornos con tratamiento correcto de flujos y ventanas temporales; no calcular métricas con series insuficientes. Reconcilia inventario y caja con shadow brokers sin mezclarlos.

## Historia por operación
Tesis/version, agentes, comité, veto, orden, fills, fechas, qty, coste, comisión, P&L EUR/% en cierres parciales/totales, invalidación y postmortem. Si precio es stale, indicar NAV estimado y bloquear nuevas órdenes.
