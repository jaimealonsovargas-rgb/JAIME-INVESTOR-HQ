# Investigación UI de terminales — HUD lateral P3

**Fecha:** 2026-10-16. Objetivo: decidir qué información tiene sentido en los paneles negros laterales de JAIME INVESTOR HQ sin convertirlos en decoración ni adelantar P6.

## Referencias oficiales revisadas

### Interactive Brokers — TWS Mosaic

Documentación oficial:
- https://www.interactivebrokers.com/en/?f=/en/general/education/pdfnotes/WN-TWSMosaic.php
- https://www.interactivebrokers.com/en/trading/tws.php
- https://www.interactivebrokers.com/campus/trading-lessons/tws-beginners-course-intro/

Patrones observados:
- Mosaic agrupa en un mismo workspace **portfolio, watchlists, quotes, charts, news y order/activity monitoring**.
- La watchlist muestra de un vistazo último precio, cambio y % cambio.
- Portfolio muestra posiciones, precio, market value, average price y P&L.
- Activity separa orders/trades/summary para monitorizar actividad sin mezclarlo con la watchlist.
- Los paneles se enlazan por símbolo/contexto y son redimensionables.

### TradingView — Watchlists y alerts

Documentación oficial:
- https://www.tradingview.com/support/solutions/43000739708-watchlist-alerts-your-trading-edge/
- https://www.tradingview.com/support/solutions/43000520149-introduction-to-tradingview-alerts/

Patrones observados:
- Una watchlist sirve como superficie compacta de seguimiento de múltiples símbolos.
- Las alertas pueden aplicarse a una watchlist y operar independientemente por símbolo.
- El valor de este rail es **situational awareness**, no ejecución directa.

## Decisión para JAIME INVESTOR HQ

### Rail izquierdo = WATCHLIST / MARKET

Motivo: es información de consulta rápida y cambia con el contexto de mercado, no con la contabilidad de cartera.

Contenido P3:
- símbolo/nombre corto;
- último precio;
- cambio diario %;
- freshness/status;
- fuente;
- pequeño Market Pulse con 2–4 referencias.

No incluir botón BUY/SELL durante P3. Un click solo abre detalle/cambia contexto.

### Rail derecho = PORTFOLIO / ACTIVITY / MAP

Motivo: portfolio y actividad pertenecen al estado de la cuenta/cartera, no al mercado general.

Tabs P3:
- **Cartera:** NAV, cash, invertido %, P&L, calidad de valoración.
- **Posiciones:** top 5 por peso; al inicio, sin posiciones y 10.000 EUR en caja.
- **Actividad:** eventos de ledger. Orders/fills quedan bloqueados hasta P6.
- **Mapa:** conservar minimapa existente como tab/botón.

### Videowall = vista ejecutiva

No duplicar tablas completas. Debe mostrar resumen: NAV/cash/performance, top positions y estado de mercados/noticias. Rails = información operativa compacta; videowall = visión ejecutiva; paneles de departamentos = análisis profundo.

## Regla de densidad

- máximo 6–10 filas visibles de watchlist;
- top 5 posiciones en rail;
- tipografía grande y contraste alto;
- stale/no-data claramente visible;
- no repetir toda la información del videowall;
- no usar datos ficticios para “llenar” huecos.

Esta decisión se implementa en `docs/PLAN_P3_LEDGER_CARTERA_Y_HUD.md` y `docs/20_UI_Y_FLUJOS.md`.
