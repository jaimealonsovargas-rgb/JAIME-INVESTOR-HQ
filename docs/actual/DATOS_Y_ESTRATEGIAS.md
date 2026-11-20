# Datos amplios y minería de estrategias

Fecha: 27-10-2026. **Especificación para construir; capacidades futuras salvo donde se indica lo contrario.** La implementación actual tiene adaptadores acotados y un ciclo descriptivo A21; no es un universo profesional ni un laboratorio de backtesting.

Actualización 11-11-2026: [B3.1 entregado](ENTREGA_B3_1.md), núcleo determinista y registro de ensayos exclusivamente sintéticos. El laboratorio con datos reales, la validación y las demás capacidades de esta especificación siguen pendientes según [ROADMAP](../../tasks/ROADMAP.md).

## 1. Tres universos diferentes

**Universo de conocimiento:** miles de empresas identificadas, documentos e información fundamental procesada incrementalmente. **Universo observable:** instrumentos con precios y condiciones de uso verificadas. **Universo ensayable:** subconjunto con historia, disponibilidad temporal y costes adecuados a una estrategia concreta. Una empresa descubierta no cuenta como activo monitorizado ni como activo apto para backtest.

Primer alcance operativo propuesto: empresas estadounidenses vía SEC; cotizaciones e históricos de acciones/ETF solo mediante proveedores que se verifiquen; macro ECB/FRED/ALFRED y series públicas pertinentes; conservar cripto A21 como integración existente y claramente identificada. Renta fija individual necesita términos y convenciones propios; precios de ETF de deuda no sustituyen precios de bonos. Expandir regiones/activos por cobertura demostrada.

## 2. Contrato de datos

- Identidad: `entity_id`, `instrument_id`, `listing_id`, CIK/ISIN cuando existan, ticker y MIC por intervalo de vigencia. El ticker no es identidad estable.
- Temporalidad: `period_start/end`, `observed_at`, `published_at` o aceptación de filing, `received_at`, `available_to_strategy_at`, `revision_id`, `valid_from/to`. Desconocido se representa como desconocido. La disponibilidad histórica se deriva de publicación/aceptación verificable y política del feed: received_at de un backfill de hoy no es la fecha histórica, y period_end o una fecha filed sin hora no bastan como instante de disponibilidad. Si no consta hora, aplicar un criterio conservador explícito; no certificar PIT por inferencia silenciosa.
- Fuente: proveedor, endpoint/modalidad, licencia/restricción, hash de respuesta, fecha de revisión de derechos y transformación/versionado.
- Mercado: divisa, unidad, zona/calendario, tipo de precio, ajuste, retraso y alcance del feed. Diferenciar último negocio, bid/ask, cierre y precio indicativo.
- Fundamentales: concepto/taxonomía, unidad, periodo fiscal, duración o instante, formulario, accession y revisión; no sumar automáticamente acumulados YTD ni mezclar monedas.
- Calidad: completitud, duplicados, outliers, huecos, orden temporal, caducidad, correcciones corporativas y discrepancia entre fuentes. Los outliers se investigan, no se borran automáticamente.

Guardar versiones crudas solo cuando los derechos lo permitan. Mantener normalizado y feature derivada separados. Corrección publicada hoy no sobrescribe el pasado que una estrategia habría conocido. Construir snapshots inmutables y manifests reproducibles; la retención depende de derechos y espacio disponible.

## 3. Ingesta y frescura

Usar bootstrap por lotes, checkpoints, reanudación, deduplicación, backoff y cuotas por proveedor. Separar metadatos, fundamentales, cierres, cotizaciones y eventos: no tienen la misma cadencia. Consultar cambios incrementales y no descargar todo el universo cada minuto.

Prioridad de precios: instrumentos visibles/seguidos y futura cartera → universo de screening → backfills. Streaming solo donde exista feed permitido; el resto por lotes/cadencia. Mostrar en UI la fecha del dato y la recepción; un refresco de interfaz no rejuvenece el dato.

Plan de escala medible, sin prometer cuotas no contratadas:

1. Cien emisores reales para normalización fundamental e identidad, o el subconjunto accesible con faltantes explícitos. Prueba de paginación y reanudación con volumen superior, usando fixtures identificados.
2. Mil entidades identificadas y un informe de cobertura **real por campo**, sin confundir metadatos con cuentas completas.
3. Miles de entidades por importación masiva permitida y cambios incrementales. Benchmark con límite de memoria/disco; procesamiento por lotes, no cargar todos los documentos al LLM.
4. Universo de precios independiente, dimensionado por cuota verificada. Un conjunto pequeño actualizado de verdad vale más que mil precios caducados presentados como vivos.

## 4. Readiness por uso

`DatasetReadiness` se evalúa por instrumento/universo, familia, periodo, frecuencia y fuente. Debe devolver estado, razones, evidencias, versión y fecha.

| Gate | Exige | Si falta |
|---|---|---|
| RESEARCH_READY | Procedencia, derecho de uso, semántica y vigencia suficiente para la pregunta | Abstención o análisis parcial identificado |
| BACKTEST_READY | Lo anterior + disponibilidad temporal, historia suficiente, calendario, universo histórico/corporate actions/FX según familia | NOT_BACKTEST_READY; no backtest con apariencia válida |
| EXECUTION_SIM_READY | Lo anterior + spread, costes, liquidez y reglas de fills suficientes | No promocionar a simulación de ejecución |

La validez es específica: series macro revisadas sin vintage no son aptas para señales históricas; un histórico de precios sin delistings no certifica selección histórica de acciones; un feed parcial no representa el mercado consolidado. No hacer que un mismo flag global habilite todas las familias.

## 5. Investigación y valoración de empresas

Primer modelo fundamental: balance, resultados, cash flow, acciones, deuda/caja y ratios trazables con periodos comparables. Dossier con modelo de negocio, segmentos disponibles, evolución, riesgos, catalizadores y documentos originales. Las valoraciones DCF, múltiplos y escenarios se calculan en Python con supuestos explícitos, sensibilidad, fecha/FX y límites de datos. Si faltan precios o inputs no producir un precio objetivo inventado. Diferenciar valor calculado, estimación de analista y dato observado.

Un índice documental por entidad/periodo/tipo de documento y búsqueda de texto basta para empezar. Evaluar embeddings únicamente si una prueba de recuperación demuestra que mejora cobertura y citas sobre esa base.

## 6. Strategy Factory

La minería busca hipótesis económicamente defendibles y las intenta refutar. No consiste en pedir al LLM miles de estrategias ni en escoger el Sharpe máximo de un grid.

Cada `StrategyGenome` declara versión, mecanismo económico, falsación, universo histórico, inputs y disponibilidad, señales allowlisted, transformaciones, parámetros acotados, rebalanceo, sizing, restricciones, costes, benchmarks y protocolo de evaluación. El compilador rechaza operaciones o datos no admitidos. No ejecutar código arbitrario generado.

Flujo: **hipótesis registrada → comprobación de datos → experimento registrado → train/validation → robustez/Red Team → OOS reservado → decisión → seguimiento futuro**. Estados separados: `DRAFT`, `DATA_BLOCKED`, `QUEUED`, `RUNNING`, `FAILED`, `REJECTED`, `VALIDATED_FOR_REVIEW`, `RETIRED`. Ninguno equivale a orden o rentabilidad futura.

Registros:

- `HypothesisRegistry`: idea ex ante, mecanismo, falsación y parentesco.
- `ExperimentRegistry`: cada intento antes de ejecutarse; seed, código, parámetros, snapshots, ventanas, costes, hardware y resultado/error.
- `StrategyRegistry`: versiones candidatas, validaciones, relación con familias y promoción.
- `StrategyGraveyard`: rechazos con razones y evidencia; no borrar pérdidas ni ensayos fallidos del recuento.
- Registro de exposición OOS: quién/qué vio la muestra y cuándo. La exposición se hereda a descendientes e hipótesis derivadas aunque cambien de ID o familia. Tras consultarla, ya no es un test final intocable para variantes nuevas.

Primeras familias: buy-and-hold/efectivo como controles y tendencia temporal simple sobre series autorizadas. Después momentum transversal, reversión, value/quality y macro, **solo** al superar sus gates. No empezar con opciones, intradía ni estrategias que exijan datos inexistentes.

## 7. Validación que debe existir

Motor de referencia determinista con prueba exacta de señal/posición/retorno; señales ejecutables después de conocerse los datos, no al mismo cierre por defecto. Comisiones, spread, slippage, FX y corporate actions modelados y versionados; no omitir coste porque el bróker anuncie comisión cero.

Separación temporal train/validation/OOS y walk-forward. Purga/embargo cuando haya etiquetas o posiciones solapadas y corresponda al diseño; nunca dividir aleatoriamente una serie temporal para aparentar independencia. Examinar sensibilidad de parámetros, costes adversos, turnover, concentración, exposición al benchmark, dependencia de pocos instrumentos/días y estabilidad entre regímenes. Un régimen usado por la señal debe definirse con información disponible en t; segmentación ex post solo sirve como diagnóstico, sin reajustar sobre el OOS observado.

Registrar todos los trials y dependencias entre variantes. PSR/DSR/PBO/CSCV son métodos posibles con supuestos y tamaño muestral comprobados; no sellos automáticos de aprobación. Si una estadística no aplica, mostrar N/A y motivo. Definir umbrales y presupuesto de búsqueda antes del experimento, no ajustarlos para salvar al ganador.

Selección por evidencia, robustez, costes y diversidad de exposiciones/retornos, con incertidumbre visible. El comité revisa supervivientes; su opinión no reemplaza controles deterministas. El resultado aceptable de una campaña puede ser **cero estrategias aptas**.

La construcción de cartera y el riesgo de P5 producen propuestas con sizing, límites, escenarios y motivos de veto. La ejecución y los fills de una cartera forward corresponden a P6 Alpaca PAPER, ya autorizada y pendiente de superar los gates de datos/riesgo/conciliación. Los fills simulados internos de un backtest P5 son parte del experimento, separados de MASTER.

## 8. Ideas contrastadas y decisiones

Fuentes consultadas el 27-10-2026. Son referencias de diseño; no se han activado servicios ni probado cuotas con las credenciales del usuario.

| Idea | Evidencia primaria | Decisión para JAIME |
|---|---|---|
| SEC por entidad y lotes | [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces): submissions/XBRL y archivos masivos nocturnos, sin API key | Ampliar el preset a ingestión con CIK, filings/revisiones y checkpoints; no asumir cuentas comparables o PIT por recibir JSON |
| Cuotas SEC | [Developer Resources](https://www.sec.gov/about/developer-resources): acceso eficiente e identificado; máximo publicado 10 peticiones/s agregado | Límite propio conservador, User-Agent adecuado, backoff y bootstrap por lotes |
| Precios gratuitos con cobertura explícita | [Alpaca Market Data](https://docs.alpaca.markets/us/docs/about-market-data-api): Basic con IEX y 30 símbolos streaming; históricos con restricciones | Candidato a verificar para watchlist limitada; no prometer tiempo real consolidado de miles de activos ni contratar Plus |
| Streaming centralizado | [Stock stream](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data): feeds diferenciados y acceso según suscripción | Un adaptador backend distribuye eventos a consumidores; no una conexión por panel/agente |
| Historia analítica local | [DuckDB/Parquet](https://duckdb.org/docs/stable/data/parquet/overview): consulta de Parquet con filtrado y selección de columnas | Evaluar con benchmark después de corregir contratos; SQLite conserva transacciones |
| Macro tal como se conocía | [FRED/ALFRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html): consulta de información conocida en periodos pasados | Usar vintages cuando la estrategia los requiera; el dato revisado actual no se filtra al pasado |
| Agregadores de datos | [OpenBB proveedores](https://docs.openbb.co/odp/python/faqs/data_providers): cobertura/fechas dependen del proveedor | Referencia para adapters; no instalar otra plataforma como sustituto de resolver derechos, identidad y calidad |

La especificación extensa del usuario [Plan_JAIME_P5_P6](../Plan_JAIME_P5_P6.md) sigue como referencia de requisitos; el orden ejecutable es [ROADMAP](../../tasks/ROADMAP.md).


Referencias estadísticas primarias: [DSR](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf), [PSR](https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf), [PBO](https://papers.ssrn.com/sol3/Papers.cfm?abstract_id=2326253).
