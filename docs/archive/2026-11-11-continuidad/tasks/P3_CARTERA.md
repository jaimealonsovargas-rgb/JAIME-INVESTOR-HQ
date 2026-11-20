> ARCHIVO INACTIVO · copia anterior a la auditoría del 11-11-2026. Sus próximos pasos y autorizaciones no gobiernan el trabajo actual. Enlaces relativos reubicados; contenido histórico conservado.

> REFERENCIA DE FASE. La cola activa está en [ACTUAL](ACTUAL.md) y [ROADMAP](ROADMAP.md); [STATUS](../STATUS.md) declara capacidad actual. P5 autorizada posteriormente con mejoras previas; P6 pendiente. Conservar los requisitos útiles; no ejecutar STOP o aprobaciones históricos ya superados.



# P3 — Ledger MASTER EUR, cartera, valoración y HUD | Astra diseño/finanzas; Sol implementación



**Autorizado 2026-10-16. STOP antes de P4.** Fuente vinculante: `docs/PLAN_P3_LEDGER_CARTERA_Y_HUD.md` y `docs/AUTORIZACION_P3_2026_10_16.md`.



## Objetivo



Sembrar **una sola vez** 10.000,00 EUR virtuales en la cartera MASTER y construir ledger append-only, doble entrada, Decimal, posiciones/lotes FIFO, FX, fees, dividendos, cupones, corporate actions, NAV, P&L, snapshots y rentabilidad trazable. La valoración consume datos P2 reales y conserva proveedor/timestamp/calidad/derechos. Las cuentas paper externas son scopes separados y nunca se suman al MASTER.



## UI P3



- **Rail izquierdo:** Watchlist/Market Pulse con datos P2, último/cambio/frescura/fuente y sin acciones de trading.

- **Rail derecho:** tabs Cartera / Posiciones / Actividad / Mapa. Actividad P3 muestra ledger; órdenes/fills siguen `P6 — NO DISPONIBLE`.

- Videowall activa Cartera MASTER, Posiciones, NAV/caja/rentabilidad; mercados/noticias P2 continúan; P4/P5/P6 siguen pendientes.

- Mejorar nitidez del videowall si es posible sin reabrir layout 3D ni degradar rendimiento.



## Gates



P3.0 preflight/regresión → P3.1 dominio+migración+seed idempotente → P3.2 FIFO/FX/corporate-action fixtures → P3.3 NAV/performance/provenance → P3.4 API read-only → P3.5 HUD/videowall → P3.6 QA/backup/evidencia.



## Invariantes



`POST /api/orders = 403`, `orders_enabled=false`, PAPER ONLY, 0 EUR, no agentes P4, no riesgo P5, no ejecución P6. No usar precios inventados como mercado real; stale/no-data se muestran explícitamente. No `float` financiero.

