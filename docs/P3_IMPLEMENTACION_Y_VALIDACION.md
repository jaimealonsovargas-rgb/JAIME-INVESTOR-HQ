# P3 · MASTER, ledger y HUD financiero

Fecha de ejecución: 2026-10-16. Autorización: `AUTORIZACION_P3_2026_10_16.md`, plan P3 e issue #4. **STOP antes de P4**. Esta ejecución se realizó en Windows local, no en Cloud; cualquier evidencia de navegador indica su entorno real.

## Base y preservación

Se comprobó que `460c7e0` y todos los cambios/evidencias P1/P2 estaban en GitHub. Árbol inicial limpio. Avance rápido de once commits documentales hasta `901f6f05666e3f79f9ee6a8558e0bccd6fabcc5c`, sin reset, clean, force ni reconstrucción. STATUS histórico se conserva. Copia SQLite consistente previa: `output/p3-preflight/before-p3-20261016T094959Z.db`, integridad `ok`, esquema `0002_data`, 98 instrumentos. El backup contiene datos locales y **no se publica en Git**.

## Modelo contable

- Migración incremental `0003_portfolio`: `portfolios`, `ledger_events`, `ledger_entries`, `valuation_snapshots`. Las cuentas se identifican por `(account, currency)` en los asientos; lotes y posiciones se reconstruyen de eventos y no se duplican en una segunda tabla mutable.
- Diario append-only: triggers SQLite prohíben UPDATE/DELETE de las cuatro tablas. Cada lectura comprueba cadena SHA-256, sobre del evento y equivalencia exacta de asientos con replay. La cadena detecta corrupción; no se presenta como firma criptográfica contra un administrador que controle toda la base.
- Doble entrada **por moneda nativa**. FX usa cuentas puente por divisa; la valoración y los costes históricos EUR se derivan por separado. No se suman USD y EUR como si fueran la misma unidad. Reservas reclasifican efectivo disponible, sin reducir NAV.
- Serialización financiera en **TEXT/strings Decimal**, nunca SQLite REAL ni números JavaScript. Contexto financiero de 50 dígitos; presentación monetaria a céntimos con HALF_EVEN. Operaciones no terminantes quedan sujetas a ese contexto explícito. El último consumo FIFO absorbe el residuo exacto de cada lote; no acumula céntimos ficticios. En frontend se formatean strings/BigInt sin convertir dinero a Number.
- Seed transaccional con `BEGIN IMMEDIATE` y clave única `MASTER:DEPOSIT_VIRTUAL:v1`. MASTER solo admite el depósito fijo de 10.000,00 EUR por el inicializador durante P3. La inicialización simultánea/repetida preserva el evento y su timestamp originales.
- Soporte de dominio probado: reservas, compras/ventas, FIFO parcial, fees, FX, dividendos, devengo y liquidación de cupón, amortización, split, fusión canje de acciones y ajuste con evidencia. Compras/ventas son **fixtures aislados**, nunca registros de la cartera de usuario. Fusiones con efectivo, fiscalidad, shorts, préstamos y derivados quedan fuera de V1; no se finge soporte general de corporate actions.
- Comisiones de compra capitalizadas una vez en coste; comisiones de venta deducidas una vez del ingreso; FEE independiente reduce caja/gasto. El ledger idempotente no aplica dos veces la misma referencia. El P&L realizado de lotes, ingresos, comisiones independientes y efectos FX se identifican separadamente.
- Saldos demo externos no forman parte de MASTER. Prueba específica con `ALPACA_PAPER` en una base temporal.

## Valoración y performance

`NAV = caja EUR + valor de mercado EUR + devengos EUR − pasivos`. No se añade P&L otra vez. V1 no permite pasivos ni descubierto. Ausencia de precio/FX propaga `null` y `NO_DATA`; nunca cero. STALE puede conservar el último valor **etiquetado como desactualizado**. ESTIMATED conserva su marca. No hay acciones/bonos comprados en MASTER.

Selección P2: cache compatible con configuración actual, conexión real registrada, derechos de acceso/display/almacenamiento/redistribución, alias exacto de proveedor/símbolo/venue/divisa, capacidad explícita `valuation` activa y feed idéntico. No se mezclan IEX/SIP, referencias, yields ni precios en porcentaje de nominal. Las capacidades P2 existentes son de investigación: **no se han elevado a valoración por conveniencia**. La ausencia de instrumentos habilitados no afecta a una cartera EUR compuesta solo de caja.

FX disponible en el puente P3: observación BCE `A01`, unidad normalizada `USD/EUR`; EUR por USD = inversa Decimal. Otras divisas necesitan un feed y mapeo semántico verificados: `NO_DATA` mientras no existan. Se conserva observación completa: provider, instrumento, feed/venue, observed_at, received_at, flags, freshness, derechos, URL y hash del payload.

Snapshots reales en arranque y CLI; deduplicados por día UTC, estado, ledger e inputs. **GET no escribe snapshots ni consulta proveedores**. No hay scheduler P4. Comando manual para registrar un nuevo checkpoint de valoración: `python scripts/manage.py portfolio-snapshot`.

- Aportación inicial ≠ beneficio: retorno acumulado inicial 0%.
- Retorno acumulado exacto con una aportación inicial; con flujos posteriores sin valoraciones de frontera se devuelve null.
- Retorno diario solo con snapshot del día UTC anterior; sin rellenar fechas.
- TWR y drawdown solo con al menos tres fechas reales y sin flujos intermedios no valorados. Se muestra periodo de la serie disponible.
- XIRR Decimal: mínimo 30 días, flujos convencionales con un cambio de signo y raíz dentro del intervalo documentado de −99,99% a 10.000%; fuera de estas condiciones se devuelve null. No se presume cumplimiento GIPS ni se anualiza un día de historia.

Referencias primarias consultadas para precisión y tratamiento de flujos: [Python Decimal](https://docs.python.org/3/library/decimal.html) y [GIPS Handbook: metodología de retornos y flujos](https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/). La implementación utiliza criterios conservadores propios, no una certificación GIPS.

## API y UI

APIs GET: `/api/portfolio/master/summary`, `/positions`, `/ledger`, `/nav/history`, `/performance` bajo el mismo prefijo. Además `/api/markets/watchlist` y ampliación de `/api/hq/overview`. Ledger e historia paginados. No hay endpoints para editar saldo, insertar fills, posiciones o NAV, ni borrar eventos. Fallo de integridad del diario → HTTP503 sin servir un NAV plausible.

Rail izquierdo: CORE con consultas P2 autorizadas, selector OPPORTUNITIES/PORTFOLIO preparado sin agentes, datos/fuente/unidad/fechas por fila y Market Pulse. No hay un cierre diario comparable verificado en los presets actuales: cambio diario `N/D`, sin flechas ficticias. Máximo diez cotizaciones y cuatro referencias. **En esta entrega no hay cotizaciones redistribuibles en cache; no se inventan seis o diez filas.** Coinbase/CoinPaprika tienen derechos internos/personales que no permiten esta salida redistribuible; Kraken/Binance/CoinGecko mantienen las restricciones anteriores. No se reabrió la investigación de derechos P2 ni se hicieron consultas externas masivas.

Rail derecho: Cartera, Posiciones, Actividad y Mapa. NAV/caja/retornos de API, estado de valoración y timestamp. Actividad muestra el depósito virtual; órdenes/fills `P6 — NO DISPONIBLE`. Mapa conserva los nueve accesos. Tabs con flechas/Home/End y foco; juego responde solo cuando el canvas tiene foco. Raíles plegables y diseño 390px; se ocultan en inspección para no tapar el videowall. Recepción/Trading/Performance consumen la misma consulta deduplicada.

Videowall: misma geometría/posición/materiales de P1; nueve módulos. Cartera/posiciones activados desde ledger, performance solo cuando haya historia, mercados/noticias P2 conservados, P4/P5/P6 bloqueados. Diagnóstico anterior: texto rasterizado en CanvasTexture 1024×1536, mipmaps/anisotropía4, proyectado sobre módulos físicos pequeños y framebuffer DPR0,8. Subir resolución no elimina esa minificación. Se sustituyó el texto por **nueve superficies DOM transformadas** coincidentes con las pantallas; se liberan sus mapas de texto GPU. Textos financieros independientes del DPR, sin texturas enormes, cambios por frame ni cambios de cámara/layout. El centro de control sigue siendo la lectura accesible ampliada. A distancia las letras continúan limitadas por el tamaño proyectado; no se promete legibilidad de toda la metadata en una vista general.

## Operación, restauración y seguridad

Arranque: `python scripts/manage.py migrate`, después `python scripts/manage.py backend` y frontend según README. Inicialización/snapshot explícita opcional mediante `python scripts/manage.py portfolio-snapshot`. P3 no depende de claves ni internet.

Backup con `sqlite3.Connection.backup`, nunca copia en caliente solo del archivo ignorando WAL. Restauración se verifica en una DB separada: integrity_check, esquema, cantidades, hash y replay. Downgrade P3 vacío probado; downgrade con historia financiera falla sin borrarla. Para regresar a P2 se usa el backup previo verificado con el servicio detenido, no se destruye el diario.

Se mantienen PAPER ONLY, `orders_enabled=false`, POST `/api/orders`403, CORS/hosts locales y allowlists P2. Ninguna orden a bróker, OAuth, wallet, agente, ejecución Vibe/Liquid o servicio facturable. 0 EUR. **P4/P5/P6 no iniciados**.

## Evidencia y límites

Resultados finales y rutas de capturas en `docs/evidencias/P3/README.md` y `STATUS.md`. Los tests usan fixtures explícitos TEST_ONLY en bases temporales sin red. Las respuestas reales se guardan separadamente. La primera prueba de movimiento offline se descartó: Chrome limitaba el target ocluido a ~1 FPS. La repetición con `Emulation.setFocusEmulationEnabled` y entrada nativa pasa; esta condición se registra en los scripts/resultados, no se oculta.

El código P3 no reabre layout, NPC, controles, materiales, proveedores ni integraciones. Advertencias históricas de TestClient/httpx, THREE.Clock y tamaño del chunk 3D siguen separadas de errores. La aceptación visual subjetiva en el monitor del usuario y una sesión prolongada con su carga habitual permanecen pendientes.
