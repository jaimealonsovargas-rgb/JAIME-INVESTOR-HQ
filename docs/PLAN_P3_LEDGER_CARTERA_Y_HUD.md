# P3 — Ledger MASTER, cartera, valoración y HUD profesional

> **Autorizado 2026-10-16.** P3 convierte la base P2 en una cartera virtual contablemente consistente. **No implementa órdenes ni agentes. STOP antes de P4.**

## 0. Objetivo

Crear una cartera maestra de **10.000,00 EUR virtuales**, auditable y reproducible, cuyo NAV y P&L se calculen con datos P2 reales y trazables. La cartera MASTER es la única fuente de verdad financiera de la simulación; saldos de Alpaca Paper/T212 Demo u otros scopes nunca se suman al efectivo MASTER.

## 1. Principios no negociables

- PAPER ONLY, coste adicional 0 EUR, secretos fuera del repo.
- Decimal end-to-end; **nunca `float` para dinero, cantidad, precio o FX**.
- Ledger **append-only** e idempotente: no editar ni borrar historia para “arreglar” resultados.
- Cada evento debe ser trazable a `source_ref`, actor, timestamp UTC y, cuando aplique, observación/FX P2.
- Una valoración sin precio/FX válido queda `NO_DATA`, `STALE` o `ESTIMATED`; nunca sustituir por cero.
- `POST /api/orders` permanece **403** y `orders_enabled=false` durante todo P3.
- No crear compras/ventas reales ni paper en P3. Los casos de BUY/SELL/FILL se prueban con fixtures aislados para preparar P6, pero la cartera de usuario empieza con caja y **sin posiciones**.

## 2. Modelo contable y datos

### 2.1 Entidades

Reutilizar/adaptar el esquema existente antes de crear duplicados:

- `portfolios`: MASTER, moneda base EUR, estado, `seed_virtual`.
- `accounts`: como mínimo `CASH_EUR`, y cuentas auxiliares por divisa cuando existan eventos futuros.
- `ledger_events`: evento económico inmutable, tipo, moneda, importe, `source_ref`, `occurred_at`, hash/metadata.
- `ledger_entries`: doble entrada; por evento debe cumplirse **débitos = créditos**.
- `lots`: lotes por instrumento para FIFO, cantidad original/restante, coste, divisa, FX y fecha.
- `valuation_snapshots`: NAV, caja, valor de mercado, P&L, calidad/frescura y referencias de precio/FX.
- posiciones: preferentemente **derivadas** de lotes/eventos; si se materializan por rendimiento, deben reconciliarse contra ledger/lotes.

### 2.2 Semilla inicial

Crear una sola vez un evento `DEPOSIT_VIRTUAL` de **10.000,00 EUR**. Debe ser idempotente: reinicios, migraciones o doble ejecución no pueden duplicar el capital.

Estado inicial esperado tras P3 init:
- cash EUR = 10.000,00
- market value = 0,00
- liabilities = 0,00
- NAV = 10.000,00
- posiciones = 0
- rentabilidad desde la aportación inicial = 0,00 %, porque la aportación externa no es beneficio.

### 2.3 Tipos de evento preparados

`DEPOSIT_VIRTUAL`, `ORDER_RESERVED`, `FILL_BUY`, `FILL_SELL`, `FEE`, `FX_CONVERSION`, `DIVIDEND`, `COUPON`, `INTEREST_ACCRUAL`, `BOND_REDEMPTION`, `SPLIT`, `MERGER`, `RECONCILIATION_ADJUSTMENT`.

En P3 el usuario real solo necesita `DEPOSIT_VIRTUAL` y valoración; el resto se implementa como dominio/test donde sea razonable, **sin activar ejecución P6**.

## 3. Motor de posiciones, NAV y P&L

### 3.1 Lotes y FIFO

- Compras futuras crean lotes; ventas futuras consumen FIFO.
- Impedir cantidad restante negativa y ventas superiores a inventario; shorts fuera de V1.
- Cost basis por lote, fees y FX explícitos.
- Cierres parciales conservan trazabilidad de lotes consumidos.

### 3.2 Valoración

`NAV = caja en EUR + valor EUR de posiciones + accruals - pasivos`.

Para cada posición futura:
1. seleccionar observación P2 semánticamente compatible;
2. guardar `provider`, `observed_at`, `received_at`, venue/feed, quality y rights;
3. convertir a EUR con FX P2 compatible si hace falta;
4. separar efecto precio y efecto FX;
5. si precio/FX está stale o falta, mostrar el estado y no fingir un valor exacto.

No sumar P&L por segunda vez al NAV.

### 3.3 Rentabilidad

- P&L realizado y no realizado separados.
- Rentabilidad de cartera ajustada por flujos externos; la aportación de 10.000 EUR no es retorno.
- TWR cuando exista una serie suficiente; MWR/XIRR solo cuando haya flujos y datos suficientes.
- Daily return y period return con calendario/timestamps coherentes.
- Drawdown solo cuando exista historia de NAV suficiente; no fabricar series.

## 4. API P3 (solo lectura para UI)

Adaptar nombres a la arquitectura local existente; propuesta:

- `GET /api/portfolio/master/summary`
- `GET /api/portfolio/master/positions`
- `GET /api/portfolio/master/ledger`
- `GET /api/portfolio/master/nav/history`
- `GET /api/portfolio/master/performance`
- extender `GET /api/hq/overview` con módulos P3.

No exponer endpoint UI para editar saldo, insertar fills o cambiar NAV. La inicialización se hace por migración/servicio/CLI idempotente, no por un botón peligroso.

## 5. HUD lateral profesional — decisión de producto

La oficina tiene paneles negros laterales. Deben evolucionar a un **cockpit de monitorización**, no a decoración.

### 5.1 Rail izquierdo — WATCHLIST / MARKET

Basado en patrones comunes de terminales profesionales: las watchlists suelen mostrar último precio, cambio y % cambio; plataformas como IBKR Mosaic enlazan watchlist, quotes, charts, news y portfolio, y TradingView permite alertas sobre listas completas.

Mostrar, cuando P2 lo soporte:
- Watchlist compacta: ticker/nombre corto, último, cambio diario %, estado de frescura y fuente.
- 6–10 símbolos máximo visibles; scroll/paginación para no saturar.
- selector de watchlist futura (`CORE`, `OPPORTUNITIES`, `PORTFOLIO`) pero sin agentes P4 todavía.
- Market pulse compacto: 2–4 referencias relevantes (índice/FX/tipo/cripto según disponibilidad y derechos).
- alertas **solo informativas** P2; nada dispara órdenes.
- click en símbolo puede abrir ficha/read-only o cambiar contexto del panel de Research/Trading, sin enviar acciones financieras.

### 5.2 Rail derecho — PORTFOLIO / ACTIVITY

En P3 debe sustituir parte del minimapa estático por una vista tabulada/colapsable, manteniendo el minimapa accesible.

Tabs sugeridas:
- **CARTERA P3:** NAV, caja, invertido %, P&L día/acumulado, nº posiciones, estado de valoración.
- **POSICIONES P3:** top 5 por peso con precio/fuente/estado cuando existan; al inicio “Sin posiciones · 10.000 EUR en caja”.
- **ACTIVIDAD:** eventos de ledger relevantes. En P3 mostrará aportación virtual, dividendos/cupones/reconciliaciones cuando existan; **órdenes/fills permanecen P6 — NO DISPONIBLE**.
- **MAPA:** conserva el mini mapa 3×3 actual como tab o botón.

Cuando llegue P6, `ACTIVIDAD` puede evolucionar a blotter de órdenes/trades con estados, pero P3 no debe inventar operaciones.

### 5.3 Videowall

P3 activa de verdad:
- Cartera MASTER
- Posiciones
- NAV/caja/rentabilidad

Y mantiene:
- Mercados/noticias P2 si válidos
- Operaciones P6 = pendiente
- Riesgo P5 = pendiente
- Comité/agentes P4/P5 = pendiente

La tipografía del videowall debe ser DOM/SDF de alta resolución o textura suficientemente nítida; no sacrificar legibilidad por FPS. La nitidez visual puede mejorarse en P3 siempre que no reabra el layout 3D.

## 6. Checkpoints ejecutables

### P3.0 — preflight y regresión
- `git status --short`, branch/log/diff, confirmar remoto limpio.
- ejecutar tests esenciales P1/P2 y seguridad PAPER ONLY.
- inspeccionar migraciones/modelos actuales antes de añadir tablas.

### P3.1 — dominio y migración
- portfolio MASTER + evento inicial idempotente 10.000 EUR.
- ledger events/entries, invariantes de doble entrada y Decimal.
- migración reversible y backup de SQLite.

### P3.2 — posiciones/lotes/FX
- FIFO y cost basis con fixtures aislados.
- soporte multi-divisa/FX de valoración y compra/venta preparado.
- tests de parciales, fees, dividends, coupons, split y redemption donde corresponda.

### P3.3 — valoración/NAV/performance
- snapshots reproducibles, price provenance, stale/no-data.
- P&L, TWR básico cuando haya serie suficiente; evitar métricas sin muestra.
- reconciliación ledger → cash/lots → NAV.

### P3.4 — APIs read-only
- summary, positions, ledger, NAV history/performance.
- paginación/filtros estables; schemas tipados.
- no endpoints de mutación financiera desde frontend.

### P3.5 — HUD/videowall
- rail izquierdo Watchlist/Market P2.
- rail derecho Portfolio/Positions/Activity/Map.
- videowall P3 con datos MASTER reales de simulación.
- estados claros: LIVE-DATA/STALE/NO DATA/PENDING PHASE.

### P3.6 — QA y cierre
- tests unitarios/integración/E2E de invariantes, reinicio idempotente, offline/stale y backup/restore.
- `python scripts/manage.py check`, `python scripts/manage.py audit`, `git diff --check`, build frontend.
- verificar `POST /api/orders = 403` y ninguna llamada externa de ejecución.
- capturas de rail izquierdo, rail derecho, videowall y panel Performance/Trading.
- actualizar `STATUS.md` y entregar commits/evidencias.
- **STOP antes de P4.**

## 7. Tests financieros mínimos

- semilla ejecutada 2 veces sigue en 10.000,00 EUR, no 20.000.
- por evento: sum(debits) == sum(credits).
- cash y qty nunca negativos en V1 salvo fixture explícito rechazado.
- FIFO correcto con dos lotes y venta parcial.
- fee reduce cash/P&L una sola vez.
- FX conversion conserva equivalencia según rate y redondeo definido.
- dividend/coupon no aumenta cantidad de posición.
- split cambia qty/coste unitario sin crear P&L económico artificial.
- NAV no suma P&L por duplicado.
- stale quote/FX marca valoración stale y no inventa cero.
- restart/rebuild produce el mismo NAV desde el mismo ledger.
- cuenta demo externa no altera MASTER.

## 8. Criterio de terminado

P3 está terminado cuando la app puede reconstruir de forma determinista la cartera MASTER desde el ledger, mostrar 10.000 EUR iniciales sin doble conteo, valorar posiciones futuras con procedencia P2, presentar NAV/P&L coherentes, alimentar HUD/videowall con datos reales de simulación y mantener ejecución completamente bloqueada.

**P4 no se inicia automáticamente.**
