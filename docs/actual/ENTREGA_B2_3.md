# B2.3 — datos de mercado y lectura Alpaca PAPER

29-10-2026 · Europe/Madrid. Núcleo de lectura implementado y comprobado localmente. **Actualización 30-10: conexión real de lectura comprobada; ver cierre siguiente.** No se declara B2.3 plenamente aceptado, ni datos aptos para backtest o ejecución.

## Cierre de conexiones 30-10-2026

Claves incorporadas por el usuario al `.env`; ocho endpoints Alpaca probados con respuestas reales válidas. Catálogo de 14.407 activos; snapshot AAPL y 21 barras IEX de septiembre de 2026, sin huecos frente a 21 sesiones del calendario. La operación del snapshot estaba antigua a la hora de consulta y se muestra STALE. Corporate actions disponible para esa consulta, sin garantizar exhaustividad.

Trading 212 Demo devolvió HTTP 200: 500 instrumentos normalizados por el adaptador acotado; no representa un censo completo ni integración de cartera/órdenes. Secretos y datos privados de cuenta fuera de esta evidencia. [Registro saneado](evidencias/b23-real-connection.json).

El cierre cubre conexión y lectura por solicitud. Streaming, watchlist e identidad emisor/clase/divisa siguen pendientes; órdenes bloqueadas y ninguna certificación de backtest. El texto siguiente conserva el alcance y las pruebas de implementación del 29-10.

## Resultado

Centro de activos incorpora Mercado y cuenta simulada, acceso por endpoint, captación de catálogo Alpaca, último precio IEX, históricos diarios y lectura de cuenta/posiciones PAPER. La interfaz distingue hora de operación, cotización, recepción y reloj de sesión, con estado antiguo y desconocido al vencer su vigencia. Muestra gráfico, tabla OHLCV, ajustes y cobertura por sesiones. Opera por solicitudes explícitas; refrescar la pantalla no descarga nuevas cotizaciones.

La cuenta PAPER se lee en un dominio separado de MASTER. Si la lectura de posiciones falla, no se representa como una cartera vacía confirmada. No se exponen identificadores privados de cuenta. Los 100 emisores SEC continúan disponibles.

## Captación y procedencia

- Transporte exclusivamente GET a hosts/rutas fijos de PAPER y Market Data. Sin órdenes, LIVE, redirecciones, URL arbitraria o fallback de pago. Claves solo backend; mensajes de error saneados. IEX y USD pedidos explícitamente; no se confunde el mercado de cotización con el feed.
- Endpoints separados: assets, clock, calendar, snapshot, bars, corporate-actions, account y positions. Claves presentes no acreditan derechos. Una respuesta sintética se marca TEST_ONLY en preparación; no certifica conexión externa.
- Trabajos persistentes con idempotencia, una captación activa, reintentos acotados, cancelación, reanudación de fallos/pausas y concesiones con token. Recuperación tras interrupción; un trabajador vencido/cancelado no publica resultados.
- Cuota ALPACA compartida con el conector anterior: techo local 180/min y separación mínima de un segundo; Retry-After conservado. El intervalo de un segundo limita adicionalmente el caudal efectivo. Sin esperas dentro del bloqueo SQLite.
- Ventanas hasta 3.660 días, desde 2016 y terminadas antes de hoy en Nueva York. Barras diarias, hasta 1.000 por página y 12 páginas por etapa. Se siguen tokens aunque la página sea corta; ciclos, contradicciones, OHLC imposible, decimales no finitos y fechas futuras se rechazan.
- Series raw, split y all separadas, con petición, identidad observada, hashes, recibos y normalizador. `asof=-` desactiva el mapeo automático de símbolos: **no es un certificado de información histórica disponible**. Solo una paginación terminada se publica como serie; las páginas parciales se preservan para recuperación.
- Calendario con America/New_York, cambios de hora y cierres anticipados. Dependencia nueva `tzdata==2026.2` fijada en pyproject/uv.lock para Windows. Se cuentan sesiones esperadas, ausentes e inesperadas; no se rellenan huecos.
- Acciones corporativas consultadas por process_date. Acceso, exhaustividad y fecha efectiva no se infieren de una respuesta vacía; un fallo de esta etapa no certifica el histórico aunque existan barras.
- Originales públicos comprimidos/deduplicados por hash en `data/market/raw`. Cuenta/posiciones conservan solo campos normalizados permitidos y huella, sin archivar el cuerpo privado completo. Presupuesto inicial: 512 MiB de originales comprimidos, con reserva conservadora por tamaño de respuesta, y 500.000 filas de barras. Se detiene la captación al alcanzar límites; no hay borrado automático ni política completa de retención.

## Identidad: límite deliberado

El UUID de Alpaca identifica su activo; Assets no entrega CIK ni divisa nativa ni una clasificación exhaustiva de clases accionarias. Se conserva el registro del proveedor. La coincidencia SEC por símbolo/mercado solo genera un candidato que se abre por separado; no fusiona emisores ni asigna precios al registro SEC.

USD identifica la denominación solicitada de los precios, no se deduce de las cuentas empresariales. No se promueven registros ambiguos al maestro de instrumentos ejecutables. Al cambiar la identidad/símbolo, los precios e históricos de la identidad anterior no se muestran bajo la nueva. Vínculo emisor/instrumento, clase precisa, universo histórico y continuidad ante cambios de símbolo quedan pendientes de evidencia suficiente.

## Corrección encontrada

El control anterior de cuota SEC estaba situado en `quality()` y podía devolver un tipo incorrecto al consultar el estado; la ruta efectiva de descarga no reservaba esa cuota compartida. Ahora el estado es de solo lectura y SEC/Alpaca reservan presupuesto transaccionalmente antes del HTTP. Los reintentos y la caché no acortan bloqueos ajenos ni consumen doble cuota. Diez regresiones específicas cubren esta corrección.

## Validación realizada

- Suite completa backend: **412 pruebas correctas**. Después del ajuste final del mensaje de límite de almacenamiento: **13 pruebas afectadas correctas**, incluida una nueva regresión. No se presenta como suite completa de 413 ejecutada.
- Suite frontend: **86 correctas y una omisión preexistente**. Tras el cierre de fechas/accesibilidad/timestamps: **10 afectadas correctas** y TypeScript/build correctos. Continúan los avisos preexistentes de httpx/TestClient y del bloque 3D mayor de 500 kB.
- Navegador contra frontend y API locales, con base sintética separada: candidato SEC sin heredar precio; apertura explícita de Alpaca; antigüedad; tabla OHLCV; separación de ajustes; encolar/cancelar; endpoint de prueba explícito; desconexión y reintento. 1920/1366/800/390 px sin desbordamientos ni errores JavaScript. La evidencia sintética no acredita precios ni permisos reales.
- Migración 0010 aditiva, cuatro tablas, respaldo `output/b23-before-0010.db`. **31 tablas preexistentes idénticas antes/después**, comprobadas mediante conteos y hashes. No se migraron datos sintéticos a la base personal.
- Comprobación en aplicación habitual: esquema 0010, cuentas SEC de 100 emisores visibles, cero activos/barras Alpaca, `NO_CREDENTIALS`, botones de captación deshabilitados, `orders_enabled=false` y `POST /api/orders=403`. El arranque posterior mantiene los procesos previamente configurados.

Evidencia: [migración](evidencias/b23-migration.json), [navegador sintético](evidencias/b23-ui-verification.json), [aplicación habitual](evidencias/b23-personal-check.json). Capturas privadas en `output/playwright/b23`. Copia pequeña de pruebas y scripts en el directorio de trabajo del chat, separados de la base habitual.

## Qué falta y continuidad

Configurar ALPACA_API_KEY y ALPACA_SECRET_KEY de PAPER en `.env` local y reiniciar. No enviar claves al chat. Después comprobar conexión, catálogo, un precio y un histórico con evidencia real; revisar derechos por endpoint sin comprar planes. El acceso a corporate actions se valida por separado.

No hay streaming ni watchlist automática implementados. Se mantienen pendientes una conexión backend con watchlist limitada y su prueba de recuperación, así como la vinculación de identidades con evidencia adicional. No se promete tiempo real consolidado ni seguimiento autónomo con este tramo de solicitudes explícitas. La programación n8n continúa en B2.5/B5.

El siguiente desarrollo independiente es **B2.4: modelos empresariales deterministas y adaptación Model Builder / Earnings Reviewer / Valuation Reviewer**, usando las cuentas SEC verificadas. No necesita fingir conexión Alpaca ni cerrar su aceptación pendiente. Antes de escalar a miles de históricos: política de retención, presupuesto de disco, benchmark y cobertura suficiente por familia.

## Fuentes oficiales consultadas

- [Planes de datos Alpaca](https://docs.alpaca.markets/us/docs/about-market-data-api): Basic, IEX, límites y cobertura documentada.
- [FAQ de Market Data](https://docs.alpaca.markets/us/docs/market-data-faq) y [Paper Trading](https://docs.alpaca.markets/us/docs/paper-trading): distinguir plan/derechos efectivos. SIP histórico diferido es una posibilidad por comprobar, no fallback habilitado.
- [Assets](https://docs.alpaca.markets/us/reference/get-v2-assets-1) y [modelo Asset](https://alpaca.markets/sdks/python/api_reference/trading/models.html#asset): campos de identidad disponibles.
- [Barras históricas](https://docs.alpaca.markets/us/reference/stockbars): paginación, ajustes, feed, divisa y asof.
- [Calendario](https://docs.alpaca.markets/us/v1.1/reference/getcalendar-1), [reloj](https://docs.alpaca.markets/us/reference/legacyclock), [cuenta](https://docs.alpaca.markets/us/reference/getaccount-1).
- [Corporate actions](https://docs.alpaca.markets/us/reference/corporateactions-1): process_date y ausencia de garantía de publicación inmediata.
- [Streaming](https://docs.alpaca.markets/us/docs/streaming-market-data): referencia para el tramo aún pendiente.
