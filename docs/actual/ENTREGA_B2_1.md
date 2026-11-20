# B2.1 — registro empresarial y centro de activos

28-10-2026 · Europe/Madrid. Primer tramo de B2; B2 completo sigue en curso.

## Entrega

Descarga real del directorio de SEC: **8.023 emisores y 10.430 símbolos/listados** en la comprobación inicial, sin conflictos de alias detectados. Un emisor puede tener varios símbolos. Estos números cuentan identidad de catálogo; no cuentan empresas analizadas, instrumentos ejecutables ni históricos disponibles.

La oficina incorpora el acceso **Centro de activos** (`?activos=1`). Permite buscar por empresa, símbolo o CIK, navegar páginas de 50 resultados, filtrar identidades incompletas/conflictivas y abrir una ficha enlazable. Cada ficha muestra fuente, primera/última observación local, historial y datos pendientes para investigación, backtest y simulación.

Se conserva la oficina y el registro operativo anterior. El nuevo catálogo no transforma automáticamente un ticker SEC en un Instrument, no inventa divisa ni clasifica todos los registros como acciones ordinarias. El enlace entre emisor, clase de valor y listing requiere más evidencia y continúa en B2.2.

## Identidad y captación

- Entidades por CIK e identidades de listado por proveedor. Clases de un mismo emisor permanecen separadas.
- Versiones con intervalos de conocimiento local. La ficha temporal excluye cambios futuros, incluida la fecha futura de cierre de una versión. No se declara un universo histórico point-in-time de mercado.
- Colisiones del mismo símbolo/mercado dentro de un proveedor se muestran como conflicto. Un símbolo ausente en una descarga completa pasa a «ausente en último catálogo»; no se infiere una baja bursátil.
- La respuesta completa se valida antes de actualizar el registro. Respuestas inválidas, errores y cuotas conservan el catálogo anterior. Se guarda hash, fuente, fecha y resultado de cada importación.
- Importación idempotente y exclusión mutua por proveedor; recuperación de solicitudes interrumpidas tras una concesión de tres minutos. La aplicación mantiene un único estado persistente por petición.
- Una consulta SEC acotada a una URL HTTPS fija, sin redirecciones ni URL aportada por el usuario. Máximo 16 MiB, tiempo limitado y cuota SEC compartida de dos consultas/minuto con el conector previo; se respeta `Retry-After`.
- Búsqueda y paginación en SQLite. Corregido además un límite previo: crear un caso de investigación ahora busca el instrumento por ID, sin depender de los primeros 1.000 registros.

El contacto SEC facilitado por el usuario está configurado en `.env`, ignorado por Git; la interfaz solo muestra su estado. Alpaca sigue sin credenciales. Su integración por universo permanece pendiente; el catálogo no anuncia conexiones ni precios de Alpaca inexistentes.

## Verificación

- 339 pruebas backend pasan en la suite completa. Los casos nuevos cubren identidad, conflictos, revisiones, renombrado, consulta temporal, idempotencia, cuota compartida, recuperación, rechazo de respuestas parciales, destinos HTTP y búsqueda superior a 1.000 registros.
- 71 pruebas frontend pasan; una omisión preexistente. TypeScript y compilación correctos; se conserva el aviso del bloque 3D de más de 500 kB.
- Navegador con el catálogo real sobre copia: búsqueda AAPL → ficha Apple → procedencia; paginación; filtros; búsqueda vacía; desconexión. Cuatro tamaños (1920, 1366, 800 y 390 px), sin desbordamiento horizontal ni errores JavaScript en la pasada final.
- Migración 0008 aditiva: cuatro tablas nuevas. La prueba sobre copia conserva idénticas las filas de las 21 tablas anteriores. La definición de la migración queda congelada, independiente de cambios futuros en modelos de aplicación.
- Aplicada también a la base habitual, con respaldo `output/b2-before-0008.db`. La nueva descarga SEC devuelve el mismo hash y recuentos que la copia; las 20 tablas protegidas (excluida la cuota SEC) permanecen idénticas después de la captación. Se repiten 21 pruebas de catálogo/base tras congelar la migración; todas pasan.

Evidencia de ingeniería: [catálogo en copia](evidencias/b2-catalogue-probe.json), [catálogo en base habitual](evidencias/b2-catalogue-personal.json), [navegador](evidencias/b2-ui-verification.json), [migración](evidencias/b2-migration-applied.json). Logs del chat en `work/b2-*.log`; capturas privadas en `output/playwright/b2/`.

## Límites y siguiente tramo

La captación actual es un directorio completo en una petición, no un bootstrap multiemisor reanudable de cuentas y documentos. El guardado se confirma en una transacción; la siguiente fase debe medir y acotar la carga de los lotes financieros. La ficha muestra hasta las 100 versiones más recientes.

**B2.2:** seleccionar 100 emisores piloto, incorporar submissions/companyfacts por CIK y normalizar conceptos, periodos, unidades y revisiones. Después completar la vinculación de instrumentos y datos Alpaca, el piloto de tres modelos empresariales y la preparación del ciclo n8n. Los modelos de valoración, minería, selección y ejecución PAPER aún no están implementados por este tramo.

## Fuentes comprobadas

- [SEC: acceso a EDGAR](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data): directorio `company_tickers_exchange.json`, identificación del cliente y fair access. SEC indica que las asociaciones de nombres/símbolos/mercados no garantizan exactitud ni cobertura; por eso no se usan como única prueba de elegibilidad.
- [SEC: APIs de empresa](https://www.sec.gov/search-filings/edgar-application-programming-interfaces): submissions, companyfacts y archivos masivos; referencia del siguiente tramo.
- [Alpaca: catálogo de activos](https://docs.alpaca.markets/us/reference/get-v2-assets-1): identidad de activo, mercado y estado. `tradable` no sustituye los controles locales ni habilita órdenes.
