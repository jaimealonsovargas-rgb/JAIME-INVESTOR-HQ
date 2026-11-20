> ARCHIVO INACTIVO · copia anterior a la auditoría del 11-11-2026. Sus próximos pasos y autorizaciones no gobiernan el trabajo actual. Enlaces relativos reubicados; contenido histórico conservado.

# Estado actual de JAIME INVESTOR HQ



## 11-11-2026 · B2.3: revisión de contratos y divisa IBKR entregada



Conciliados AAPL/MSFT/WMT con los vínculos SEC/Alpaca existentes. USD documentado para los contratos observados; NASDAQ se mantiene separado de la ruta SMART. Revisión fijada a las 09:55 Madrid, informe privado conservado por hash, archivo idempotente bajo presupuesto y sin migración/escritura SQLite ni nuevas peticiones a proveedores. La ficha muestra contrato, moneda, fechas y procedencia en los detalles de calidad. [Entrega](../../actual/ENTREGA_B2_3_CONTRATOS_IBKR.md).



Diagnóstico `daily-trend-data-v2`: divisa de la observación comprobada; identidad histórica y restantes controles pendientes. No se atribuye la revisión a fechas anteriores. La pérdida/cambio de evidencia retira la confirmación correspondiente. B2 abierto, P4 PARTIAL, PAPER ONLY y órdenes 403. IBKR complementa identidad; no sustituye SEC ni la ruta futura Alpaca PAPER.



**98 tests backend y 16 frontend afectados correctos; TypeScript/build y navegador correctos.** Repetición real con corte fijo, fichas SEC/Alpaca coherentes y consulta anterior a la revisión sin divisa futura. **13 tablas protegidas/18 modelos preservados por hash**. Archivo comprimido IBKR: 670 bytes. Evidencia privada `output/b23-ibkr-reconciliation-20261111.json` y log `output/b23-ibkr-tests-final.log`. Avisos preexistentes de TestClient/httpx y bundle 3D; no se repite suite completa.



Siguiente punto: **B2.3, continuidad de identidad en un intervalo histórico acotado**; después ajustes/acciones corporativas y ampliación de series. Piloto europeo IBKR condicionado a derechos/acceso/coste cero. Mantener el orden B2 → B3 minería → B4 validación → B5 autonomía/riesgo → B6 Alpaca PAPER. No repetir instalación, n8n, bootstrap ni oficina.



Verificación tras arrancar servicios: API de las tres acciones correcta y órdenes 403. La agenda A22 existente refrescó HT/ZSE a las 16:38 Madrid; solo su `last_seen_at` cambió entre las tablas protegidas. Reconstrucción en memoria reproduce el hash anterior exactamente; otras 12 tablas/18 modelos idénticos. No se deshizo el refresco ni se modificó la agenda. Evidencia `output/b23-ibkr-runtime-20261111.json` y `output/b23-ibkr-runtime-audit-20261111.json`.



## 11-11-2026 · IBKR: piloto real de contratos solo lectura



Usuario con sesión de simulación verificada en navegador y TWS. API habilitada con autorización expresa, Read-Only y localhost-only conservados, puerto 7497. SDK oficial 1052.01 firmado por IBKR, licencia aceptada por el usuario; Python `ibapi==1052.1`/`protobuf==7.36.2` en entorno aislado, compatible en esta prueba con Python 3.14.4. Sin cambiar dependencias del backend.



Prueba real **09:38 Europe/Madrid**: cuenta Paper exacta validada por hash privado, reloj/servidor 226 y tres contratos únicos AAPL/MSFT/WMT, USD y NASDAQ según respuesta IBKR. Mensajes salientes `[71,49,9,9,9]`; desconexión al terminar. Candidatos actuales, todavía sin conciliación/persistencia en P2; no prueban continuidad histórica ni cobertura de mercado. **Sin precios, históricos ni órdenes**, sin escritura en SQLite/MASTER. B2 abierto, P4 PARTIAL.



Validación: diez tests de política y tres del SDK offline correctos (798 intentos de mensajes no autorizados bloqueados), `pip check` correcto. Evidencia privada `output/ibkr-contract-probe-20261111.json`, SHA-256 `402f5bb6c22eba424497a961ad4eabb2ae5855a1e50c9345f128ca8db2a566a2`. Instalación/sesiones TWS excluidas de Git. Herramientas inventariadas aparte: `.tools/ibkr` ~243 MB y TWS ~560 MB, sin borrar datos. [Operación y límites](../../../integrations/ibkr/README.md).



Comprobación adicional: **37 tests de seguridad** correctos, incluido `POST /api/orders=403`, sobre bases temporales. Total de esta entrega: 50 tests (10 política + 3 SDK offline + 37 seguridad). Aviso de deprecación preexistente de TestClient/httpx, sin fallo. No se repite la suite completa ni el frontend porque el piloto no los modifica.



Siguiente: contrastar los tres contratos con SEC/Alpaca/plaza y conservar evidencia de divisa/identidad; después piloto europeo e históricos acotados con derechos/coste cero. No repetir instalación ni activar un proveedor continuo por el éxito de esta prueba.



## 09-11-2026 · IBKR: comprobación de requisitos



Usuario aún sin cuenta. Ejecutado diagnóstico local reproducible: Python 3.14.4, SDK ibapi/protobuf ausentes y sin aplicación en rutas estándar; estado NOT_READY, cero peticiones al broker. Sin instalaciones ni cambios de datos financieros. Documentada discrepancia entre FAQ trial y respuesta de soporte; no se promete cobertura gratuita. [Preparación y siguiente dependencia](docs/actual/IBKR_PILOTO_PREPARACION.md). Pendiente acceso Paper/elegibilidad del usuario, compatibilidad del SDK y adaptador de contratos; identidad/divisa B2 sigue abierta.



## 09-11-2026 · Almacenamiento entregado; TWS API evaluada



Control de admisión compartido para captación/modelos: 4 GiB data, 12 GiB output, 16 GiB conjuntos, 5 GiB libres más reserva de 512 MiB por unidad. Medidos unos 7,96 GiB conjuntos; sin borrar originales, modelos ni backups. Panel en Sistemas → Casos y entregas. Pausa y recuperación de colas verificadas sin consumir intentos. 525 backend/111 frontend superados, una omisión preexistente, build y navegador correctos; 11 tablas y 18 modelos preservados, órdenes 403 y agenda n8n intacta. [Entrega y límites](../../actual/ENTREGA_B2_ALMACENAMIENTO.md).



Investigada TWS API: candidato para identidad y mercados, condicionado a permisos, coste cero y sesión. Propuesta de piloto solo lectura; sin instalación, conexión, pago ni órdenes. [Evaluación IBKR](docs/actual/IBKR_TWS_EVALUACION.md). Siguiente B2: divisa/identidad temporal y ampliación histórica acotada; IBKR entra como evaluación de viabilidad, no sustituye automáticamente Alpaca ni habilita B3.



## 08-11-2026 · B2.3: vínculo del piloto y diagnóstico de históricos



Apple, Microsoft y Walmart tienen vínculo actual empresa–acción documentado con los originales SEC y el catálogo Alpaca fijado. La comprobación distingue clase/contexto XBRL: MSFT aparece también en bonos. No fusiona registros ni convierte el instrumento lógico en ejecutable. Divisa nativa e identidad histórica siguen pendientes.



Diagnóstico `daily-trend-data-v1`: Apple conserva **21/21 sesiones raw IEX** de septiembre, aptas solo para exploración descriptiva; Microsoft/Walmart sin histórico de la serie seleccionada. **Los tres bloqueados para backtest**, con razones visibles en Centro de activos → Precios e históricos → Calidad para investigación. Dos ejecuciones iguales conservan las huellas de 13 tablas y los 18 modelos; sin nuevas descargas ni migración (0013).



Validación: **509 backend, 102 frontend superados**, una omisión preexistente; TypeScript/build correctos tras ajustar el tipo del validador. Navegador, móvil, salto emisor–acción y desconexión verificados. [Entrega, evidencia y límites](../../actual/ENTREGA_B2_3_IDENTIDAD_HISTORICOS.md). B2 continúa abierto. Siguiente: presupuesto agregado de disco y conservación antes de ampliar históricos, manteniendo pendientes explícitos de divisa, continuidad temporal y ajustes.



## 07-11-2026 · B2.5 cerrado: disparo automático observado



Completada la comprobación pendiente del temporizador real de n8n: agenda temporal a las **10:22 de Madrid**, tarea `succeeded`, ejecución en modo `trigger` con estado `success`. JAIME recibió el segundo ciclo, terminado PARTIAL: Apple v7 y Microsoft v5 PASSED; Walmart v6 PARTIAL por sus pendientes contables. **18 modelos, los 16 previos intactos**, ledger y cartera con las mismas huellas. Restaurada la agenda original de seis horas (00/06/12/18 UTC). No se acredita funcionamiento continuo durante la interrupción del ordenador.



Desactivado el catálogo MCP opcional de n8n, ajeno a este flujo. Se conserva la validación completa del 06-11 (**485 backend, 98 frontend, una omisión preexistente**); el cierre del 07-11 añade evidencia del scheduler y comprobación de servicios/bloqueo de órdenes. [Entrega y límites](../../actual/ENTREGA_B2_5.md). B2.5 terminado dentro del piloto, **B2 aún abierto**. Siguiente paso: identidad SEC–instrumento–listing e históricos admisibles del piloto B2.3, según [ACTUAL](tasks/ACTUAL.md). Sin repetir instalación, migración ni bootstrap.



## 06-11-2026 · B2.5 completado: n8n y ciclos SEC en sombra



n8n Community 2.46.6 instalado localmente y flujo de seis horas publicado, con UTC explícito y binding 127.0.0.1. Un único propietario para la agenda SEC; JAIME conserva cola, autenticación, idempotencia, presupuesto y recuperación. Piloto de tres emisores, seis tareas SEC y revisión contable, sin LLM ni órdenes. A21 conserva su agenda independiente. [Entrega B2.5](../../actual/ENTREGA_B2_5.md) · [Arranque](../../../integrations/n8n/README.md).



Migración **0013_shadow_cycles**, respaldo `output/b25-before-0013.db`: 38 tablas previas idénticas por conteos/hashes, integridad y claves foráneas correctas. Dos ejecuciones del workflow real de n8n crean un solo ciclo, un job y seis recibos; el segundo envío y un reenvío después de reiniciar el backend recuperan el mismo resultado. Apple v6/Microsoft v5 PASSED, Walmart v5 PARTIAL por sus pendientes; 13 modelos anteriores preservados, 16 en total. Ledger/cartera conservados. No se atribuye aceptación financiera completa al éxito de n8n.



Panel en Sistemas → Casos y entregas: estado, pausa de nuevas solicitudes, cancelación y resultados. Navegador real con móvil y desconexión verificados. Check final: **485 backend y 98 frontend superados**, una omisión preexistente, TypeScript/build correctos; órdenes 403. P4 PARTIAL, coste obligatorio 0 EUR. Runtime n8n/Node aproximado 2,18 GB, más datos locales de n8n y caché npm.



Scheduler registrado para 00/06/12/18 UTC; próxima frontera al verificar: 06-11, 19:00 Madrid. Las dos ejecuciones observadas se iniciaron mediante CLI de n8n; no se ha observado aún esa frontera horaria. Servicios arrancados al entregar, sin inicio automático de Windows ni funcionamiento con PC apagado. Próximo trabajo según [ACTUAL](tasks/ACTUAL.md): cerrar identidad e históricos admisibles del piloto B2.3 antes de experimentar con B3.



## 06-11-2026 · Lote contable cerrado y adaptación de Day Trader



**B2.4:** Apple, Microsoft y Walmart concilian balance y caja con las partidas de sus informes originales SEC; los seis controles tienen residuos cero. Modelos actuales Apple v5/Microsoft v4 PASSED y Walmart v4 PARTIAL: falta un subtotal etiquetado para el ratio pasivos/activos. Plantilla `company-accounting-v3.1`. Se conservan los siete modelos previos y seis versiones técnicas (13 en total). El evento real de Apple permanece en v3/NEW_PERIOD; no se atribuye un filing nuevo a estos ajustes. [Entrega, fuentes y límites](../../actual/ENTREGA_B2_4.md).



Lote reutilizable de hasta 25 CIKs explícitos, adquisición SEC con cuota/recibos/hashes y reconstrucción local. La web muestra partidas y documentos del informe anual. Repetir el lote o construir las tres empresas desde la web conserva sus IDs/versiones. Corregida una dependencia de la última consulta del catálogo que alteraba la identidad histórica. Ledger, cartera y evento SEC conservan sus huellas. Un arranque del backend añadió una valoración rutinaria; las 14 anteriores están preservadas y las valoraciones tampoco cambiaron durante el lote final.



Day Trader ya estaba incluida entre las skills: nueve módulos/22 archivos, contrastados con el commit `3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd`, sin ejecutar sus scripts. Incorporado el control de cobertura del informe anual conocido localmente. Documentada su adaptación a scanner, hipótesis, simulación, alertas y riesgo en las fases correspondientes, con los límites observados de datos, calendario, costes y Monte Carlo. [Revisión y adaptación](../../actual/DAY_TRADER_ADAPTACION.md).



Verificación final: **468 pruebas backend y 95 frontend superadas**, una prueba frontend omitida previamente; TypeScript/build correctos. Navegador: las tres empresas, botón de construcción, partidas específicas, enlaces SEC, 1366/390 px, sin errores JavaScript ni desbordamiento. `POST /api/orders` HTTP 403. Evidencia privada `output/b24-statement-batch-20261105.json`, `output/b24-batch-browser.json` y `output/b24-final-check.log`. Coste obligatorio 0 EUR, P4 PARTIAL. El siguiente paso es **B2.5: CycleRequest/n8n en sombra**, según [ACTUAL](tasks/ACTUAL.md); DCF, identidad, streaming y retención conservan sus pendientes. Este cierre no implementa P5/P6.



## 04-11-2026 · Primer cierre europeo en el Centro de activos



**B2.3, piloto de una acción.** El actualizador P2 recibió diez sesiones de Hrvatski Telekom (HT, ISIN HRHT00RA0005, XZAG, EUR por acción) en una descarga oficial. La última sesión recibida es el 03-11-2026. El Centro de activos encuentra HT por ISIN y permite abrir la ficha directamente desde «Cierres europeos». Muestra cierre histórico, fecha de sesión, antigüedad y fecha de recepción. [Ficha de la bolsa](https://zse.hr/en/papir/310?isin=HRHT00RA0005).



La modalidad A22 de Nivel 1 solicita los catorce días naturales anteriores al día UTC y guarda los cierres de las sesiones con operaciones en negociación continua. Conserva los importes en EUR tal como cotizaron, sin ajustar por dividendos ni desdoblamientos. El uso es personal, interno y no comercial. La política de la bolsa y la definición del cierre figuran en la [política de datos, apartado 4.4](https://zse.hr/UserDocsImages/docs/marketdata/vendors/2019-05%20-%20ZSE%20Data%20vending%20policy%20of%20the%20Zagreb%20Stock%20Exchange.pdf) y las [reglas de negociación](https://zse.hr/UserDocsImages/docs/legal/rules/Exchange%20Rules%202024_consolidated.pdf).



La cadencia es de seis horas mientras funciona el servicio local. La ficha marca el dato como pendiente al vencer la caché o al superar cinco días naturales desde la sesión. En la prueba del día 4 se verificaron una descarga, diez observaciones, una ficha y una versión antes y después de repetir la consulta. Pruebas aisladas cubren revisiones del precio, sesiones sin operaciones, fechas inválidas, restricciones de acceso y antigüedad. Falta observar la incorporación del próximo cierre publicado.



Evidencia privada en `output/europe-ht-pilot.json`. Verificación en navegador y suite completa con **453 pruebas de backend y 95 de interfaz superadas**, una omitida previamente y compilación correcta. El ledger, la cartera y los siete modelos previos conservaron sus huellas. Órdenes HTTP 403, coste 0 EUR, P4 PARTIAL. Catálogo P2 con 39 modalidades, 34 proveedores candidatos y 35 adaptadores implementados. Yahoo y Stooq siguen como candidatos de Nivel 2.



Actualizado 04-11-2026 (Europe/Madrid). B1/B2.1/B2.2 completados; B2.3 lectura real y B2.4 conciliación/actualización por filing real verificadas. Skills P4 incorporadas; Yahoo/Stooq candidatos Nivel 2 pendientes de habilitación. Sede visual aceptada. [Bitácora anterior](../2026-10-27/STATUS_PRE_REORGANIZACION.md) conserva resultados históricos.



## 2026-11-03 — skills y niveles de datos, incorporados localmente el 04-11



Entrada localizada en la [PR #8](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/pull/8), todavía abierta, commit `41ccf4e41bb0927f4d718e78e1fc01d639b6f53e`. Importados 143 archivos/39 skills con licencias; sin ejecutar scripts. D027/D028 de esa PR se integran como D038/D039 locales por colisión de identificadores; historia previa preservada e invariantes 9/10 incorporados. No se fusionó la PR ni se publicaron cambios remotos.



Adaptadas morning-note, thesis-tracker y catalyst-calendar al dossier y resultado del ciclo P4 existente. Nota con evidencia vigente, tesis solo si existe y calendario solo con fechas confirmadas. Desplegable en Research. El dossier real comprobado se abstiene por datos insuficientes; no se inventan tesis, eventos ni inferencias. P4 PARTIAL. Yahoo C01/Stooq C02 son candidatos UNOFFICIAL_SOURCE/internal/sin redistribución: 38 modalidades y 33 proveedores candidatos, pero siguen siendo 34 adaptadores implementados. Condiciones/endpoint/identidad europea pendientes; no están conectados.



## 2026-11-04 — nuevo filing real y eventos SEC



Migración aditiva **0012_company_updates** y outbox idempotente en el worker SEC existente. Apple: filing **0000320193-26-000026 de 03-11-2026**, ejercicio cerrado **26-09-2026**, genera automáticamente **v3 / NEW_PERIOD**. V1/v2 conservadas; seis modelos anteriores intactos, ledger sin cambios y órdenes HTTP 403. Job repetido sin duplicado. Backup `output/b24-before-0012.db`, 37 tablas anteriores idénticas tras migración, integridad OK y Alembic sin drift.



`manage.py check` final: **443 pytest, 93 Vitest y una omisión preexistente; TypeScript/build correctos**. Primera ronda falló en tres expectativas antiguas del tamaño del catálogo; corregidas y check completo repetido. Avisos preexistentes httpx/TestClient y chunk 3D conservados. Sin dependencias nuevas, gasto, P5/P6 ni órdenes. [Entrega, evidencia y límites](../../actual/ENTREGA_B2_4_ACTUALIZACION_Y_P4.md).



## Entrega visual 04-11



Paneles simplificados y sede antracita; LED amarillos con halo y mayor grosor, recepción centrada con mostrador más grande y pared de piedra, mesas ampliadas, iluminación cálida al final de pasillos y Riesgos alineado al lateral derecho. Nueve departamentos/16 NPC y navegación preservados; colisiones actualizadas al mobiliario. 90 pruebas frontend y build en la ronda inicial; 13 pruebas afectadas y build tras el acabado final. Navegador en tres tamaños sin errores JavaScript, con controles y cabecera móvil verificados. [Entrega, capturas y límites](../../actual/ENTREGA_VISUAL_SEDE.md). No se ha avanzado contabilidad ni activado órdenes durante este trabajo visual.



## Capacidad real



| Área | Estado |

|---|---|

| Oficina P1 / ledger P3 | Implementados; se conservan |

| Datos P2 / catálogo B2.1 | 8.023 emisores y 10.430 símbolos SEC; registro operativo anterior separado, sin convertir directorio en datos de mercado |

| Research P4 | PARTIAL; ciclo A21 descriptivo con tres roles Python; debate profundo sin aceptación |

| Agentes | 30 roles registrados; no 30 procesos/modelos ni 30 capacidades completas |

| Universo empresarial / modelos | Catálogo y cuentas SEC de 100 emisores; precios IEX separados por identidad Alpaca; balance y caja de tres emisores conciliados; ratio de Walmart y valoración pendientes |

| Minería P5 | Autorizada después de mejoras; no implementada |

| Ejecución P6 / LIVE | P6 Alpaca PAPER autorizada, aún no implementada; LIVE fuera de alcance; órdenes bloqueadas |



## Entrega 27-10: reorganización B0



Recuperado contexto de «Construye la base P0 de JAIME» y autorización P5. Auditoría de documentación, código y capturas históricas; reproducciones sintéticas SEC/historia/aliases. Unificados mandato, entradas, estado, roadmap y trabajo siguiente. Planes/prompts puntuales y bitácora retirados de lectura activa y preservados en archivo. Añadida investigación oficial de tres plantillas financieras Anthropic y adaptación local a B2.



Esa primera entrega fue documental. La implementación posterior B1 corrige los defectos reproducidos, añade fichas por persona y corrige el ciclo de vida 3D. El circuito n8n → datos → 30 especialistas → P5 → riesgo → Alpaca PAPER queda incorporado a la arquitectura por instrucción expresa del usuario.



## Entrega B1



Revisiones inmutables, recibos de descarga, consultas temporales y ventanas sin duplicados; alias multiproveedor y vínculo CIK; contrato fundamental coherente; fichas con tareas/últimas entregas y estados honestos. Migración 0007 aplicada con backup: las 20 tablas preexistentes no cambian sus registros. Ledger conservado.



**326 tests backend, 68 frontend (uno omitido), TypeScript/build correctos.** Navegador: cuatro tamaños, persona→dossier, desconexión, datos caducados, modelo ausente, clic NPC, Escape y cámara. Reparado error de disposición GPU en StrictMode. Detalles y límites en [ENTREGA_B1](../../actual/ENTREGA_B1.md).



Cierre 28-10: 77 pruebas afectadas pasan después de ajustar la cota de publicación SEC y conservar la identidad del estado financiero en la entrada compacta de IA. Incluyen dos nuevas regresiones; no se suman a la suite anterior como pruebas distintas.



Inventario al cerrar B1: 99 instrumentos (96 macro, 2 cripto, 1 FX), ninguna acción. Era anterior al directorio B2.1. Los presets siguen sin bastar para el circuito completo; [revisión y plan](docs/actual/PROVEEDORES_Y_COBERTURA.md). No se instalaron n8n/modelos ni se activaron conexiones PAPER.



## Entrega B2.1



Contacto SEC configurado privadamente con el dato facilitado por el usuario. Dos descargas reales (copia de revisión y base habitual) coinciden: **8.023 emisores, 10.430 símbolos/listados, cero conflictos detectados**. Son identidades de catálogo; no empresas analizadas ni instrumentos elegibles. Alpaca continúa sin claves.



Centro de activos desde la oficina o `?activos=1`: búsqueda paginada, ficha enlazable, filtros, procedencia y versiones. Captación idempotente, cuota compartida, validación completa y recuperación tras interrupción. Alias contradictorios quedan señalados; una ausencia no implica delisting.



Migración 0008 aplicada con respaldo `output/b2-before-0008.db`: las 21 tablas anteriores quedan intactas durante la migración. La captación posterior solo incorpora el nuevo catálogo y su cuota; las 20 tablas protegidas restantes no cambian. **339 pruebas backend, 71 frontend (una omitida), build correcto.** Tras congelar la definición de migración se repiten 21 pruebas afectadas, todas pasan. Navegador con datos reales en cuatro tamaños, sin errores JavaScript. [Entrega y límites](../../actual/ENTREGA_B2_1.md).



## Entrega B2.2



Piloto real de **100 emisores, 200 descargas SEC**. Al cotejar el 28-10: **353.528 cifras consultables y 12.961 registros documentales**, con originales conservados, unidades, periodos, documentos y recibos. Centro de activos incorpora cuentas anuales, documentos y cifras comparativas. 71/100 cuadros reúnen seis magnitudes básicas; 29 muestran cobertura parcial. Seis cifras con periodos anómalos quedan aisladas. Los documentos son metadatos/enlaces; no HTML analizado.



Cola persistente, idempotencia, cuota SEC común de 1/s y 60/min, pausa/reanudación/cancelación y recuperación tras interrupción. Snapshot temporal local, sin certificar PIT de mercado. Cuentas por documento/periodo/divisa, sin completar huecos con otra presentación ni convertir moneda contable en moneda del instrumento.



Migración 0009 y transferencia de evidencia ya verificada, backup `output/b22-before-0009.db`; **25 tablas anteriores idénticas durante esos pasos**. No repetición de 200 consultas. HTTP habitual: 100 emisores con datos/documentos, lote completado, órdenes 403. 353 pruebas backend en suite completa y 37 afectadas tras el cierre final (incluyen dos nuevas); 76 frontend, una omisión preexistente, build correcto. Navegador en cuatro tamaños sin errores; 60 cifras de Apple/Microsoft/Walmart cotejadas con originales y un cambio comparativo real conservado. [Entrega, evidencia y límites](../../actual/ENTREGA_B2_2.md).



## Entrega B2.3 — núcleo de lectura



Integración privada GET con Alpaca PAPER/IEX: catálogo UUID, snapshot, OHLCV diario paginado, ajustes separados, calendario/DST, corporate actions por process_date y cuenta/posiciones de solo lectura. Cola recuperable, idempotencia, cuotas compartidas y límites de almacenamiento. UI con antigüedad, sesiones, gráfico/tabla y estados de acceso. Corregida reserva SEC indebidamente realizada al consultar el estado.



Estado inicial del 29-10: sin claves ni datos Alpaca. **Cierre externo 30-10:** claves locales cargadas; ocho endpoints AVAILABLE tras consultas reales; 14.407 instrumentos, snapshot AAPL y 21 barras diarias IEX de septiembre con 21 sesiones esperadas y ningún hueco. Última operación correctamente marcada antigua en la comprobación previa a la sesión. Trading 212 Demo: HTTP 200 y 500 registros normalizados (muestra acotada del adaptador, no universo completo). Vínculo SEC/instrumento sin certificar y sin streaming/watchlist automática. [Evidencia](../../actual/evidencias/b23-real-connection.json).



Migración 0010, respaldo `output/b23-before-0010.db`, 31 tablas anteriores idénticas durante migración. Suite backend 412 correctas, después 13 afectadas por cierre de almacenamiento; frontend 86/una omitida, después 10 afectadas y build. Navegador sintético con API real local en cuatro tamaños sin desbordamiento/errores; app habitual conserva cuentas SEC y bloquea captación sin claves y órdenes (403). [Entrega y pendientes](../../actual/ENTREGA_B2_3.md).



## Entrega 30-10: primer tramo B2.4



Modelos contables inmutables, ratios y comparativas del mismo informe, revisión racional independiente y tres vistas de análisis. Apple/Microsoft/Walmart: 120 inputs contrastados con originales; revisión PARTIAL por conciliaciones ausentes. Roles existentes y entregas reales visibles, sin inferencia inventada. Migración 0011, backup output/b24-before-0011.db y 35 tablas anteriores intactas tras migración y builds.



426 tests backend; suite frontend 86/una omisión y después 4 nuevas pruebas específicas; build y 11 comprobaciones de navegador correctos. [Entrega y límites](../../actual/ENTREGA_B2_4.md).



## Próximo bloque



Segundo tramo B2.4: parser/plantilla v2 y reprocesado de originales con hash, versiones históricas preservadas. Tres modelos v2 guardados; total declarado del balance coincide en los tres y caja de Walmart concilia con diferencia cero. Apple/Microsoft bloquean caja por FX compatible ausente; los componentes del balance siguen incompletos. MASTER/ledger intactos e idempotencia verificada. Suite completa backend: 435 correctas; tras ajuste final, 40 afectadas correctas con dos nuevas regresiones. Cinco pruebas frontend y build correctos. [Evidencia y límites](../../actual/ENTREGA_B2_4.md).



Actualización del 06-11: el lote de tres emisores y el evento de nuevo filing real están comprobados. Continuar [ACTUAL](tasks/ACTUAL.md) con B2.5 n8n en sombra. DCF e interpretación local aún requieren sus inputs y contrato. B2.3 conserva identidad/streaming; Nivel 2 requiere condiciones/endpoint y derechos antes de habilitarse. B2 y P4 siguen abiertos. Esta entrega no inicia P5/P6.



## Evidencia histórica, no repetida hoy



26-10: 317 tests backend, 63 frontend, TypeScript/build; dos ciclos autónomos A21 registrados. Estas cifras proceden de la bitácora y no son pruebas ejecutadas por la reorganización. Último commit de partida `5b56dc8e699a73e6d4b9519a03088e5b05151b8e`.



La investigación encontró fallos aunque existían tests verdes. B1 añade las regresiones y arreglos; P4 sigue PARTIAL y no se cierra por contadores de pruebas.

