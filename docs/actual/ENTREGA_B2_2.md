# B2.2 — cuentas e informes empresariales SEC

28-10-2026 · Europe/Madrid. B2.2 completado; B2 completo sigue abierto.

## Resultado disponible

El Centro de activos incorpora cuentas anuales, documentos y cifras comparativas por emisor. El piloto contiene **100 emisores**, seleccionados de forma reproducible del catálogo observado. Es una muestra técnica por conveniencia, no un índice ni una selección de inversiones.

Se completaron **200 descargas válidas**: submissions y companyfacts por emisor. La comprobación a las 16:55 de Madrid encontró **353.528 cifras consultables y 12.961 registros de documentos**. Se almacenan 353.697 cifras y 12.965 registros: los restantes no superaban todavía la cota conservadora de publicación aplicada a esa consulta. Los documentos son metadatos y enlaces al original SEC; no se ha descargado ni analizado su HTML completo.

**71 de 100 emisores** reúnen seis magnitudes básicas en un mismo informe anual: ingresos, resultado atribuible a la matriz, activos, patrimonio de la matriz, efectivo y flujo de caja operativo. Los otros **29 muestran cobertura parcial**. Esta medida no certifica una inversión ni garantiza comparabilidad sectorial. El mapa contiene 24 magnitudes, algunas con alcances contables distintos y no aplicables a todas las empresas.

## Captación e integridad

- Cola SQLite con manifiesto y versión del normalizador, idempotencia, tareas por endpoint, progreso, pausa, reanudación y cancelación. Una cola activa; trabajador único por proceso y concesiones con token para impedir escrituras de un trabajador vencido. Recupera pendientes al reiniciar, sin crear una programación periódica nueva.
- Endpoints HTTPS fijos por CIK, solo GET, sin redirecciones ni rutas libres. Contacto privado, máximo 32 MiB y tiempo acotado. Configuración/derechos actuales gobiernan la captación. Un 401/403 pausa el lote; errores recuperables tienen tres intentos y 429 respeta Retry-After.
- Cuota unificada entre directorio, A09 y nuevo trabajador: hasta 60/minuto, separadas por al menos un segundo. Sustituye las antiguas dos/minuto. SQLite serializa la reserva; no mantiene bloqueos durante espera/descarga.
- JSON original comprimido en `data/sec/raw`, identificado por SHA-256. Snapshots inmutables, recibos y confirmación transaccional por endpoint. Una redescarga idéntica no duplica filas normalizadas.
- CIK, concepto/taxonomía, unidad, inicio/fin, accession, formulario, fecha y etiquetas fiscales se conservan. Decimales como texto; sin conversión FX ni suma de alternativas.
- Vista anual por un único documento, periodo y divisa. Ausencias no se sustituyen por cero ni por otra presentación. Divisas ambiguas y valores contradictorios impiden seleccionar una cifra. Se distinguen trimestre, duración acumulada e instante. El año fiscal de la presentación no se usa como año del dato comparativo.
- `as_of` requiere zona horaria, descarga conocida y publicación anterior al instante. Una fecha SEC sin hora usa las 05:00 UTC del día siguiente como cota conservadora. Se mantienen snapshots anteriores; no se certifica disponibilidad histórica de mercado.

El piloto real detectó submissions bancarias de hasta 26.503 registros y seis cifras antiguas de Goldman Sachs sin el inicio requerido por su concepto. Se amplió el límite de filas conservando el de bytes y la validación de arrays. Las seis cifras se guardan con anomalía de periodo y se excluyen del cuadro anual; no se inventa su fecha.

## Pantalla

Elegir una empresa en Centro de activos y abrir **Cuentas, documentos y revisiones**. Incluye periodo fiscal real, importes/unidades, cobertura y evidencia exacta desplegable; documentos paginados y cifras de distintas presentaciones. Permite actualizar una empresa o el piloto, y pausar/reanudar la captación.

La divisa contable pertenece al emisor; no confirma la del valor cotizado. El catálogo sigue separado de Instrument, precios y cartera. BACKTEST y PAPER permanecen bloqueados.

## Verificación

- **353 pruebas backend** correctas en la suite completa. Tras cerrar rechazo SEC y cobertura IFRS pasan **37 pruebas afectadas**, incluidas dos regresiones nuevas; no se suman como una segunda suite completa.
- **76 pruebas frontend** correctas y una omisión preexistente. TypeScript/build correctos. Continúa el aviso preexistente del bloque 3D de más de 500 kB. Sin dependencias nuevas.
- Navegador con datos reales en copia: Microsoft, Walmart/ejercicio distinto, evidencia exacta, documentos/paginación, historia, empresa no importada y desconexión. 1920, 1366, 800 y 390 px, sin desbordamiento ni errores JavaScript. Detector de diseño sin hallazgos en los cuatro archivos revisados.
- **60 cifras** de Apple, Microsoft y Walmart cotejadas con JSON original: concepto, unidad, valor, periodo y documento coinciden. Ejercicios terminados el 27-09-2025, 30-06-2026 y 31-01-2026. Cambio real de ingresos comparativos Apple comprobado entre presentaciones; no se infiere su causa.
- Los 100 emisores quedan sin cuentas/documentos antes de su primera descarga. Tests de revisión futura invisible, recuperación con token vencido, cuota, cancelación, respuestas inválidas e inmutabilidad.
- Consulta por emisor: media 0,224 s, máximo 1,188 s en el recorrido sobre copia; medición local, no garantía a mayor escala.
- Migración 0009 aditiva, seis tablas. Backup `output/b22-before-0009.db`. Se transfieren los datos SEC verificados conservando recibos originales y comprobando 200 hashes, sin repetir otras 200 descargas. **Las 25 tablas anteriores quedan idénticas durante migración/transferencia**, incluida la cartera. El arranque posterior mantiene los procesos configurados previamente.
- HTTP habitual: esquema 0009, 100 emisores con cifras/documentos, lote completado, trabajador disponible, `orders_enabled=false` y `POST /api/orders=403`.

Evidencias: [piloto/manifiesto](evidencias/b22-pilot-report.json), [cotejo y cobertura por emisor](evidencias/b22-financial-audit.json), [migración/transferencia](evidencias/b22-migration-and-import.json), [navegador](evidencias/b22-ui-verification.json), [HTTP habitual](evidencias/b22-personal-http.json), [confirmación de navegador sobre base habitual](evidencias/b22-personal-ui-verification.json). Capturas privadas: `output/playwright/b22`; logs del chat: `work/b22-*.log`.

## Límites y continuidad

Este tramo no implementa modelos, forecasts, DCF, consenso, transcripts, minería ni trading. No vincula instrumentos por ticker o divisa contable. Conceptos personalizados, segmentos y archivos submissions históricos adicionales quedan fuera del bootstrap; se indica en pantalla. La pestaña de cifras usa el snapshot consultado; los previos siguen disponibles mediante consulta temporal API. IFRS tiene prueba sintética de contrato, no aceptación de un piloto IFRS real.

Cuentas de más de 550 días desde el cierre se señalan como antiguas. La cola consume peticiones explícitas y recupera pendientes; la programación automática sigue en el futuro contrato n8n. Roles/modelos conservan su estado anterior.

**Siguiente B2.3:** identidad de instrumentos y datos Alpaca: preparación por endpoint, calendario, precios/barras, feed/ajustes/cobertura y cuenta PAPER de solo lectura, separada de MASTER. Claves Alpaca pendientes en `.env`; se puede avanzar implementación/pruebas aisladas, no certificar conexión real. Después B2.4 modelos empresariales y B2.5 contrato n8n en sombra. Órdenes siguen bloqueadas.

## Fuentes oficiales

[SEC: APIs EDGAR](https://www.sec.gov/search-filings/edgar-application-programming-interfaces): submissions, companyfacts, conceptos estándar de toda la entidad, archivos históricos y periodos. [SEC: acceso a EDGAR](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data): identificación, máximo de diez peticiones/segundo y enlaces a presentaciones. Reconsultadas el 28-10-2026; la política local es más conservadora.
