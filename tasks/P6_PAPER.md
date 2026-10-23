# P6 — OMS y ejecución autónoma PAPER exclusivamente

**ESTADO: NO INICIADO / NO AUTORIZADO (2026-10-23).** Especificación futura, **no** habilita endpoints ni credenciales. Requiere autorización P6 expresa y gates P5/P2/P3.

## Pipeline obligatorio

```text
Strategy aprobada -> PortfolioTarget -> TradeIntent
-> RiskEngine determinista -> ValidatedOrderIntent
-> OMS -> InternalPaperBroker -> Fill -> P3 MASTER ledger
-> Reconciliation -> Performance / Postmortem
```

`TradeIntent` **no es una orden**. UI, NPC, LLM y comité no envían órdenes ni pueden cambiar límites. Solo el OMS PAPER, tras veto de riesgo y capacidad del instrumento, puede ejecutar simulaciones autorizadas.

## P6A — InternalPaperBroker primero

- Contratos `BrokerAdapter` y `BrokerCapabilities`, adaptador interno reproducible, semántica de precio/coste/slippage/fill explícita y límites de cobertura.
- OMS persistente con estados `PROPOSED`, `RISK_ACCEPTED`, `READY_FOR_PAPER`, `SUBMITTED`, `ACKNOWLEDGED`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `REJECTED`, `UNKNOWN`, `RECONCILIATION_HALT`.
- Idempotencia end-to-end: un retry no duplica orden/fill; `UNKNOWN` obliga a reconciliar **antes** de reintentar. Desajuste de posiciones/caja o broker desconectado bloquea nuevas órdenes.
- Reconciliación con ledger MASTER ficticio, fills parciales, fees, FX y corporate actions compatibles con P3; auditoría completa.
- Kill switch bloquea nuevas órdenes; no implica venta/liquidación automática sin política explícita.

**Gate P6A:** fixtures de partial fills, duplicados, timeout UNKNOWN, reconcile mismatch, cash, stale data, riesgo, permisos y reinicio. No introducir adaptadores LIVE.

## P6B — adaptadores externos PAPER (autorización posterior)

Evaluar **IBKR PAPER** como destino multiactivo y **Alpaca PAPER** como alternativa/comparación, siempre tras verificar disponibilidad desde España, costes, datos, condiciones API, permisos y compatibilidad local. IB Gateway es una opción futura a medir, no dependencia instalada. Binance Testnet sería módulo crypto separado, no núcleo. No habilitar ninguna integración por defecto.

**Gate P6B:** aislamiento de credenciales, health/capabilities, reconciliación, estados UNKNOWN, pruebas sandbox PAPER reales y evidencia de 0 EUR obligatorios. No prometer funcionamiento 24/7 ni paper idéntico al mercado real.

## Prohibiciones vigentes

Hasta autorización e implementación aprobada: `orders_enabled=false`, `live_trading_enabled=false`, `POST /api/orders=403`, sin credenciales de ejecución, sin broker LIVE, sin dinero real, sin bypass desde LLM, frontend o variables de entorno. P8 LIVE sería otro proceso/fase/autorización independiente.

Fuente rectora: [Realineación 2026-10-23](../docs/REALINEACION_FONDO_AUTONOMO_2026_10_23.md). Diseño previo: [Plan P5/P6](../docs/Plan_JAIME_P5_P6.md).
