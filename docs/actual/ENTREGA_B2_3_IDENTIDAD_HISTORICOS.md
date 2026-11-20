# B2.3 — identidad del piloto y diagnóstico de históricos

08-11-2026, Europe/Madrid. Entregada la revisión inicial de identidad y admisibilidad usando la evidencia ya guardada. No se amplía el universo ni se certifica B2 completo. El vínculo actual empresa–acción queda documentado para Apple, Microsoft y Walmart; la divisa nativa, la continuidad histórica y la aceptación para backtest siguen pendientes.

## Identidad contrastada

Se conservan por separado emisor SEC, instrumento lógico del piloto y listing del proveedor. `pilot_identity.json` fija los tres registros de catálogo, sus huellas y los recibos de los informes originales. Cada consulta vuelve a comprobar esas referencias, el catálogo vigente, el hash del XML, el CIK del documento y los hechos `Security12bTitle`, `TradingSymbol` y `SecurityExchangeName` dentro del **mismo contexto XBRL**. Solo se admite una clase de acción ordinaria única en este piloto. Un cambio, ambigüedad o archivo alterado retira la confirmación; no se adivina otro vínculo por ticker.

El caso Microsoft demuestra por qué hace falta este control: su documento utiliza MSFT también en los contextos de varios bonos. El contexto y la clase separan esos valores de la acción ordinaria. No se ejecutan instrucciones ni se descargan enlaces contenidos en XML. Se rechazan DTD/entidades y se acota la descompresión.

| Emisor | CIK | Acción del catálogo Alpaca | Informe contrastado |
|---|---|---|---|
| Apple | 0000320193 | AAPL · NASDAQ · Common Stock | 0000320193-26-000026 |
| Microsoft | 0000789019 | MSFT · NASDAQ · Common stock | 0001193125-26-323660 |
| Walmart | 0000104169 | WMT · NASDAQ · Common Stock | 0000104169-26-000055 |

La revisión se conoce localmente desde el **07-11 a las 10:43 Madrid**. Los originales se recibieron antes, el 05-11 en hora de Madrid. Ninguna de esas fechas acredita que el vínculo estuviese disponible en cada sesión del histórico. No se asigna USD como divisa nativa a partir del valor nominal, de las cuentas contables o del parámetro de precios.

Las referencias verificadas permanecen en el repositorio; los originales y los informes de diagnóstico permanecen en `data/` y `output/`. No se modifica el maestro antiguo de instrumentos, los catálogos originales ni MASTER. El instrumento lógico del piloto no es un instrumento ejecutable ni un maestro universal ya resuelto.

## Resultado de admisibilidad

Política versionada `daily-trend-data-v1`, aplicada por instrumento, serie y fecha de conocimiento. El diagnóstico lee una transacción consistente, verifica los originales comprimidos y reproduce su normalización. Compara hashes, filas, parámetros, identidad fijada en la solicitud y cadenas de paginación de barras y acciones corporativas. Comprueba OHLC, unidades, unicidad por sesión, fechas de Nueva York, calendario, huecos y longitud. No rellena sesiones ni combina series raw/ajustadas o feeds.

| Acción | Histórico guardado revisado | Resultado |
|---|---|---|
| Apple | 21 barras diarias raw IEX; 01–30 septiembre 2026; 21 sesiones esperadas, sin ausencias ni sesiones inesperadas | EXPLORATORY_ONLY: exploración descriptiva, BACKTEST BLOCKED |
| Microsoft | Sin captación histórica de la serie seleccionada | INSUFFICIENT_DATA, BACKTEST BLOCKED |
| Walmart | Sin captación histórica de la serie seleccionada | INSUFFICIENT_DATA, BACKTEST BLOCKED |

La descarga de Apple se recibió el 30-10. Las 21 sesiones completas **solo acreditan cobertura del intervalo pedido**. El umbral preliminar de 252 sesiones es un mínimo de ingeniería para evaluar datos de tendencia diaria; no demuestra potencia estadística, robustez ni rentabilidad, y deberá concretarse con el protocolo de B3. Esta versión del diagnóstico nunca activa backtests ni órdenes aunque se supere ese número.

Bloqueos explícitos: divisa nativa sin evidencia independiente, identidad/aliases durante todo el histórico, conciliación de splits/dividendos y ajustes, disponibilidad de la información en cada fecha, selección histórica del universo/bajas y alcance de uso para minería. IEX se muestra como un solo mercado. Una consulta de corporate actions por fecha de proceso, incluso vacía o marcada completa, no acredita exhaustividad por fecha efectiva.

Estas distinciones coinciden con la documentación oficial consultada el 07-11: [barras, ajustes, asof y divisa solicitada](https://docs.alpaca.markets/us/reference/stockbars), [acciones corporativas y retrasos de disponibilidad](https://docs.alpaca.markets/us/reference/corporateactions-1), [alcance IEX/SIP](https://docs.alpaca.markets/us/docs/market-data-faq). La revisión no habilita otra fuente ni presume derechos de redistribución o planes de pago.

## Producto y reproducción

Centro de activos → empresa o acción → **Precios e históricos → Calidad para investigación**. Tres campos resumen el vínculo, las sesiones y el uso actual; las comprobaciones y evidencias quedan plegadas. Desde el emisor se abre explícitamente la acción vinculada, conservando las cuentas y los precios en sus dominios. Si la API falla, se oculta el diagnóstico anterior. No se añaden formularios de claves ni se cambia la sede 3D.

El campo `assessment` se incorpora a la consulta de mercado existente. Solo lectura; sin nueva ruta de escritura, dependencia ni migración. El esquema sigue en **0013_shadow_cycles**. La CLI fuerza `PRAGMA query_only=ON` y no realiza HTTP:

```powershell
.\.venv\Scripts\python.exe scripts/assess_pilot_data.py --as-of "2026-11-08T11:43:57.854551+00:00" --output output/b23-identity-history-20261108.json
```

Repetir la misma consulta conserva exactamente el JSON. Si un archivo de evidencia ya existe con otro resultado, se rechaza sobrescribirlo. El ID del manifiesto depende de entradas, evidencia, comprobaciones y política; la hora de refresco por sí sola no crea otro ID. Una fecha equivalente en otro huso horario produce el mismo resultado. Esto es un diagnóstico, no un DatasetManifest que autorice todavía a B3 a consumir precios.

## Verificación y preservación

- **509 pruebas backend y 102 frontend superadas**, una omisión frontend preexistente. TypeScript/build correctos tras precisar el tipo del validador de fechas. `output/b23-identity-full-check.log` conserva la primera compilación fallida; `output/b23-identity-build.log` acredita la compilación corregida. Avisos preexistentes de httpx/TestClient y chunk 3D.
- 24 pruebas nuevas backend: clases y contextos, CIK/namespace, XML inseguro, evidencias posteriores al corte, cambio de identidad, duplicados, huecos de fuente, modificaciones de originales/filas/parámetros, páginas ausentes y fuentes desactivadas. Cuatro pruebas nuevas de UI: estados, enlaces, evidencia futura/inválida y ausencia de promoción a READY.
- Dos ejecuciones reales del diagnóstico con idéntica fecha de corte producen el mismo resultado y conservan conteos/huellas de **13 tablas**: catálogos, jobs, recibos, barras, snapshots, modelos y ledger/cartera. Los **18 modelos** permanecen guardados. Ninguna descarga ni construcción contable forma parte de ese diagnóstico.
- Navegador con API real: salto SEC→acción, tres emisores, Apple 21/21, ausencia de histórico de las otras dos, detalles plegados, móvil 390 px sin desbordamiento y ocultación ante desconexión, sin errores JavaScript. Capturas en `output/playwright/b23-identity/`.

Evidencia privada: `output/b23-identity-history-20261108.json`, `output/b23-identity-preservation.json`, `output/b23-identity-browser.json` y `output/b23-identity-runtime.json`. PAPER ONLY, órdenes 403, coste obligatorio 0 EUR y P4 PARTIAL se mantienen.

## Continuación

El punto de salida de esta revisión está cumplido: vínculos actuales contrastados y diagnóstico reproducible que identifica por qué los datos todavía no son admisibles. **No equivale a cerrar todas las identidades históricas ni B2.3/B2.** El siguiente trabajo es presupuesto agregado de almacenamiento y política de conservación antes de ampliar históricos. El plan de captación deberá resolver divisa nativa, continuidad temporal y acciones corporativas; después ampliar por lotes y medir capacidad. No repetir bootstrap, piloto n8n ni esta revisión sin cambios de evidencia.
