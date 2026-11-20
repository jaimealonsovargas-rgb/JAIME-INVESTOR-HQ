# B2.4 — primer tramo del análisis empresarial

30-10-2026 · Europe/Madrid. **Núcleo contable anual implementado y probado con SEC real. B2.4 continúa abierto para ampliar estados y conciliaciones.** No hay DCF, consenso, inferencia local ni recomendaciones simuladas.

## Resultado utilizable

Centro de activos → empresa SEC → **Análisis de empresa**. Construir con cuentas guardadas ejecuta Python sobre una versión de datos fijada. No descarga documentos ni consulta un LLM. Modelo, Resultados y Valoración muestran cifras, fórmulas, inputs exactos y controles. Cada fuente conserva CIK, concepto, unidad, inicio/final, accession, fecha de presentación, snapshot, recibo y hash. El panel del especialista enlaza las entregas empresariales reales, separadas de los debates P4.

Se reutilizan `fundamental_equity`, `value_quality`, `valuation` y `data_quality`. Son mandatos lógicos de un flujo determinista, no cuatro modelos de IA trabajando. La narrativa figura NOT_REQUESTED y no representa actividad inventada.

## Reglas financieras

- Una tabla anual pertenece a un solo informe/periodo/divisa. Las alternativas, conflictos y ausencias del normalizador SEC se conservan.
- Márgenes operativo, resultado de la matriz/ingresos, caja operativa/ingresos, liquidez corriente y pasivos/activos: denominador positivo y magnitudes compatibles. Sin dividir por cero ni reemplazar ausencias por cero.
- Caja operativa menos pagos de inmovilizado US-GAAP es una medida parcial. No se etiqueta como flujo libre de un DCF; los signos IFRS no se infieren.
- Resultados compara los ejercicios consecutivos publicados en el mismo informe, con concepto y unidad iguales. Admite diferencia máxima de siete días entre ventanas 52/53 semanas, sin ajuste por semana adicional. Bases anteriores nulas/negativas conservan la diferencia absoluta y bloquean el porcentaje.
- Las comparativas pueden estar revisadas. Conocimiento local desde recepción y cota conservadora de publicación, nunca PIT histórico de mercado. `as_of` exige zona, rechaza futuro y excluye datos/recibos posteriores.
- Constructor con Decimal (48 dígitos) y revisor separado con fracciones racionales. El revisor no reescribe el modelo. Balance exige patrimonio total con minoritarios: no sustituye patrimonio de la matriz ni inventa tolerancias.
- Cada nueva evidencia genera versión inmutable; una petición repetida o nueva petición con idéntico resultado reutiliza la misma. Cambios del mismo periodo conservan antes/después sin atribuir automáticamente la causa. Reinicio no pierde versiones.
- DCF/comparables/precio objetivo bloqueados por inputs insuficientes. Consenso, guidance y transcript ausentes; sin sorpresas de resultados inventadas. `backtest_ready=false`, `execution_ready=false`.

## Persistencia y protección

Migración aditiva **0011_company_models**: `company_models` y `company_model_requests`. Copia SQLite consistente `output/b24-before-0011.db`. **35 tablas anteriores idénticas antes/después de migración y construcción**, cotejadas por conteos y hashes. No se modificó MASTER ni se copiaron fixtures a la base personal.

Un build es una transacción corta: fuente fijada, cálculo, revisión y asignación de versión. Sin red, espera ni inferencia dentro del bloqueo. Rollback ante error; idempotencia, hash de inputs y huella del artefacto completo. Límite inicial de 150.000 facts de entrada y 10.000 modelos; no hay borrado automático. La retención y presupuesto agregado de disco siguen pendientes antes de escalar.

Rutas localhost bajo `/api/universe`: versiones/crear modelo por CIK, detalle por ID y cinco entregas recientes. Escritura con cabecera local, origen permitido y clave de idempotencia; sin URL, código, prompt, credenciales ni órdenes en el cuerpo. Desactivar SEC bloquea también lectura de sus modelos. Datos externos se tratan como contenido, nunca como instrucciones.

## Evidencia realizada

Piloto real:

| Empresa | Ejercicio | Inputs contrastados con original | Cálculos disponibles |
|---|---|---|---|
| Apple | 29-09-2024 a 27-09-2025 | 40 | 6/6 |
| Microsoft | 01-07-2025 a 30-06-2026 | 40 | 6/6 |
| Walmart | 01-02-2025 a 31-01-2026 | 40 | 5/6 |

Las cinco variaciones de cada empresa tienen base comparable. Los 120 inputs se contrastaron contra los JSON SEC comprimidos y su hash, no solo contra la tabla normalizada. Los tres modelos quedan con revisión PARTIAL: faltan conciliaciones de balance/caja. En Walmart no se calcula pasivos/activos por ausencia del pasivo total en el mapeo disponible. No se presenta como fallo aritmético ni aceptación financiera completa.

- **426 pruebas backend** pasan; incluyen 13 pruebas nuevas de modelos (variaciones con base nula/negativa, conceptos/periodos incompatibles, revisión independiente, idempotencia, persistencia, revisión de cifras, temporalidad, fuente desactivada, origen y órdenes).
- **86 pruebas frontend y una omisión preexistente** en la suite; después **4 nuevas pruebas específicas**, todas correctas. TypeScript/build correctos tras los cambios finales. No se presenta como una nueva suite completa de 90 ejecutada.
- Navegador real con la API y los modelos personales: cuatro tamaños (1920/1366/800/390), fórmula/recibo, tres vistas, build idempotente, ficha especialista, desconexión/reintento y órdenes 403. Sin errores JavaScript ni desbordamiento horizontal. Dos rondas visuales; revisión externa de la skill confirma resueltas las tres correcciones de claridad. Su disposición `ship` se limita a esas tres correcciones.
- Sin nuevos servicios, dependencias o modelos. Persisten los avisos de httpx/TestClient y del chunk 3D superior a 500 kB.

[Migración y cotejo real](evidencias/b24-migration-pilot.json) · [Navegador](evidencias/b24-ui.json). Capturas privadas en `output/playwright/b24`. Revisiones simuladas solo en tests; no se ha fabricado una corrección de filing en la base personal.

## Segundo tramo — 04-11-2026

Parser `sec-financials-v2` y plantilla `company-accounting-v2`: flujos de inversión/financiación, FX de efectivo restringido, variación declarada y total declarado del balance. Los modelos antiguos se conservan; si el snapshot usa el parser anterior, el constructor relee su original gzip local, comprueba SHA-256 y límite de tamaño y normaliza con el nuevo mapeo. No descarga ni reescribe snapshots. Las nuevas versiones se distinguen como `MAPPING_UPDATED`, no como un filing nuevo.

La conciliación exige mismo informe, identidad, divisa y periodo; saldo inicial del día anterior al inicio y mismo concepto de efectivo que el cierre. No mezcla caja del balance con efectivo restringido ni convierte FX ausente en cero. Contrasta cierre−apertura con CFO+CFI+CFF+FX y con la variación publicada. Revisor con fracciones exactas, sin tolerancia inventada; la interfaz muestra residuos sin escalarlos a millones. El contraste de activos con el total declarado se muestra separado de la conciliación de sus componentes.

Versiones 2 guardadas desde originales reales ya disponibles:

| Empresa | Inputs | Total declarado del balance | Caja | Componentes del balance |
|---|---:|---|---|---|
| Apple | 48 | PASS, diferencia 0 USD | BLOCKED: FX compatible ausente | BLOCKED: patrimonio total ausente |
| Microsoft | 48 | PASS, diferencia 0 USD | BLOCKED: FX disponible tiene alcance ampliado a disposal groups/discontinued operations | BLOCKED: patrimonio total ausente |
| Walmart | 50 | PASS, diferencia 0 USD | PASS, ambos residuos 0 USD | BLOCKED: pasivo total ausente |

Los tres mantienen revisión PARTIAL. La coincidencia de un total no sustituye componentes ni certifica el estado financiero completo. Sin nueva presentación descargada, inferencia, valoración objetivo ni órdenes.

Backup SQLite consistente `output/b24-before-reconciliation-v2.db`. Los tres modelos anteriores conservan su payload y las cuatro tablas de cartera/ledger/valoraciones conservan conteos y hashes durante los builds. Repetir cada solicitud devuelve el mismo modelo. Evidencia privada: `output/b24-reconciliation-persisted.json` (versiones, fuentes, controles y huellas). No se ejecutó una campaña sobre los 100 emisores.

Verificación: suite completa backend **435 pruebas correctas**; tras mejorar precisión del balance, **40 pruebas afectadas correctas**, incluidas dos nuevas regresiones. Frontend: **5 pruebas afectadas correctas** y TypeScript/build correctos, incluida visibilidad de residuo cero y de 0,01 USD. Backend local reiniciado con código actual: POST por el proxy 5173 reutiliza Walmart v2, devuelve parser/plantilla v2 y ambos residuos cero; órdenes continúan HTTP 403. Se mantienen los avisos preexistentes de httpx/TestClient y chunk 3D. No se equiparan estos tests a aceptación financiera.

Referencia de alcance: [guía XBRL US de flujos de caja](https://xbrl.us/data-rule/guid-cashflows/), contrastada durante esta entrega; apertura/cierre y variación deben compartir definición de efectivo.

## Cierre del lote de tres emisores — 06-11-2026

Se completó el contraste de balance y caja de Apple, Microsoft y Walmart con las relaciones de cálculo y cifras XBRL de sus propios informes anuales. La plantilla `company-accounting-v3.1` conserva la revisión independiente con fracciones exactas. Cada ecuación contrasta sus partidas, el total publicado y los comparadores de Companyfacts; para caja comprueba también apertura y cierre del mismo concepto, periodo y divisa.

| Empresa | Versión actual / ejercicio | Balance | Caja | Revisión numérica |
|---|---|---|---|---|
| Apple | v5 / 26-09-2026 | PASS, residuos 0 USD | PASS, residuos 0 USD | PASSED |
| Microsoft | v4 / 30-06-2026 | PASS, residuos 0 USD | PASS, residuos 0 USD | PASSED |
| Walmart | v4 / 31-01-2026 | PASS, residuos 0 USD | PASS, residuos 0 USD | PARTIAL: ratio pasivos/activos pendiente |

Las ausencias anteriores tenían causas distintas. Apple publica una ecuación de caja de tres flujos y su balance usa el patrimonio de la matriz. Microsoft incluye expresamente la etiqueta de FX de alcance ampliado en su ecuación. Walmart desglosa pasivos corrientes y no corrientes y participaciones minoritarias reembolsables. Estas composiciones se aceptan por la relación presentada por cada emisor; no se generalizan a otras compañías. La línea de compromisos y contingencias figura explícitamente `nil` en los tres originales: se conserva como partida sin cuantificar. El ratio de Walmart sigue requiriendo un subtotal de pasivos etiquetado y no se rellena con una suma supuesta.

Fuentes: [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm), [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm), [Walmart 10-K](https://www.sec.gov/Archives/edgar/data/104169/000010416926000055/wmt-20260131.htm). Los recibos privados fijan URL, SHA-256 y primera recepción. Microsoft incluye el cálculo en su esquema; el acceso al esquema solo se intenta tras un 404 del archivo de cálculo. Los seis originales comprimidos ocupan 835.229 bytes, más tres pequeños manifiestos. Se consultan localmente después de la primera adquisición.

El script reutilizable admite un lote explícito de entre uno y 25 CIKs con cuentas ya guardadas:

```powershell
.\.venv\Scripts\python.exe scripts/review_company_batch.py 0000320193 0000789019 0000104169
```

Usa derechos y cuota SEC comunes, transporte limitado al archivo oficial, límites de descarga y hashes. No resuelve enlaces XML. Relaciones ambiguas, contextos segmentados, unidades incompatibles, partidas ausentes y formatos no soportados quedan bloqueados. Los nombres de documento admitidos son los del contrato actual; este piloto no certifica compatibilidad con todos los emisores SEC. La adquisición precede al build: no hay red bajo el bloqueo de SQLite ni en el botón de construcción de la web.

La interfaz incorpora el desplegable **Partidas y documentos del informe anual**, con conceptos en español, importes, partidas sin cuantificar y enlaces oficiales. Las discrepancias muestran sus residuos. Construir de nuevo reutiliza el modelo correspondiente.

### Integridad y repetición

Se conservaron por hash los siete modelos originales y se añadieron seis versiones técnicas durante el cierre: primero Apple v4/Microsoft v3/Walmart v3 con la plantilla v3; después v5/v4/v4 con v3.1. La revisión final corrigió una dependencia de la última consulta del catálogo: su primera recepción determina ahora la identidad histórica. Las versiones intermedias también se preservan. El total es 13 modelos. Reintentar una solicitud de una plantilla anterior devuelve su modelo original.

El evento real de Apple sigue asociado a **v3 / NEW_PERIOD / SUCCEEDED**. Las versiones posteriores son actualizaciones técnicas, no nuevos filings. Repetir el lote y construir las tres empresas desde la web conserva IDs y conteos. Ledger, cartera y evento SEC conservan sus huellas. El arranque habitual del backend añadió una valoración rutinaria de cartera; las 14 anteriores permanecen idénticas y durante el lote final tampoco cambió la tabla de valoraciones. No se confunde esa escritura de arranque con una operación de inversión.

Evidencia privada: `output/b24-statement-batch-20261105.json` (fecha del nombre heredada; comprobación final del 06-11), `output/b24-batch-browser.json` y `output/b24-final-check.log`. Navegador real: tres empresas, construcción idempotente, enlaces SEC, partida específica por empresa, pantallas de 1366 y 390 px sin desbordamiento ni errores JavaScript, órdenes HTTP 403.

Verificación final: `scripts/manage.py check` completo, **468 pruebas backend y 95 frontend superadas**, una omisión frontend preexistente, TypeScript/build correctos. Incluye regresiones de XML inseguro, ecuaciones ambiguas, contexto/divisa incompatibles, hash alterado, conocimiento temporal, nuevo informe anual pendiente y compatibilidad de solicitudes antiguas. El fallo de identidad histórica apareció en la primera ronda completa, se corrigió y la suite final lo verifica. Persisten los avisos preexistentes de httpx/TestClient y tamaño del chunk 3D.

### Adaptación de Day Trader

Se incorpora el contraste del modelo con el último informe anual conocido en el catálogo SEC local. Una publicación posterior o enmienda pendiente bloquea la cobertura aunque la aritmética cuadre. La fecha de conocimiento limita el resultado; no se afirma que un catálogo antiguo conozca todas las publicaciones actuales. Esta adaptación procede del criterio de cobertura del analista de Day Trader. [Auditoría, pin y adaptación por fases](DAY_TRADER_ADAPTACION.md).

`PASSED` describe estos controles numéricos. DCF, comparables, interpretación local y aceptación financiera completa conservan los requisitos pendientes. P4 sigue PARTIAL; este cierre no implementa P5/P6.

## Continuación exacta

1. **Lote de tres emisores conciliado y repetible.** Mantener el ratio pendiente de Walmart y las limitaciones de cobertura documentadas; no repetir el piloto ni ampliar empresas como siguiente tarea.
2. Actualización por filing real completada el 04-11: Apple v3/NEW_PERIOD y evento idempotente, [entrega posterior](ENTREGA_B2_4_ACTUALIZACION_Y_P4.md). La corrección de cifras del mismo periodo sigue probada con fixture aislado; no se confunde con el nuevo ejercicio real. Interpretación local pendiente de inputs/outputs y disponibilidad real, sin gasto.
3. Siguiente entrega B2.5: CycleRequest/n8n en sombra y propiedad única de agenda. Reutilizar la captura y los eventos SEC existentes, con autenticación, idempotencia y recuperación, sin duplicar programación interna.

Separadamente, B2.3 ha superado la prueba de conexión real de lectura, pero conserva pendientes streaming/watchlist e identidad emisor/clase/divisa. El bloque B2 completo sigue abierto. Minería y ejecución PAPER aún no están implementadas.

Referencia técnica contrastada el 30-10: [API SEC](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), para límites de conceptos estándar, unidades y periodos fiscales. Se reutiliza el diseño local [agentes financieros](AGENTES_FINANCIEROS_ANTHROPIC.md); no se instalaron agentes Anthropic.
