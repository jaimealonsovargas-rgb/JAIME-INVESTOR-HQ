# Estado del proyecto

## 2026-10-23 · Reparación prioritaria Bull/Bear/Chair — PARTIAL

**No hay debate completo financieramente validado; no declarar P4 terminada.** Se reparó el transporte con `debate-wire.v2` (claves/IDs reversibles, todos los campos públicos conservados, gramática y validación Python) y se añadieron comparaciones Python, guardas de contradicción/eco/incompletitud, métricas de fallos y cuarentena local de candidatos rechazados. Los dossiers antiguos se revalidan al abrirlos y ocultan argumentos inválidos. Template `p4.14-debate-wire`, esquema sin cambios `0005_data_history`. No se ampliaron timeouts, tokens ni retries.

**Evidencia real:** cuatro casos acotados, seis inferencias financieras en dos modelos existentes. Ya no hubo TIMEOUT/TRUNCATED_OUTPUT: Bull cerró JSON con 118–161 tokens. Qwen2.5 terminó el caso en 47,824 s y Qwen3 en 84,682 s, pero Bear repitió el argumento y fue rechazado; Chair siguió bloqueado. Revisión final: Bull tampoco aporta un mecanismo favorable válido (Qwen3 además corta frases); ambos argumentos se retiran. Una guarda experimental demasiado amplia se corrigió antes del último ensayo, sin borrar el fallo histórico. **No es un PASS financiero.** [Informe, causas, límites y siguiente paso](docs/evidencias/P4/reparacion-debate-20261023/README.md).

**Rendimiento:** red eléctrica comprobada, ~16 GB, un solo LLM. Qwen2.5 wire v2: 19,27–20,31 s/llamada y 18,60–18,94 tok/s; Qwen3 final: 29,31–45,38 s y 9,24–11,54 tok/s. RAM libre mínima 620,5 / 1066,6 MiB; RSS pico 1159,3 / 2649,2 MiB. Caché y carga distintas: no atribuir causalmente toda la mejora. Runtime descargado de RAM al terminar, sin nuevas inferencias ni descargas.

**QA:** check completo 278 pytest, 54 Vitest + 1 opt-in omitido, TypeScript/build; tras último ajuste de trazabilidad, 21 pruebas focalizadas correctas. Audit: cero vulnerabilidades conocidas; diff-check correcto. Ordinario sin LLM `COMPLETE/VERIFIED_DATA` en 1,036 s; insuficiente `COMPLETE/ABSTAINED` en 1,031 s. Reinicio/lectura real conserva jobs y retira Bull inválido. Capturas privadas de oficina, cuatro paneles y videowall; sin errores JS ni overflow. Intel, movimiento continuo 12 s, Equilibrado1920×1080/DPR0,8: **56,74 FPS móviles**, 670 muestras, p95 22,5 ms, **sin LLM**. No sustituye la prueba bajo inferencia pendiente.

**Seguridad:** 30 roles; cola/activos0; MASTER10000.00EUR ficticios, 0 posiciones y hash intacto `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`; PAPER ONLY, orders_enabled=false, POST/api/orders403, coste0EUR. Autonomía programada no implementada; P5/P6 no iniciados. No repetir estos runs: siguiente trabajo debe mejorar hipótesis/evidencia y probar razonamiento por etapa antes de reabrir el pipeline profundo.

**Git de implementación:** `5b34e4b` conserva el contrato, validadores, auditoría y tests de esta reparación. Evidencias y cierre documental se versionan aparte; ningún payload financiero privado ni peso del modelo entra en Git.

---

## 2026-10-23 · Goal P4 LLM local y profundidad adaptativa — PARTIAL

**P4 aún no cumple su criterio profundo.** La arquitectura propuesta en `docs/P4_PROFUNDIDAD_Y_CIERRE.md` se implementó y probó: `ordinary` por defecto, Python determinista y como máximo una síntesis local opcional; `deep` explícito con Bull/Bear/Chair secuenciales. Los treinta roles, contratos, permisos, jobs persistentes e idempotencia por profundidad se mantienen. Cada nueva inferencia tiene un intento y presupuestos estrictos; sin modelo local la investigación ordinaria continúa y el debate no se fabrica. La UI Research presenta profundidad, estados reales y cuatro métricas Python trazables antes de abrir el dossier. No hay migración: esquema `0005_data_history`.

**E2E real:** caso A BTC histórico CoinPaprika autorizado para uso personal local, refrescado por P2: `COMPLETE / VERIFIED_DATA`, 3 jobs Python, 91 evidencias, **1,416 s**; las observaciones anteriores se degradaron correctamente al caducar. Caso C BTC-USD sin serie directa autorizada: `COMPLETE / ABSTAINED`, ningún LLM ni cifra inventada. Caso B profundo: 2 intentos acotados, **88,529 / 92,650 s**; cuatro jobs Python correctos cada uno, Bull falló por salida de 384 tokens y Bear/Chair `BLOCKED`. Sin debate aceptado. Síntesis opcionales: Qwen2.5 contradijo las estadísticas Python (revalidación `PARTIAL / REJECTED`); Qwen3 falló grounding numérico (`PARTIAL`, cálculos Python conservados; `ABSTAINED` al caducar la fuente). Un test nuevo impide que una síntesis opcional fallida vuelva a marcar datos vencidos como vigentes. No se repiten esas inferencias. [Informe y evidencia](docs/evidencias/P4/adaptativo-20261023/README.md).

**Diagnóstico controlado de los dos modelos ya instalados, enchufado/100 %:** Qwen2.5 Q4_K_M 586/28 tokens, prefill 8,257 s, TTFT 8,469 s, generación 14,58 tok/s, RSS máximo 1787 MiB y RAM libre mínima 1455 MiB. Qwen3 Q8_0 590/38, prefill 14,862 s, TTFT 14,871 s, generación 9,87 tok/s, RSS 2319 MiB y RAM libre mínima 724 MiB. Ambos JSON válidos solo en fixture sintético; Qwen2.5 no se aprueba por rapidez porque falló financieramente. La paginación global fue mayor con Qwen3, sin atribuirla toda al proceso. Ningún modelo adicional ni API de pago.

**QA:** `manage.py check` final exit 0: **220 pytest, 54 Vitest + 1 opt-in omitido, TypeScript/build**; suite Research: **50/50**. `manage.py audit` exit 0, cero vulnerabilidades conocidas; `git diff --check` correcto. Navegador real 1920×1080: oficina y Research por clic NPC, casos A/C/B visibles y consola limpia tras recarga. Los 502 observados solo durante el reinicio manual del backend fueron transitorios. Watchlist y MASTER operativos. Una muestra de 60 FPS/DPR0,8 tuvo movimiento con flechas, pero la proximidad abrió Recepción durante la ventana y **no sustituye** el benchmark válido anterior bajo LLM (31,68–37,71 FPS del 21-10). Capturas privadas auténticas `output/p4-adaptive/`, con hashes en el informe; no se redistribuyen precios CoinPaprika.

**Invariantes:** MASTER `10000.00 EUR` ficticios, 0 posiciones, 1 evento y hash `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836` intacto; `PAPER_ONLY`, `orders_enabled=false`, HTTP `POST /api/orders=403`, coste adicional 0 EUR. Alineación documental hacia research autónomo y futura fábrica cuantitativa registrada en `docs/ARQUITECTURA_AUTONOMIA_P4_P5.md` (commit `666f28e`), sin implementar P5/P6. Pendiente esencial: Bull/Bear/Chair completo, semánticamente correcto y viable en 16 GB; no declarar P4 `SUCCESS`.

**Git:** commits `d7a1da3` (runtime y UI), `b283e51` (evidencia) y `62f1244` (merge seguro de `e9943ce` desde `origin/main`). Primer push normal verificado: HEAD y `origin/main` coincidieron en `62f12442c7645cb9b2cdc42cc738d484b9e6435d`, con árbol limpio. No se usaron reset, clean ni force-push.
---

## 2026-10-23 · Realineación arquitectónica a autonomía local — SOLO DOCUMENTACIÓN

Se ha contrastado una auditoría integral recibida del usuario con el repositorio GitHub. Decisión de producto: JAIME debe ser un núcleo de investigación y futura simulación cuantitativa **autónomo mientras el backend esté encendido**, supervisado por la oficina 3D, no principalmente un sistema de preguntas y debates. Se conservan la interfaz, P2/P3, 30 roles, un único LLM local, 16 GB RAM y presupuesto 0 EUR.

**Cambios de este Goal:** visión, instrucciones Codex, ADR, índice, especificaciones P2/P4/P5/P6 y contrato rector en [REALINEACION_FONDO_AUTONOMO_2026_10_23](docs/REALINEACION_FONDO_AUTONOMO_2026_10_23.md). P4 debe poder recibir eventos autónomos en un **Goal futuro**; P5 debe ser determinista y no depender del éxito del debate LLM; P2 necesita readiness point-in-time; P6 requerirá OMS e InternalPaperBroker antes de brokers externos. **Nada de esto se ha implementado en este Goal.**

**Estado real heredado:** HUD compacto ya completado y probado (entrada 2026-10-22); P4 sigue PARTIAL, Bull TIMEOUT/Bear/Chair BLOCKED, y P5/P6 NO INICIADOS. **No se han ejecutado pruebas locales ni inferencias LLM en esta actualización documental.** No se han cambiado Python, TypeScript, SQL, dependencias, datos de mercado ni credenciales.

**Invariantes:** MASTER 10.000 EUR ficticios, PAPER ONLY, `orders_enabled=false`, `live_trading_enabled=false`, `POST /api/orders=403` **sin modificar**. Sin gastos, sin brokers ni órdenes. Siguiente paso: revisar/autorizar **un Goal acotado P4** para evento programado, routing, idempotencia y ejecución sin UI; después readiness P2. **STOP antes de P5/P6 hasta autorización expresa.**

---

## 2026-10-22 · Goal acotado HUD compacto — completado

Compactación limitada a los dos paneles laterales. Vista Compacta por defecto en escritorio desde1280px, Normal en menor tamaño; selector accesible que afecta ambos rails y conserva la preferencia. Base/símbolos13px, precios14px, encabezados16px, patrimonio24px; filas9px verticales e interior12×14px. Ancho306px, Normal conserva340px a1920 y300px a1366. Sin cambios de tipografía en departamentos, escena ni runtime.

**Navegador real:** seis filas disponibles (feeds/referencias reales). A1920×1080 pasan3→6 filas completas (+100%); a1366×768,2→3 (+50%). Sparklines, unidades, estados y procedencia conservados. Seis detalles contrastados con API, cuatro pestañas y teclado correctos; controles inferiores descubiertos, sin overflow/erroresJS. Alternancia/persistencia verificadas. Comprobación adicional390×844 correcta. Capturas antes/después de ambos rails y vista completa en `output/playwright/hud-density/`; se mantienen locales por licencia de datos. [Evidencia y medidas](docs/evidencias/HUD_COMPACTO_20261022/README.md).

**Pruebas:** `manage.py check` exit0:212pytest,54Vitest+1opt-in omitido, TypeScript/build. `git diff --check` correcto. MASTER10000EUR/hash intacto, orders_enabled=false, POST/api/orders403;30roles,0jobs/cola, runtimeNO_LOCAL_MODEL. Sin inferencias, nuevas dependencias ni conexiones a brokers. Coste0EUR. No se repite el debate fallido ni se afirma mejorar FPS.

**Preparación técnica:** propuesta breve añadida a `docs/P4_PROFUNDIDAD_Y_CIERRE.md` para profundidad por run/idempotencia, selección ordinaria/profunda, contrato compacto, presupuesto y gates. No implementada. `docs/Plan_JAIME_P5_P6.md` permanece como requisito futuro. **P4 continúa PARTIAL; P5/P6 no iniciados.** Este Goal visual termina sin abrir otra fase.

---

## 2026-10-22 · Cierre solicitado P2 + P4 — PARTIAL

**P4 no está listo.** Se cierra la ejecución acotada solicitada por el usuario, conservando fallos y sin nuevas inferencias largas. P5/P6 no iniciados. Informe verificable: [cierre y diagnóstico](docs/evidencias/P4/cierre-20261022/README.md). Las entradas anteriores son históricas, no el estado actual.

**Implementado/verificado:** persistencia/refresco P2 con derechos, histórico personal autorizado y TTL corregido; datos reales en watchlist; objetivos de research diferenciados, contexto compacto, abstención por mandato, grounding/citas y salida cualitativa separada de cifras Python; HUD sans serif y paneles legibles. Schema `0005_data_history`; 30 roles lógicos, una inferencia máxima. Fuente/cadencia no se presenta como cotización en tiempo real. Catálogo31proveedores/36modalidades/34adaptadores; conteos de conexiones fechados en informe, no inflados por mocks.

**Pruebas finales:** `manage.py check` exit0: **212 pytest, 54 Vitest +1 opt-in omitido, TypeScript/build**, 97,24s. `manage.py audit` exit0: cero vulnerabilidades conocidas. Alembic0005head, sin drift. Restart real conserva9jobs/estados/intentos/errores y hashMASTER. UI real4/4 departamentos Research/Quant/Comité/Sistemas por clic NPC, sin JSerrors/overflow; 6sparklines reales, texto16px, dossier INCOMPLETE visible y videowall con estados auténticos. Nueve NPC y offline/responsive se verificaron en el checkpoint anterior. Capturas privadas `output/playwright/p4/history-*.png`; hashes públicos, sin redistribuir precios de CoinPaprika.

**Fallo E2E:** p4.11 terminó INCOMPLETE:6jobs Python SUCCEEDED, Bull TIMEOUT tras2intentos y Bear/Chair BLOCKED. El p4.10 había rechazado UNGROUNDED_NUMBER. No se ha certificado ningún debate suficiente nuevo; la abstención con evidencia insuficiente sí está probada. No se convierte JSON válido en aceptación financiera.

**Diagnóstico acotado:** una petición sintética por modelo existente, máximo128tokens/120s, sin nuevos modelos. Qwen3Q8:590entrada/42salida, contexto32,50s, TTFT33,98s, generación6,27tok/s, total40,51s. Qwen2.5Q4:586/28, contexto6,03s, TTFT6,20s, generación18,73tok/s, total7,49s. Ambos JSON válidos solo para diagnóstico. No es A/B causal: Qwen3 estaba en batería y RAM mínima68,55MiB; Qwen2.5 en red y mínimo2,15GiB. CPU proceso~19–21%del total12lógicos (3threads), lecturas page-in globales medias1226/s→131/s. Presión/paginación reales, no toda atribuible al modelo. RSS pico1,79/1,75GiB; memoria privada1,33/0,89GiB. Carga Qwen2.5health7,46s incluyendohash, no cold-cache garantizada. Los runs largos previos bajaban de2tok/s en tramos y agotaron300s; se conservan.

**Oficina:** medición21-10 con red/avatar/LLM:31,68–37,71FPS, cuatro ventanas válidas, Equilibrado1920×1080/DPR0,70–0,72. No alcanza40–45; no se afirma mejoraFPS con Qwen2.5. Runtime descargado de RAM al terminar las dos pruebas; API muestra NO_LOCAL_MODEL, cola0/activos0, backend/preview siguen disponibles.

**Pendiente:** debate semántico suficiente, rendimiento gráfico bajo carga, calendarios/publicaciones completos y cobertura point-in-time/corporate actions para futuros usos. Estudio de profundidad adaptativa y registro del plan futuro en [P4_PROFUNDIDAD_Y_CIERRE](docs/P4_PROFUNDIDAD_Y_CIERRE.md); la modalidad descriptiva compacta nueva es propuesta, no implementación. Plan_JAIME_P5_P6 se conserva como requisito futuro, sin activar laboratorio, órdenes ni integraciones.

**Seguridad:** MASTER10.000EUR ficticios, cero posiciones; hash `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836` intacto. PAPER_ONLY, orders_enabled=false, POST/api/orders403. Coste0EUR. Próximo paso: **esperar instrucciones del usuario**, sin repetir inferencias ni empezar otra fase. Commits/push se verifican al terminar este cierre.

---

## 2026-10-21 · Continuación P2/P4 · NO SUCCESS

Trabajo local preservado. Commit de seguridad **955fd38** actualiza únicamente certifi por GHSA-6q48-6c7w-9gw2; audit repetido exit0, sin vulnerabilidades conocidas Python/npm. Regresión completa anterior: **209 pytest, 54 Vitest +1 opt-in omitido, TypeScript/build exit0**. Después: 50 tests research por contexto compacto, 76 datos/refresh/derechos, y el test adicional de reducción de TTL correctos. `git diff --check` sin errores. No confundir estas pruebas con aceptación semántica.

**Datos:** A21 verificado de nuevo por HTTP200 el 21-10 a las 10:02:26 UTC, 1290 ms, 90 observaciones y última fecha 20-10. Revalidación horaria de histórico diario (no hora de publicación certificada), fechas UTC, feed agregado separado del spot. Un cache hit no prolonga el TTL y reducir el TTL vigente invalida una caché antigua más larga. Archivo local y MASTER sin cambios financieros. Catálogo36/31proveedores/34adaptadores. Metadatos de prueba en `output/p4-data-refresh/history-refresh-20261021.json`; datos personales fuera de Git.

**Research:** caso `de7188a7-de42-4318-b5ae-e77b5c86dc76`. p4.8 rechazado semánticamente: el LLM afirmó incrementos diarios, pese a 22 intervalos positivos y20 negativos; cancelación HTTP200 conservando resultados. p4.9 añade abstención determinista de microestructura/liquidez/macro cuando no existe evidencia del mandato, selecciona historia sin que la desplacen noticias/spot y calcula trayectoria completa. Bull agotó ambos intentos de300s; Bear/Chair BLOCKED. No hay debate aceptado en esa versión.

**Prueba actual:** p4.10 compacta metadatos repetidos mediante diccionario de fuentes, manteniendo IDs, unidades, scope, fechas y extractos exactos; el manifiesto completo se conserva. Qwen3-1.7B Q8_0 existente, llama.cpp b11696, ctx4096, thinking256, repackCPU, threads3 y una inferencia. Run `history-source-p410-run` terminó rechazado: Bull `UNGROUNDED_NUMBER` en ambos intentos; Bear/Chair bloqueados. Archivo privado `research-history-p410.json`. No se ha descargado otro modelo. El gate semántico sigue pendiente. La prueba p4.11 separa narrativa cualitativa de cifras exactas presentadas por Python, acota citas a evidencia usable y conserva los validadores. Run `history-qualitative-p411-run` en curso; primer intento Bull TIMEOUT, segundo en curso. 51 tests focalizados correctos.

**FPS reales durante p4.10:** cuatro ventanas válidas con flechas, Chrome1920×1080, Intel/D3D11 y Equilibrado adaptativo. MovingFPS: Recepción35,99; Trading34,38; Comité30,45; Sistemas35,91. DPR0,70–0,72. No alcanza40–45. En esta muestra del21-10 Windows indica batería43%, ACLineStatus0, sin ahorro; no es comparable con cargador. RAM libre1,61GiB, working set modelo2.384.920.576bytes durante captura. Evidencia `fps-p410.txt` y `hardware-p410.json`; no inventar un benchmark en corriente. Captura privada `output/playwright/p4/advanced-moving-office.png`.

**Cargador reconfirmado el 21-10:** Win32 ACLineStatus1, BatteryFlag8 (cargando), 41%, sin ahorro; RAM libre2,19GiB. Repetición real con avatar/LLM activo: Recepción31,68; Trading33,73; Comité34,19; Sistemas37,71 FPS, cuatro ventanas válidas, DPR0,70–0,72. Sigue por debajo40–45; no se atribuye la diferencia exclusivamente a alimentación. Metadatos públicos `docs/evidencias/P4/datos-20261021/fps-ac-llm.json`; bruto y captura privados.

**UI real:** nueve NPC/paneles ya comprobados en checkpoint anterior; repetición actual Research/Quant/Comité/Sistemas4/4 mediante clic NPC, caso BTC visible, pausa movimiento correcta, sin errores JS/overflow, seis sparklines reales y tipografía sans serif16px. Videowall muestra estados backend y errores reales. HTTPórdenes403 y hashMASTER conservado.

Siguiente paso exacto: terminar/revisar el run p4.11 ya activo, registrar límites y cerrar commits/push sin declarar P4 terminada si falla semántica. Backend/preview/modelo locales activos; consultar puertos8000/5174/8089 antes de reiniciar. Sin P5/P6, 0EUR, PAPER ONLY.

---

## 2026-10-20 · Reanudación exacta · histórico conectado, caso generativo en marcha

Checkpoint `e24a6b2` publicado en origin/main. Cambios locales anteriores de HUD/runtime conservados. Catálogo ampliado a 36 modalidades / 31 proveedores / 34 adaptadores con **A21 CoinPaprika histórico diario**: HTTP real, 90 observaciones; API de watchlist muestra 60 puntos comparables. A15 spot separado. Permiso explícito de IA personal local, sin redistribución ni valoración MASTER; datos y capturas con valores personales permanecen en `output/`. MASTER conserva su hash. 74 pruebas focalizadas de datos correctas antes del último ajuste de selección de evidencia y tests de contrato frontend; regresión completa actual todavía pendiente.

Los tres experimentos TEST_ONLY de premisa no certifican semántica: Qwen2.5 acertó etiquetas pero contradijo hechos; Qwen3 con reasoning confundió una etiqueta y, al explicar primero, volvió a fallar una etiqueta. No se ha instalado otro modelo. Resultados locales `premise-qwen25.json`, `premise-qwen3-thinking.json`, `premise-qwen3-explain-first.json`; no cuentan como research real.

Runtime actual Qwen3-1.7B Q8_0, ctx4096, reasoning256, no-repack, 3 threads, una inferencia. Caso HTTP real `de7188a7-de42-4318-b5ae-e77b5c86dc76`, pregunta acotada al histórico BTC y sus límites. Sigue EN CURSO, **no aceptado**; `output/p4-data-refresh/research-history-real.json` conserva dossier privado y estados. El primer rol generativo terminó en 168469 ms, 4,94 tokens/s de generación; TTFT no medido. No confundir ejecución correcta con calidad semántica.

Cargador vuelto a confirmar por Win32 `ACLineStatus=1`, batería28 %, ahorro desactivado; con el LLM activo quedan 0,68 GiB libres. No ejecutar builds junto al benchmark. El backend activo todavía usa la selección anterior de evidencia; el cambio en disco evita que macro/noticias desplacen el histórico y requiere reinicio cuando los jobs terminen. Siguiente paso: revisar el caso en curso, corregir problemas reales, verificar UI y gate final; no repetir investigación del repositorio. PAPER ONLY, 0 EUR, P5/P6 no iniciados.

---

## 2026-10-20 · Continuación P2 + P4 · histórico y refresco EN CURSO

Continuado desde `5fd14e2`, conservando todos los cambios locales del HUD, evidencia y runtime. Objetivo vigente: fuente real → actualización/persistencia → caso → LLM → Bull/Bear/Chair → dossier. **No declarar SUCCESS: aceptación semántica y E2E generativo siguen pendientes.** Sin nuevos modelos ni P5/P6.

**Checkpoint de datos:** migración `0005_data_history` aplicada con backup SQLite `output/p4-data-refresh/before-0005-20261020-072922.db`, Alembic sin drift. Archivo de observaciones separado de la caché, revisiones conservadas y lectura condicionada a derechos/configuración actuales. Refresco secuencial con plazos persistentes, lease, backoff y cuotas; 30 s tras arrancar, comprobación de vencimientos cada 60 s, consultas según TTL (mínimo 300 s). Sin brókeres ni fuentes restringidas. `GET /api/data/refresh` informa estado real; PC/backend apagado implica ausencia de actualizaciones. Fechas móviles en presets existentes OCDE/BIS/Treasury/FMI/ESMA/BEA/BLS v2. No se confunde cadencia de consulta con calendario de publicación. Una cotización spot antigua sigue STALE aunque se vuelva a descargar.

**Prueba real de datos:** pasada por las 35 modalidades, con 2 brókeres excluidos. 17 conexiones verificadas en la pasada, de ellas 16 peticiones HTTP nuevas y una caché verificada; 12 respuestas utilizables para su uso P2 autorizado (no equivalen a 12 fuentes aptas para IA o valoración). 11 sin credenciales, una configuración SEC pendiente, 2 planes/endpoints pendientes, 5 restricciones, CoinPaprika STALE y GDELT TIMEOUT. Los contadores históricos de Data Quality (18 conexiones) incluyen verificaciones anteriores y no certifican disponibilidad actual. Archivo inicial: 730 observaciones. Reiniciar el planificador conserva vencimientos y no repite consultas. MASTER conserva hash `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`.

**Corrección Eurostat verificada aparte:** el preset antiguo `prc_hicp_midx` estaba archivado (terminaba en 2025). Se usa `prc_hicp_minr`, ECOICOP2/TOTAL/I25; HTTP real devuelve julio–septiembre de 2026. Feed/unidad separados de la base anterior. Coinbase queda bloqueado en HQ: condiciones Market Data 2026-08-07 §3(5), verificadas el 20-10, prohíben operación/benchmark de IA sin consentimiento escrito. No se relajan derechos para aumentar cifras.

**Pruebas:** 78 focalizadas iniciales correctas. Primera regresión completa: 199 correctas y 2 fallos (lista de rutas y degradación de evidencia incompleta). Corregidos ambos; repetición de las 58 afectadas correcta. La nueva restricción Coinbase requirió aislar explícitamente los derechos ficticios del fixture de cartera; 9 pruebas afectadas correctas. Gate final `manage.py check` **exit 0: 202 pytest, 52 Vitest + 1 opt-in omitido, TypeScript/build**. Logs negativos conservados. Evidencias actuales en `output/p4-data-refresh/` y `docs/evidencias/P4/datos-20261020/`.

**Checkpoint anterior ya verificado:** 194 pytest, 52 Vitest + 1 opt-in omitido, build y audit exit 0; 9/9 clics NPC, UI responsive y offline sin overflow ni errores. Los FPS de la noche anterior no dan aceptación: con carga concurrente 39,71–41,10; pasada posterior sin LLM 11,04–25,59 con dos ventanas inválidas. No atribuir la diferencia al LLM ni al HUD: condiciones no controladas. Hoy cargador confirmado, ahorro desactivado, 2,45 GiB libres / 15,69 GiB; falta repetir benchmark prudente y FPS.

**Siguiente paso exacto:** publicar checkpoint pequeño de datos y preservar el HUD anterior. Corregir inferencia con una hipótesis nueva (contrato compacto y abstención explícita cuando la premisa contradice evidencia), probar primero Qwen2.5 existente, luego caso real suficiente/insuficiente desde API/UI. Investigación nueva: documentación oficial CoinPaprika confirma IA personal gratuita e histórico diario; falta separar permiso local de redistribución e implementar/verificar ese histórico antes de usarlo. Ningún candidato tiene aún aceptación semántica. No repetir benchmarks fallidos sin cambiar hipótesis. PAPER ONLY, 0 EUR, órdenes bloqueadas, sin mutación financiera.

---

## 2026-10-19 · P4 avanzado EN CURSO · checkpoint de contratos y HUD

Trabajo anterior preservado; documentación sincronizada por fast-forward hasta **137f9db**. Backup local consistente: `output/p4-advanced/before.db`. Sin migración nueva (0004_research), sin cambios financieros ni P5/P6.

Implementados objetivos `data_quality` / `macro_reference` / `investable_thesis`, EvidencePack tipado con alias estables, contratos separados Bull/Bear/Chair y referencias cruzadas, guardas contra duplicados y cifras sin respaldo. Los informes de referencia usan cuatro jobs deterministas; una tesis sin evidencia comparable se abstiene sin llamar al LLM. Ejecución técnica y calidad se muestran por separado. Validación léxica/estructural NO certifica razonamiento financiero.

HUD negro, rails 340 px adaptables, tarjetas de argumentos y sparklines SVG solo con >=3 observaciones reales del mismo feed/venue/unidad/divisa/frecuencia; sin historia se muestra ausencia. Build TypeScript correcto y **52 tests frontend**; último gate backend anterior a ampliar las pruebas de objetivos: **46 tests focalizados** correctos. Pruebas ampliadas en ejecución; no contar como pasadas todavía.

Benchmark auténtico TEST_ONLY aislado: Qwen3-1.7B Q8_0 produjo tesis repetidas y una inferencia favorable no sustentada por plazos de cobro crecientes; Chair agotó timeout. **No aceptado semánticamente**. Salidas originales conservadas en `output/p4-advanced/debate-qwen3.json`; el guard nuevo rechaza tesis repetidas que la primera validación estructural dejó pasar. Qwen2.5-1.5B Q4_K_M en evaluación con el mismo fixture y contratos. No se han insertado hechos ficticios en P2/P3. TTFT no medido en estas llamadas no streaming; no confundir duración total con tokens/s de generación.

Siguiente paso exacto: terminar comparación de los dos candidatos; cerrar pruebas de objetivos/abstención, revisar integraciones read-only, reiniciar backend con nuevo código y demostrar BCE informativo/abstención reales, QA visual responsive y FPS, pruebas completas, evidencias y publicación normal. **P4 avanzado no terminado ni publicado todavía.** Mantener PAPER ONLY / 0 EUR / STOP antes de P5.

---

## 2026-10-19 · P4 pendiente de aceptación semántica · STOP antes de P5

Continuación de P4, sin reconstruir P1–P3. Esquema **0004_research**, 30 roles lógicos, scheduler persistente 1 LLM/2 quant/4 fetch. Commits anteriores conservados: 6c17a31, 34baca4, 325c17b, 6c8153c. Nuevos: **64049f7** (paneles simplificados/clic NPC) y **65d976d** (contexto independiente Bull/Bear y rechazo de tesis duplicada).

**Petición visual implementada:** listas negras, sans serif local, texto principal a 16 px y notas a 14 px, panel izquierdo a 100 px bajo la marca. Los 16 NPC tienen clic; prueba nativa sobre los nueve principales: **9/9** paneles, pausa/cierre/control correctos. Fuentes y fechas desplegables; no se inventan minigráficos. Captura `docs/evidencias/P4/simple-sidebars.png`. Responsive sin overflow, diagnóstico P0 operativo. Capturas finales en contexto nuevo a 1920×1080 CSS y DPR de dispositivo 1, sin el zoom heredado. Frontend revalidado tras el último ajuste de letra.

**QA:** `manage.py check` exit 0: **182 pytest + 49 Vitest**, TypeScript/build; `audit` exit 0, cero vulnerabilidades conocidas. Alembic check sin diferencias. Backup SQLite y dos reaperturas/recovery preservan jobs, resultados y MASTER. Runtime detenido realmente: `NO_LOCAL_MODEL` verificado, sin fallback. MASTER mantiene hash `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`, 10000.00 EUR ficticios y cero posiciones. HTTP /api/orders=403 verificado previamente; cierre HTTP final pendiente.

**FPS tras cambio visual:** Intel Graphics/D3D11, Equilibrado adaptativo, movimiento nativo y LLM activo: Recepción **58,09**, Trading **58,68**, Comité **58,32**, Sistemas **59,44**; p95 18,6–21,7 ms, DPR 0,81–0,84. Viewport de captura 1920×1080; canvas CSS reportó 2133×1200 por zoom del navegador. Frente a muestra previa 59,59–59,91: ligera caída; no es A/B controlado. Un intento de Sistemas interrumpido por proximidad se excluyó; repetición válida archivada. No se ejecutaron builds/tests durante las muestras.

**No declarar P4 terminada:** Qwen3-1.7B Q8_0 pasa JSON/grounding del fixture, pero sus argumentos reales son repetitivos y confunden ocasionalmente tipo de referencia con spread. Run p4.5 `3653e0d1-5901-4fb5-b2e1-cd2564b4658b` terminó mecánicamente, sin aceptación semántica. Run p4.6 `3f573ece-9f82-459b-b5a7-413c324416b4` terminó INCOMPLETE: Bear rechazado y Chair bloqueado. Historial conservado. No basta con nueve estados SUCCEEDED.

**Bloqueo confirmado en ambos candidatos:** run Qwen2.5 **08dec597-8a6b-4a6a-9426-ad5dd3e29545**, caso BCE **ccadc542-5ddf-415f-8692-676415729886**, terminó INCOMPLETE: siete jobs SUCCEEDED, Bear FAILED (`DEBATE_DUPLICATE_THESIS`, dos intentos), Chair BLOCKED (`DEPENDENCY_INCOMPLETE`). El modelo también confundió el identificador de serie con una plataforma. No se acepta el debate ni se declara P4 completa. No descargar un tercer candidato sin revisar el límite de dos modelos del encargo. El runtime de prueba se ha detenido para liberar RAM; API/UI reflejan NO_LOCAL_MODEL. Los dos GGUF y sus hashes permanecen locales; el manifest identifica Qwen3 como candidato probado, no modelo aprobado semánticamente.

**Cierre de esta iteración:** regresión HTTP final: 30 roles, 98 instrumentos, MASTER intacto y /api/orders=403. Backup/reopen repetido con todos los jobs terminales. Capturas y evidencia real en [P4](docs/evidencias/P4/README.md). Próximo trabajo exacto: resolver la calidad semántica del runtime dentro de los límites autorizados; no rehacer interfaz, scheduler, fuentes ni pruebas ya válidas. P4 sigue bloqueada por calidad, P5/P6 no iniciados. PAPER ONLY, coste 0 EUR. Publicación normal de los commits de esta iteración y comprobación HEAD=origin/main al cerrar.

---

## 2026-10-16 · Cierre P3 · STOP antes de P4

P3 autorizado por el prompt maestro y Astra confirmado por el usuario. Entorno real **Windows local**, no Cloud. Trabajo P1/P2 preservado; sincronización inicial fast-forward de 460c7e0 a 901f6f0 sin reset/clean/force. Implementación: **c8b8ab2** (ledger/API), **cf00a19** (FX devengado/semántica de feeds), **4725693** (HUD/videowall DOM). La evidencia y este cierre se guardan en el commit posterior; publicación normal de main y verificación HEAD=origin/main al finalizar.

**MASTER:** migración **0003_portfolio aplicada**, NAV y efectivo **10000.00 EUR ficticios**, **0 posiciones**, **1 depósito**. Ledger append-only con triggers, hash chain, Decimal, doble entrada por divisa y reconstrucción FIFO. Hash verificado `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`. Seed único/idempotente; snapshots auditables. Dos inicializaciones y dos arranques reales del backup restaurado conservan estado y hash; integridad SQLite correcta, 98 instrumentos P2 preservados. Backup local separado, no publicado.

**API/UI:** GET summary, positions, ledger, nav/history, performance bajo /api/portfolio/master; /api/markets/watchlist y /api/hq/overview. HUD izquierdo watchlist/Market Pulse y derecho Cartera/Posiciones/Actividad/Mapa, navegación accesible y formato Decimal. Recepción, Trading y Performance conectados al ledger. Nueve módulos físicos del videowall con texto DOM nítido independiente de DPR; rails ocultos en inspección para no taparlo. Nueve departamentos, 16 NPC, cámara, controles y distribución P1 conservados.

**Pruebas finales:** `python scripts/manage.py check` exit 0: **144 pytest + 45 Vitest**, TypeScript/build. `audit` exit 0: **0 vulnerabilidades conocidas**. HTTP real GET 200 y **POST /api/orders 403**. Backup/restauración/reinicio, idempotencia, integridad, cuotas/derechos P2 y contratos financieros probados. Recorrido nativo **9/9 departamentos y paneles**, histéresis/control; repetición final de los tres paneles financieros. Offline simulado en navegador sin cifras antiguas y con movimiento; /?diagnostico=1; interfaz 390 px sin overflow horizontal. Evidencias y capturas auténticas en [P3](docs/evidencias/P3/README.md).

**FPS reales móviles:** Intel Graphics/D3D11, Chrome 1920×1080, Equilibrado adaptativo: Recepción **60,00**, Trading **59,99**, Comité **59,99**, Sistemas **59,97**; p95 17,7–17,8 ms, DPR 0,81/0,82/0,83/0,84. Peor ventana de cinco segundos **59,79 FPS**. CDP focus emulation evita la limitación del target ocluido (~1 FPS en intento inicial); sin tareas de build/tests simultáneas. No es A/B controlado ni garantía bajo otras cargas. Captura final repetida tras encontrar un target de navegador cerrado; no es fallo financiero de la aplicación.

**Límites:** cero cotizaciones redistribuibles disponibles en watchlist; referencias P2 reales separadas de precios ejecutables. 18 conexiones históricas P2/17 proveedores no equivalen a disponibilidad actual; la frescura se calcula en cada lectura, sin consultas externas nuevas durante P3. No se promueven capacidades research-only a valoración. Retorno inicial 0; ratios con historia insuficiente NO DISPONIBLE. Persisten avisos TestClient/httpx, THREE.Clock, Intel/ANGLE y chunk 3D >500 kB. Pendiente revisión visual del usuario y sesión prolongada en su carga habitual. [Arquitectura y operación](docs/P3_IMPLEMENTACION_Y_VALIDACION.md).

**Seguridad:** PAPER ONLY, orders_enabled=false, ninguna orden a bróker, secretos protegidos, coste adicional **0 EUR**, sin nuevos assets/licencias. **P4/P5/P6 no iniciados.** Siguiente paso exclusivamente revisión de la entrega; no arrancar P4 sin nuevo encargo.

---


## 2026-10-15 · Cierre visual y regresión P1/P2 · STOP antes de P3

La última imagen marcada y las correcciones de esta conversación sustituyen los fondos y planos históricos incompatibles. **Nueve departamentos, 16 NPC sentados y nueve paneles** conservados. **Ejecución está debajo de Sistemas, a la izquierda**. Todos los despachos se adelantan **4,3 m**, dejando **2,7 m de vestíbulo**. Laterales exteriores sólidos, crema más oscuro `#a7987e`, negro y suelo azul negro; accesos interiores abiertos y vidrios decorativos interiores atravesables. Fondo **negro puro**, sin ciudad ni fachada inferior. El antiguo panorama queda archivado fuera del build/runtime.

Videowall **33×7,8 m** (+67,6 % de superficie), nueve módulos **1024×1536**, tipografía ampliada, marcos finos y vista de inspección propia. Corregida la superposición de profundidad de los módulos. Mobiliario, iluminación, apliques, materiales, señalética en pared, distribución de puestos y cámara frontal isométrica pulidos. Flechas screen-relative, velocidad 2,05 m/s y seguimiento fijo. Detalle en [informe](docs/PULIDO_REFERENCIA_Y_DPR.md) y [capturas/pruebas reales](docs/evidencias/P1_PULIDO_ADAPTATIVO/README.md).

**DPR y FPS reales:** Equilibrado automático arranca en 0,80, límites 0,70–1,00, bajadas de 0,02 y recuperación de 0,01 con margen sostenido. Comparación fijo–adaptativo–fijo en Chrome con ventana, Intel/D3D11, 1920×1080 y movimiento nativo: adaptativo **Recepción 58,37 / Trading 57,70 / Comité 60,00 / Sistemas 59,83 FPS**, DPR final por zona **0,99/1,00/1,00/1,00**. Peor ventana móvil de cinco segundos **54,56 FPS**, p95 **17,2–21,7 ms**. Fijo 0,80 antes **56,13–59,84** y después **56,16–59,82 FPS**. Veinte subidas reales de 0,01; texto DOM idéntico (38 px / 320×46) al comparar DPR 1,00 y 0,80. Una muestra de Sistemas interrumpida por proximidad se excluyó y repitió; quedan 12 ventanas completas. Se conservaron las siete previas completas, con corrección nativa de deriva en la recuperación. No se requirió descenso real a 0,70; ese límite está probado con relojes sintéticos, sin contarlo como FPS del equipo. Objetivo 40–45 superado en medias y ventanas de esta muestra, sin garantía de cada fotograma bajo otras cargas. Detalle no certificado.

**Pruebas:** 115 pytest, 40 Vitest, TypeScript y build correctos; auditoría Python/npm **0 vulnerabilidades conocidas**. Recorrido con flechas por **9/9 departamentos**, apertura de **9/9 paneles** por proximidad, histéresis, pausa/foco y devolución del control; 16 NPC sentados y nueve teletransportes libres comprobados. WASD/ratón/rueda ignorados en juego. Backend inaccesible desde navegador: estado NO DISPONIBLE y movimiento conservado. `/?diagnostico=1` operativo. Capturas de Recepción, planta, Trading, Comité, videowall y nueve paneles.

**P2 conservada:** sin cambios de código backend. HTTP local real: salud/esquema `0002_data`, **98 instrumentos**, nueve secciones HQ y Data Quality correctos; **POST /api/orders = 403**. Lectura 15:01 UTC: 31 proveedores/35 modalidades candidatas, 33 adaptadores, 18 conexiones reales/17 proveedores, 11 fuentes utilizables/11 proveedores, 13 NO_CREDENTIALS y cuatro RIGHTS_RESTRICTED. Frescura variable; estas lecturas no añaden conexiones ni refrescan automáticamente proveedores.

**Preservación/Git:** respaldo previo de 72 archivos/47.279.936 bytes en `output/pre-compactado-20261015.zip`; 17 commits locales anteriores preservados, origin/main comprobado sin nuevos cambios (3415ddf). Sin reset/clean/force. Código de este pulido confirmado en **5d05209** y limpieza PCF/QA en **52ea0b4**; evidencia y documentación se guardan en el commit de cierre. Publicación mediante push normal de main, preservando también los commits locales anteriores.

**Limitaciones:** avisos de deprecación TestClient/httpx, THREE.Clock creado por R3F, redondeo X4122 del compilador Intel/ANGLE y chunk 3D >500 kB; **cero errores de consola**. Sustituido el alias retirado PCFSoftShadowMap por PCFShadowMap; Three 0.186.1 ya convertía el primero al mismo PCF durante las mediciones, por lo que el modo renderizado se conserva. Smoke del build final: **59,74 FPS móviles**, p95 17,8 ms, DPR 0,81. El acabado sigue siendo una escena interactiva optimizada, no se declara equivalencia fotográfica exacta con la referencia. Coste adicional **0 EUR**, PAPER ONLY y secretos protegidos. **P3/P4/P5/P6 no iniciadas.** Siguiente paso: revisión de esta entrega y preparación de P3 solo con su alcance autorizado.

---

## 2026-10-15 · Entrega local Sims P1.S0–S4 + P2.0–P2.6 · STOP antes de P3

La especificación definitiva, la imagen original aprobada y el issue #3 sustituyen perspectivas, controles y recuentos históricos. Se ejecutó el alcance P1 Sims y P2 viable gratuito. **P3/P4/P5/P6/P7 no iniciadas.** Los apartados siguientes son historial, no instrucciones vigentes. [Informe de entrega](docs/ENTREGA_SIMS_P1_P2.md), [capturas y FPS](docs/evidencias/P1_SIMS/README.md), [evidencias P2](docs/evidencias/P2/README.md).

**S0 comprobado:** working tree limpio en 71948e8; cinco commits locales anteriores conservados. Merge documental dc00029 desde origin/main ac3f68d; conflicto único de cámara resuelto conservando el texto anterior en `docs/HISTORICO_CAMARA_PRE_SIMS.md`. Baseline real, tras reducir carga adicional: Trading **31,29 FPS móviles**, p95 92,7 ms, Intel/D3D11, 1920×1080/DPR 1; evidencia `docs/evidencias/P1_SIMS/baseline-pre-sims.*`. Commit S0 **9f789f7**. Sin reset/clean/force/push ni pérdida de archivos.

**Preservación/documentación:** además del merge S0, incorporado origin/main **3415ddf** mediante merge **56c3b6f**, con backup previo de 48 archivos/5.209.550 bytes y hashes en `output/sims-before-definitive-docs.zip`. Sin pérdida de mejoras locales ni reset/clean/force/push. El usuario indicó `Downloads/assets`; encontrados ambos PNG originales ya extraídos, importados y verificados con el script, commit **a3547bc**. Principal SHA-256 `4e07c5f1ea91b598ce8e3fcbcc1e73da6332b64006f8c03a21df7fa7a515ef92`; secundaria `69101f7a18a0d48908b3e3a060e64ffeb1c89a2a975ccb085ac9bdf6dfd83347`. No se afirma que exista el ZIP original en la raíz ni que las referencias sean capturas.

**S1–S3:** transformación incremental de la oficina, mismos nueve IDs/builders/huella 34×28. Trading noreste, Quant este, Ejecución centro; Recepción sin sofás, operador detrás del mostrador; Performance accesible y Sistemas con dos puestos/tres racks. Marfil/roble/azul noche, ventanas, skyline conceptual, luces/sombras y materiales locales. Cámara fija elevada (offset 2,5/19/20; FOV 40), seguimiento amortiguado; flechas screen-relative y avatar orientado al desplazamiento, sin WASD/ratón/OrbitControls. Muros bajos físicos y paños superiores cutaway. **16 NPC sentados, 17 rigs**, nueve principales/siete secundarios, animaciones de teclear/leer/escribir ambientales y OFFLINE P4. **9/9 paneles** comprobados en recorrido continuo con flechas, sin teleport ni escrituras de pose; proximidad por sala/LOS, pausa, histéresis y control al cerrar. Videowall físico **32×4,8 m, nueve módulos** y diálogo accesible. Futuras funciones financieras NO DISPONIBLES, sin cifras de ejemplo.

**S4 / rendimiento final real:** Intel Graphics/D3D11, Chrome 1920×1080, Equilibrado **DPR 0,8**, buffer 1536×864, MSAA/sombra 1024, 16 NPC y videowall. Ventanas de 12 s con entrada nativa. Medias móviles: Recepción **36,38**, Trading **46,60**, Comité **41,69**, Sistemas **46,13**, pasillo **40,76**, recorrido/panel **40,93 FPS**. Peor ventana móvil de cinco segundos entre esos escenarios **32,73 FPS**. p95 37,6–62,2 ms; hay tirones y **45–60 no se alcanza en todas las zonas**. Sin tests/build/smokes simultáneos durante FPS. Se conservan negativos: última Recepción DPR 0,85 media31,74/ventana5s28,79; por eso se redujo DPR sin retirar NPC/mobiliario/luces. No se garantiza 30 en cada frame ni bajo otras cargas. Detalle no certificado. Datos completos en `controles-fps-entrega80.json` y `controles-fps-combinado80.json`.

**P2.0–P2.4:** núcleo previo conservado y endurecido: HTTPS/allowlist/GET, excepciones POST read-only OpenFIGI/BLS v2, Decimal/UTC, JSON/CSV/SDMX/XML/XBRL/RSS, cache/cuotas/circuit breaker, derechos/feed/venue y fallback compatible. DTD/entidades/UTF-16 con bytes nulos rechazados; identidad de cache compartida con HQ impide mostrar configuraciones/derechos anteriores. BCE FX corregido a USD/EUR, diez observaciones. Migración 0002_data y **98 instrumentos/series reales** preservados. Sin inventar ISIN/FIGI/divisa, cobertura de equities o elegibilidad paper.

**Cifras exactas, lectura local 2026-10-14 23:37:33 UTC:** **31 proveedores / 35 modalidades candidatas**, **33 adaptadores / 29 proveedores implementados**, **18 conexiones reales / 17 proveedores**, **12 fuentes frescas utilizables / 11 proveedores**, **13 NO_CREDENTIALS**, **4 RIGHTS_RESTRICTED**. Original34 + RSS BCE, no proveedor adicional. Verificados: BCE (FX+RSS), BdE, INE, Eurostat, OCDE, Banco Mundial, BIS, Treasury, BLS v1, FMI DataMapper, ESMA índice, Kraken, Binance data-only, CoinPaprika, CoinGecko, Coinbase y OpenFIGI. GDELT timeout en tres intentos acotados; SEC sin contacto; Finnhub/Nasdaq sin endpoint gratuito útil/derechos confirmados, no implementados. Cripto caducado no cuenta como utilizable; frescura variable, en una lectura intermedia había 11 hasta refrescar RSS. [Matriz](docs/P2_PROVIDERS_VERIFICACION.md).

**Terceros:** Agent Reach1.5.0 MIT fijado/auditado aislado, safe/dry-run/doctor solo RSS1/1 sin cookies/configuración personal; A20 noticias BCE HTTP200 real, cinco metadatos atribuidos/sanitizados y flag opt-in. Vibe0.1.16 MIT/NOTICE: **30 presets YAML verificados con hashes, METADATA_ONLY/desactivados**, contrato read-only y30roles declarativos, sin scheduler/jobs/modelos/backtest. Auditoría limpia solo del subconjunto instalado, no certificación del runtime completo Vibe. Pip vulnerable inicial corregido en venv aislado y evidencia negativa conservada. Liquid **BLOCKED_TRADE_SCOPE**, ningún OAuth/MCP/cuenta; API pública read-only no confirmada. [Auditoría y límites](docs/INTEGRACIONES_TERCEROS_VERIFICACION.md).

**P2.5–P2.6:** Data Quality montado en Sistemas tras la validación funcional/rendimiento Sims; 35 filas, cuatro filtros, pausa/reanudación, NO_CREDENTIALS sin consultas, unidades/derechos/cuotas/latencia originales y capturas reales. HQ consume cache local autorizada y metadatos; no consultas externas por frame. Markets/news con procedencia/frescura; cualquier mezcla caducada marca STALE. Cartera/posiciones/operaciones/riesgo/comité/agentes NO DISPONIBLES. Backend realmente detenido: ambos paneles NO DISPONIBLE, foco CANVAS y movimiento recuperado. Prueba adicional offline interceptada/Tab/Shift+Tab/Esc y diagnóstico P0 correcta.

**Pruebas finales:** `python scripts/manage.py check` **115 pytest +35 Vitest**, TypeScript/build y salida0; audit Python sin vulnerabilidades conocidas/npm0, salida0. Assets/FK/licencias/hashes correctos; 33 fuentes/6 mapas PBR/5 mapas humanos, ocho clips. Timeout de fixture3D5,35s sobre5s investigado, presupuesto limitado15s igual al otro test de geometría y cámara actualizada; repetición completa pasa. Logs/negativos conservados. GET health200/PAPER_ONLY/ordersfalse/schema0002 y POST local LIVE negativo **403** comprobados tras reiniciar únicamente el backend propio. Ninguna orden externa, cuenta creada, servicio pagado o clave expuesta; **coste servicios0 EUR**.

Limitaciones: luz/reflejos aproximados, skyline conceptual, una base humana reutilizada, tirones y objetivo45–60 parcial. Sin claves no hay conexión real B; sin permisos no hay display; ESMA solo índice, sin descarga masiva. Vibe operativo/P4 pendiente por seguridad y recursos; Liquid permanece bloqueado. No se ha iniciado ledger P3, agentes P4 ni ejecución P6. **Siguiente paso: revisión del usuario sobre capturas y entrega; no iniciar P3 automáticamente.** Commits finales registrados en el informe de entrega.

---

## 2026-10-14 · Correcciones P1 y P2 · gate F pendiente de rendimiento

Encargo vigente: `PLAN_EJECUCION_P1_P2`, issue #1 actualizado e issue #2. Sustituye WASD/ratón, E/clic, NPC de pie y STOP antes de P2; **STOP antes de P3**. P1 correctiva pendiente de F; P2 backend implementado parcialmente y sometido a verificación, sin integración visual todavía.

Preflight: `git status --short`, log de cinco commits, rama main y diff revisados. **205 archivos locales** preservados y hashes comprobados en `output/p1-p2-preflight-20261014.zip` (50.183.199 bytes). Snapshot local **57f5595** conserva íntegra la entrega anterior, incluidos fuentes/GLB/capturas/tests. Merge documental **ab830a5** incorpora `origin/main` **fb38420** sin conflictos, sin reset/clean/force/push. Working tree limpio tras sincronizar; centros/arquitectura locales conservados. Documentos obligatorios e issues revisados por apartados pertinentes.

Secuencia pendiente: baseline local nueva → B redistribución/puestos/vidrio → C flechas/cámara/marcha → D proximidad/histéresis → E diez NPC sentados → F QA real y FPS → P2.0–P2.6 por sublotes. No integrar datos en Sistemas hasta estabilizar P1. P2 distinguirá **34 modalidades / 31 proveedores** candidatos de implementados/conectados/utilizables; ningún mock cuenta como conexión. Coste 0 EUR, PAPER ONLY y órdenes 403 obligatorios.

Correcciones B–E implementadas: Recepción sin sofás; Trading con eje central libre; Performance con puesto accesible y aparador; Sistemas con tres racks separados del escritorio. Portales de 4,4 m, mamparas interiores a 2,45 m, sin hojas de cristal aparcadas en puertas. Se conservan materiales locales, nueve salas y arquitectura. Exactamente diez NPC sentados (uno por departamento y segundo en Trading), ocho clips originales y anchors de silla compartidos. Control exclusivo por flechas, giro suavizado, cámara automática elevada y apertura por proximidad al NPC principal con LOS, pausa e histéresis 2/2,8 m.

Pruebas ejecutadas: **47 pytest + 27 Vitest**, TypeScript/build correctos; FK sobre keyframes exportados verifica la trayectoria de apoyo de los pies y la pose sentada; nueve paneles comprobados en navegador mediante flechas reales, incluyendo 18 aperturas, foco, pausa, cierre, reentrada y WASD ignorado. Evidencias en `docs/evidencias/P1_CORRECTIVO/`. Estas pruebas usaron teletransportes entre departamentos: todavía falta el recorrido continuo sin teletransporte y la comprobación offline actualizada.

**Gate F pendiente por rendimiento:** baseline aislada de esta sesión: Trading 22,71, Recepción 20,49 y pasillo 24,66 FPS en movimiento. Tras correcciones y LOD: Trading 27,18, Recepción 29,79, pasillo 26,07, giro 26,37 y Comité 22,68. Intel/D3D11, 1920×1080, Equilibrado/DPR 1, cargador conectado y ahorro desactivado. No reutilizar los FPS históricos como aceptación actual. Ensayo FXAA: Trading 24,90; retirado por no aportar mejora. Perfil CPU real guardado. No se declara P1 correctiva completada ni se integra P2 visualmente.

P2 backend en desarrollo: catálogo de **34 modalidades / 31 proveedores**, matriz `docs/P2_PROVIDERS_VERIFICACION.md`, **32 adaptadores con presets útiles** (no clases vacías). Infraestructura común JSON/CSV/SDMX/XML/XBRL, Decimal/UTC, derechos, cache y cuotas SQLite, allowlist HTTPS/GET y únicamente dos POST de consulta acotados, límites de cuerpo, errores, circuit breaker. Migración `0002_data` conservadora con identidad por clase y aliases; no aplicada todavía a la DB de usuario. Health P0, diagnóstico y órdenes 403 preservados. API P2 separada; **sin integración visual todavía**.

Smokes reales separados de mocks en `docs/evidencias/P2/`: España/Europa, Banco Mundial, Treasury, BLS, BIS, cripto público, OpenFIGI y ESMA responden. FMI DataMapper investigado como alternativa pública a SDMX beta; estimaciones/proyecciones WEO etiquetadas, nunca señales. Las cifras definitivas se calcularán desde la última evidencia por modalidad; faltan cierre de derechos y revisión de datos/registro. Credenciales ausentes no detienen el lote. Finnhub/Nasdaq siguen candidatos con endpoint gratuito no confirmado, sin inflar adaptadores. Coste adicional 0 EUR, ninguna consulta de cuenta/orden externa.

Commits: **c9d11c0** P1 correctiva B–E; **2e80b45** núcleo/adaptadores P2; **188d1a2** visibilidad, batching y evidencias P1. Optimización adicional de batching estático mantiene geometría/materiales y reduce Trading de 141 a **37 draw calls** en el ensayo comparable; ese ensayo sigue en **19,65 FPS móviles** con tirones, por tanto F no está verde. WMI real: **750 MB disponibles, memoria comprometida 91 %, 60 páginas/s, CPU 1066 MHz** en una muestra puntual; no prueba causalidad exclusiva. Al cerrar las mediciones se ha cerrado mi navegador de QA; servicios locales conservados. Se ha solicitado reducir carga adicional para repetir sin cerrar aplicaciones del usuario ni modificar energía.

**Recorrido continuo real completado** desde Recepción por las nueve salas usando exclusivamente flechas, sin teletransportes ni cambios de posición desde scripts; nueve aperturas automáticas correctas, diez NPC sentados y once rigs independientes. `recorrido-continuo.json` y `final-{departamento}.png`. Observador del tramo final: más de 3.300 muestras sin penetración del avatar/cámara y altura 2,8–3,8 m; no se afirma cobertura de colisiones instrumentada en las nueve salas. Se ha corregido la cámara inicial que podía fijarse antes de disponer de colliders. Los intentos interrumpidos de automatización se conservan aparte y no cuentan como aceptación.

P2: **108 pytest / 32 Vitest** en las últimas ejecuciones, contratos TypeScript/build correctos; auditoría Python sin vulnerabilidades conocidas y npm 0. Migración de usuario aplicada tras backup SQLite consistente `output/p2-before-migration.db`; health P0/PAPER_ONLY/órdenes false y esquema 0002_data comprobados. API local real: health/quality/instruments 200, orden LIVE local negativa **403**. Registro: **98 instrumentos/series reales**, ningún seed; curvas separadas de bonos individuales, research sin permiso de valoración/órdenes. Smokes válidos: **17 modalidades / 17 proveedores**; 32 adaptadores / 29 proveedores implementados; 13 modalidades sin credenciales, SEC sin contacto real, 2 candidatas condicionadas pendientes. Utilizables frescas en la última lectura: **11** (caducan dos feeds cripto); cuatro restricciones display. GDELT volvió a dar timeout en el intento acotado posterior; no se cuenta. Datos personales/internos no se publican en las evidencias. Data Quality preparado y tipado, **todavía sin montar en Sistemas** por el gate P1.F. No se declara P2 completada.

QA final: offline/diagnóstico, WASD y ratón ignorados, retorno de inspección y control tras cerrar panel **pasan**. Reubicación adicional de paños laterales en el fondo y retirada de sus franjas blancas interiores; test de línea cámara–cabeza junto a los nueve agentes correcto. Capturas de aceptación en `docs/evidencias/P1_CORRECTIVO/aceptacion-*.png`. Licencias/hashes y FK finales correctos; detector UI sin hallazgos. Logs normalizados a UTF-8 sin espacios finales, originales conservados en output.

**Bloqueo de aceptación F confirmado:** Intel/D3D11, 1920×1080, Equilibrado/DPR 1, avatar caminando: Trading **22,40**, Recepción **23,88**, pasillo **22,52**, giro **17,14**, Comité **21,66**, repetición Trading **20,85** y flujo con panel automático **19,27 FPS**. Ventanas de 12 s, once rigs cargados, marcha previa, sin tests/compilación/WMI simultáneos; p95 108,8–131,7 ms. No se descartan tirones ni se usa FPS estático como marcha. El mínimo de 30 sigue fallando pese a batching/LOD/mamparas. No se atribuye exclusivamente a la presión de memoria; hace falta repetir con recursos disponibles para distinguir carga externa de problemas restantes de la escena. No se han cerrado aplicaciones del usuario ni modificado energía.

Siguiente paso exacto: liberar carga adicional con el usuario y repetir el benchmark real guardado en `scripts/qa_p1_corrective/`; si sigue fallando, perfilar y optimizar conservando calidad. Solo cuando F pase: montar Data Quality en MonitorOverlay/Sistemas, sustituir textos P2 pendientes, comprobar filtros/pausa/valores/offline/capturas reales y cerrar P2.6. Concluir verificación gratuita de Finnhub/Nasdaq y descargas ESMA selectivas sin inventar cobertura. **P1 correctiva y P2 no se declaran completas. STOP antes de P3.**

Último checkpoint de código: **e6cc900**, contratos Data Quality tipados, cliente/panel React preparado pero sin montar, endurecimiento de derechos/cuotas/Retry-After y evidencias normalizadas. Diff completo desde `ab830a5` sin errores de whitespace. Commits locales; no se ha hecho push. Navegadores de QA cerrados. Backend y frontend locales conservados para revisión; instrucciones y cifras en `docs/evidencias/P1_CORRECTIVO/README.md` y `docs/evidencias/P2/README.md`.

---

## 2026-10-14 · P1.B–F completadas · STOP antes de P2

Autorización actual: issue #1 y `docs/PLAN_CIERRE_P1_BF.md`, sincronizados con `origin/main` **abda9b6** mediante fast-forward. Sustituye los STOP históricos tras B/C. Antes de sincronizar se creó `output/p1-preclosure-20261014-131948.zip` con 24 archivos y hashes; los 23 archivos no solapados quedaron idénticos y `docs/02_MUNDO_3D.md` se combinó sin conflictos. La reserva arquitectónica local se conserva; stash de ese documento retenido como respaldo.

**Checkpoint B verde:** refinamientos anteriores preservados, techo/mamparas/marcos/lámparas elevados de forma coherente, señalética discreta y skyline mejorado. Se corrigieron las **23 sillas** de puestos/Comité para mirar hacia su mesa; prueba por raycast de la superficie real. Recepción utiliza mostrador para atención de pie y no tiene una silla de trabajo orientada incorrectamente. `python scripts/manage.py check`: **47 pytest + 13 Vitest**, TypeScript/build correctos. Capturas nuevas de [Recepción](docs/evidencias/P1B/cierre-integral/01-recepcion.png), [planta](docs/evidencias/P1B/cierre-integral/02-planta.png), [Trading](docs/evidencias/P1B/cierre-integral/03-trading.png) y [Comité](docs/evidencias/P1B/cierre-integral/04-comite.png). Chrome/Intel/D3D11, 1920×1080 Equilibrado, 12 s estáticos: Recepción **53,2**, Planta **53,1**, Trading **53,4**, Comité **56,5 FPS**. Estas cifras NO son aceptación en movimiento de F.

Preparación de C: no había modelos humanos ni Blender/MakeHuman en las rutas locales comprobadas. Se verificaron las fuentes gráficas MakeHuman y el traje formal de Margaret Toigo **CC0**, descargadas selectivamente sin instalar software pesado. El GLB derivado se integró y revisó posteriormente en C/E/F.

**Checkpoint C verde:** avatar humano MakeHuman/Margaret Toigo CC0 de 1,78 m, rig real y clips idle/walk originales; cámara elevada inicial 3,2 m / 3,8 m / FOV 65°, ratón derecho, zoom limitado, WASD relativo normalizado, giro suavizado, colisiones semánticas, spring arm, minimapa y nueve spawns libres comprobados. La inspección restaura el transform del jugador. Se añadió verificación de conectividad peatonal y se recorrieron **las nueve zonas con WASD real**, sin modificar posiciones desde automatización. [Controles](docs/evidencias/P1C/controles.json), [capturas y recorridos](docs/evidencias/P1C/). `python scripts/manage.py check`: **47 pytest + 15 Vitest**, TypeScript y build correctos.

Incidencias corregidas de C: spawn de Performance ocupado, reinicio StrictMode de AnimationMixer y luz insuficiente desde la cámara de juego. Renderizado en reposo reducido a 20 Hz, completo al moverse; techo excluido del mapa de sombras para aproximar la iluminación interior sin GI costosa. Intel/D3D11 Equilibrado 1920×1080: primera medición fría **19,2 FPS** (p95 141 ms, 39 muestras con movimiento); segunda en Trading tras carga **35,0 FPS**, p95 **52,2 ms**, 198 muestras con movimiento de 215, 122 draw calls y 218.182 triángulos. Equipo con batería al 94%, otras apps abiertas; F repetirá y optimizará con NPC. Hubo timeouts de tests bajo carga gráfica; repetidos con el navegador de QA cerrado pasan. No se ocultan los resultados iniciales.

**Checkpoint D verde:** nueve superficies físicas independientes, rango 2,25 m, cono 50°, cara frontal y LOS contra cristal/muebles. Nueve paneles React/DOM distintos, diálogo nativo con foco, Escape, Tab/Shift+Tab, cierre visible y mundo congelado; transform del jugador y cámara restaurado exactamente. Cliente tipado/validado de `/api/providers/status`, salud/proveedores P0 reales. Las interfaces financieras muestran las fases P3/P4/P5/P6 pendientes, sin filas, cotizaciones, curvas, votos u órdenes de ejemplo. Los nueve terminales se probaron con **E y clic físico**, caminando hasta su monitor desde cada spawn. [Capturas y pruebas D](docs/evidencias/P1D/).

Incidencias D corregidas: pasillo interior de Trading bloqueado por las sillas (filas separadas a ±1,95 m, conservando los seis puestos y nueve departamentos); brazo de cámara acortado por sillas bajas (origen de colisión a altura de cabeza, mirada al torso). Comité ya admite clic físico desde la perspectiva elevada. Desconexión comprobada interceptando/abortando las dos peticiones locales: el panel muestra NO DISPONIBLE y el avatar sigue moviéndose; backend intacto. `python scripts/manage.py check`: **47 pytest + 22 Vitest**, TypeScript/build correctos. Advertencias históricas de Starlette/httpx y bundle 3D grande siguen sin ser errores.

**Checkpoint E verde:** diez NPC humanos profesionales CC0 (Recepción 1, Trading 3, Research/Quant/Riesgos/Ejecución/Comité/Sistemas 1 cada uno), ropa formal y estados OFFLINE / trabajo NO DISPONIBLE — P4. Tres microanimaciones ambientales originales: idle, observe, focus; walk para el jugador. SkeletonUtils.clone con **once rigs independientes**, un solo Skeleton compartido entre las cinco piezas de cada actor, geometría/texturas compartidas. LOD con histéresis: **41.114 / 13.240 / 4.040 triángulos**, culling fuera de cámara y más de 26 m, mezcla/actualización de animación a 20/10/5 Hz por distancia. No luces ni sombras dinámicas por NPC; sombras de contacto suaves compartidas. Rutas, spawns y LOS de terminales siguen libres con los NPC como obstáculos semánticos. **24 Vitest + TypeScript/build correctos**; backend no modificado.

E, Intel Graphics/D3D11, Equilibrado/DPR 1, 1920×1080: Trading **55,1 FPS solo en movimiento**, p95 **25,5 ms**, 351 muestras de desplazamiento; promedio total 55,5 FPS, 167 draw calls, 340.622 triángulos, 46 texturas y 196 geometrías. [Capturas y datos E](docs/evidencias/P1E/). La recogida final distingue muestras en movimiento y cuenta también pausas largas; no usa FPS estáticos para afirmar rendimiento caminando. Los NPC reutilizan una base anatómica de calidad con tintes/escala y animación distintos; no son agentes operativos.

**Checkpoint F verde; P1 completada en el alcance autorizado. STOP antes de P2.** Se revisaron las capturas reales del build final: avatar humano de cuerpo entero, muebles/materiales, diez NPC, pasillos/techo, skyline, minimapa, Comité y paneles institucionales. [Entrega y comprobación](docs/ACEPTACION_P1.md) · [galería y evidencias completas](docs/evidencias/P1F/README.md).

Pruebas finales: `python scripts/manage.py check` **47/47 pytest + 25/25 Vitest**, TypeScript/build correctos; `python scripts/manage.py audit`: **ninguna vulnerabilidad conocida en Python y 0 en npm**; `git diff --check`: sin errores. [Logs](docs/evidencias/P1F/tests-finales.txt). Persisten dos advertencias: deprecación Starlette/httpx y bundle Three/R3F de 937 kB minificado (251 kB gzip). No se han ocultado ni convertido en errores de aplicación.

Aceptación en Chrome real con **ANGLE Intel Graphics / D3D11**, 1920×1080, Equilibrado/DPR 1: entrada directa en Recepción con avatar/cámara 3,2 m / 3,8 m; recorrido WASD por las nueve zonas sin modificar posiciones, nueve teletransportes seguros, nueve terminales por E y clic físico, foco/Tab/Escape, mundo pausado y restauración exacta de transform/cámara. Prueba adicional del avatar contra mostrador, mampara, columna y pared: **2.159 muestras sin penetraciones**, incluido deslizamiento lateral. [Colisiones reales](docs/evidencias/P1F/colisiones-avatar.json). Offline probado abortando únicamente las peticiones locales del navegador: interfaz NO DISPONIBLE y desplazamiento conservado. `/?diagnostico=1` disponible, `/health` 200/PAPER_ONLY/órdenes deshabilitadas, proveedores NO DISPONIBLE y POST local de órdenes LIVE **403 P0_EXECUTION_DISABLED**. Backend y App/diagnóstico P0 no modificados; ninguna orden externa.

Incidencias F corregidas: la interpolación de cámara cortaba esquinas de columnas y vidrio. Se añadió barrido/deslizamiento de cámara y pasos cortos cuando el segmento encuentra un obstáculo; broadphase vertical sin alterar las guardas del avatar/LOS. Recorrido final: **5.980 muestras, altura 3,2 m, cero penetraciones y cero cruces**. El diálogo nativo dejaba un paso de Tab al foco de navegador; se añadió cierre explícito del ciclo entre controles visibles/habilitados. Prueba real final de Tab/Mayús+Tab, E/clic, bloqueo y restauración correcta en [accesibilidad](docs/evidencias/P1F/accesibilidad.json). Se conservan los resultados negativos anteriores en las evidencias.

### Rendimiento final en movimiento

Ventanas de 12 s, entrada real WASD/ratón, muestras de desplazamiento separadas del total; se cuentan las pausas largas, no se usa el FPS estático de B. GPU/viewport/contadores e intervalos completos en cada JSON. Las aperturas y cierres de monitor están comprobadas en el mismo flujo; la ventana de FPS no representa un render activo del diálogo pausado.

| Escenario | FPS moviéndose | p95 movimiento | Muestras móviles | FPS total de ventana | Draw calls / triángulos |
|---|---:|---:|---:|---:|---:|
| Recepción | 41,5 | 41,3 ms | 274 | 37,8 | 204 / 346.188 |
| Trading con NPC | 54,1 | 26,4 ms | 357 | 52,1 | 167 / 340.600 |
| Giro de cámara | 59,9 | 18,4 ms | 393 | 52,9 | 162 / 367.192 |
| Comité | 37,6 | 58,5 ms | 279 | 32,7 | 72 / 167.126 |
| Pasillo acristalado | 34,7 | 62,9 ms | 258 | 32,8 | 143 / 330.794 |
| Recorrido + monitor | 32,8 | 53,2 ms | 274 | 28,9 | 141 / 351.162 |

No se promete 60 FPS constantes: se supera el mínimo de 30 durante desplazamiento en los seis escenarios, pero hay tirones y el total del flujo combinado cae a 28,9 FPS por pausas largas. E había medido 55,1 FPS caminando en Trading; las condiciones y vistas varían, no es una comparación controlada con B. Windows tenía ahorro de batería activo al 17% y una prueba combinada dio **29,8 FPS móviles**; quedó conservada. Tras conectar el cargador por el usuario se repitió: **32,8 FPS móviles**, AC conectado y ahorro desactivado comprobados por GetSystemPowerStatus. No se cambió el plan de energía. Los otros cinco escenarios se midieron antes de esa repetición y no se etiquetan como mediciones con cargador.

Carga observada: primer callback de escena aproximadamente **1,9–2,1 s**, primer frame GPU sincronizado **6,1 s**; no es una certificación de arranque frío completo de todos los humanos. Texturas/geometrías residentes: 48–52 / 197–201 según navegación. CPU Intel Core 5 120U, 10 núcleos/12 hilos, memoria física 16.847.925.248 bytes, driver Intel 31.0.101.4953. Rendimiento dependiente de carga del equipo y energía; perfil Detalle no certificado para 45–60 FPS.

Licencias/hashes verificados offline: **33 fuentes humanas, 6 mapas PBR, 5 mapas humanos**, GLB real con 163 huesos y cuatro clips, LOD 41.114/13.240/4.040 triángulos. Base anatómica nominal 1,78 m; altura medida del mesh vestido **1,803 m**. Assets gráficos MakeHuman/Margaret Toigo/Poly Haven **CC0**, meshoptimizer offline **MIT**. Licencia de código AGPL de MakeHuman separada: no se ha copiado ese código. Recursos runtime locales, sin CDN; ninguna dependencia o servicio de pago añadido. [Registro](assets/LICENSES.md) · [verificación](docs/evidencias/P1F/assets-verificados.json).

Limitaciones declaradas: una base humana reutilizada con variaciones de traje/escala y animación, iluminación indirecta/reflejos aproximados y skyline conceptual; no GI/reflectores costosos ni personajes únicos escaneados. Los NPC están OFFLINE y no realizan trabajos de agentes. Los paneles son interfaces finales de P1 con estados vacíos honestos: datos de mercado P2, ledger/NAV P3, agentes P4, riesgo/estrategias P5 y ejecución paper P6 siguen NO DISPONIBLES. **No se ha comenzado P2 ni habilitado operaciones; coste adicional 0 EUR.**

---

## 2026-10-14 · Revisión visual de P1.B implementada; pendiente de nueva aprobación

El usuario **aprobó la arquitectura general, los nueve departamentos y la paleta**. Esta revisión conserva la huella, los centros, pasillos, servicios P0 y controles existentes; refina únicamente el acabado de P1.B. **P1.C–F no iniciadas; detenerse para revisión visual.**

- Mobiliario: respaldos ergonómicos de superficie continua, asientos moldeados, bases metálicas con ruedas, hojas curvas y macetas torneadas, monitores finos con carcasa y soporte, teclados detallados mediante textura, carpetas, tazas y esculturas originales. Se mantienen geometrías fusionadas; los pequeños radios y biseles usan menos polígonos.
- Señalética: placas discretas de nogal/bronce integradas sobre las mamparas; Trading identificado en el suelo. Desaparecen los grandes carteles suspendidos. La vista de planta conserva los nueve nombres legibles.
- Exterior/luz: fachadas en todas las caras, alturas/retranqueos/coronaciones distintos y tres franjas de profundidad; cielo procedural, niebla neutra más lejana, menor iluminación ambiente plana, focos cálidos dirigidos hacia abajo y materiales/relieve/reflejos afinados.
- Cámara futura: techo a **4,5 m**, luminarias por encima de **4,03 m**, dinteles libres a **3,99 m**; vistas fijas a **3,25–3,35 m**, mirando hacia abajo. Documentados los rangos del usuario: 2,8–3,8 m de altura y 3–4,5 m detrás. No hay avatar ni seguimiento. P1.C deberá resolver el spawn exacto y las colisiones/oclusiones de cámara en recorridos reales.
- Coste adicional **0 EUR**. Ningún asset nuevo descargado, servicio contratado ni dependencia nueva. Geometría/texturas añadidas originales; los seis mapas CC0 y las licencias MIT anteriores se conservan. [Licencias actualizadas](assets/LICENSES.md).

### Capturas reales finales · 1920 × 1080

[Recepción](docs/evidencias/P1B/revision-visual/01-recepcion.png) · [Planta completa](docs/evidencias/P1B/revision-visual/02-planta.png) · [Trading Floor](docs/evidencias/P1B/revision-visual/03-trading.png) · [Comité](docs/evidencias/P1B/revision-visual/04-comite.png).

Se inspeccionaron las cuatro imágenes del build final. Son capturas de la aplicación WebGL en Chrome, con ANGLE **Intel Graphics / D3D11** comprobado; ninguna es un render generativo ni una imagen que sustituya la oficina. Se conservan las capturas anteriores para comparar.

### Pruebas, seguridad y rendimiento finales

`python scripts/manage.py check`: **47/47 pytest + 13/13 Vitest aprobados**, TypeScript y build correctos (14-10-2026, 10:19 Madrid). Los tests de geometría comprueban la altura mínima real del techo y rayos a 3,8 m por los nueve umbrales centrales, además de planta/presupuesto. GET local `/health`: 200, `PAPER_ONLY`, `orders_enabled=false`, DB/migración OK. POST local `/api/orders` con `mode=LIVE`: **403 P0_EXECUTION_DISABLED**. Backend, contratos, SQLite, guardas y transporte de órdenes sin modificaciones. Sin datos financieros ni actividad de agentes inventados. `git diff --check` correcto.

Equipo anterior conservado: Intel Core 5 120U, Intel Graphics y 16 GB; pantalla 1920×1080/60 Hz. Mediciones finales en una sesión aislada de **Chrome headless con la GPU Intel real**, Equilibrado (DPR 1/sombras 1024), 12 s de render continuo, hasta 600 intervalos registrados, cámara fija, foco/visibilidad verificados y sin compilación de tests concurrente. Cada JSON incluye renderer, pose, resolución y fecha. [Evidencias y lecturas completas](docs/evidencias/P1B/revision-visual/).

| Vista | FPS anteriores de referencia | FPS final revisado | p95/frame final | Draw calls | Triángulos visibles |
|---|---:|---:|---:|---:|---:|
| Recepción | 59,1 | **56,2** | 27,9 ms | 150 | 203.718 |
| Planta completa | 60,0 | **53,7** | 27,6 ms | 170 | 217.952 |
| Trading Floor | 47,5 | **59,2** | 18,4 ms | 100 | 159.092 |
| Comité | 60,0 | **59,3** | 21,7 ms | 70 | 113.366 |

Respecto a las cifras históricas: Recepción aproximadamente −5 %, Planta −10,5 %, Comité −1,1 %; Trading sube. **No son pruebas idénticas:** cambian la altura de cámara, geometría, modo de navegador y condiciones energéticas. Como comparación adicional, el build anterior archivado desde HEAD midió **57,78 FPS en recepción** en la misma sesión headless con alimentación de red, frente a **56,21** revisados (−2,7 %; poses distintas). El objetivo de 45–60 FPS se alcanza en las cuatro vistas finales. La pérdida más visible respecto a la referencia histórica está en la planta completa.

Durante ensayos previos, WMI informó batería al **12 % y descargando**; tanto la oficina anterior (29,72 FPS) como la revisada rondaron 30 FPS. Después informó `BatteryStatus=2` y 17 %: acceso a alimentación de red, coincidiendo con la recuperación de FPS. Se conservan las lecturas de referencia; se interpreta el estado con [documentación Microsoft de Win32_Battery](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-battery). No se modificaron ajustes de energía. Esto es una condición observada y una posible explicación de la variación, no una prueba de causalidad exclusiva.

**Carga y límites:** escena preparada en 1,83 s y primer frame sincronizado en 6,63 s en la navegación final; la referencia anterior, con otras condiciones de caché, dio 2,40 s hasta primer frame. No se certifica descarga fría ni un tiempo fijo. El chunk de Three/R3F sigue en 918,46 kB (244,63 kB gzip); el de Office pasa a 53,15 kB (18,83 kB gzip). Se mantiene el aviso de bundle y las deprecaciones existentes. Reflejos PMREM y sombras de contacto aproximadas; no SSR, ray tracing ni GI dinámica completa. El perfil Detalle no se ha recertificado en esta revisión: priorizar Equilibrado.

**Incidencias resueltas:** las luces de área ensayadas se retiraron al observar unos 26 FPS bajo carga/batería; no se atribuye toda la caída al tipo de luz. Se corrigieron facetas de los respaldos con una superficie de normales continuas y un error de sintaxis en su primera implementación; la batería final de tests está verde. Una medición en el navegador de revisión sufrió cambio de cámara y se descartó; las cuatro medidas finales se obtuvieron aisladas y se validaron contra sus poses/resolución.

**Comprobación manual:** recargar `http://127.0.0.1:5173`, elegir las cuatro vistas y pulsar «Medir FPS» con la cámara quieta, navegador visible, Equilibrado y condiciones energéticas comparables. El diagnóstico P0 sigue en `/?diagnostico=1`. **Siguiente paso: aprobación visual de esta revisión de P1.B; esperar antes de implementar P1.C.**

---

## Checkpoint P1.A–B previo a la revisión de acabado (histórico)

## 2026-10-14 · P1.A y P1.B terminadas para revisión visual

**Alcance alcanzado:** la ruta inicial abre una oficina 3D real en React Three Fiber/Three.js. Una sola planta de 34 × 28 m contiene los nueve departamentos según el plano: Research, Comité y Quant al norte; Riesgos, Trading y Ejecución en el centro; Performance, Recepción y Sistemas al sur. Hay pasillos y umbrales abiertos, mamparas de vidrio, mobiliario propio de cada sala, luminarias, piedra, madera oscura, bronce y skyline geométrico. Las cámaras Recepción/Trading/Comité/Planta sirven para inspeccionar el diseño. El diagnóstico P0 sigue en `/?diagnostico=1`.

**Límite de fase:** las cámaras de inspección no son la navegación jugable. Avatar, WASD, colisiones y teletransporte corresponden a P1.C; paneles clicables a P1.D; diez NPC y pulido posterior a P1.E–F. Los monitores actuales son objetos 3D con rótulos `NO DISPONIBLE`, sin cotizaciones, posiciones, NAV, P&L, órdenes, saldos ni trabajos ficticios. **Detenido antes de P1.C para aprobación visual del usuario.**

**Hardware comprobado:** Windows 11; Intel Core 5 120U (10 núcleos/12 hilos); 16.847.925.248 bytes de RAM instalados; Intel Graphics, driver 31.0.101.4953; pantalla 1920 × 1080. Chrome expone `ANGLE (Intel, Intel(R) Graphics (0x0000A7AC) Direct3D11 vs_5_0 ps_5_0, D3D11)`. WMI informa 1 GiB de AdapterRAM, que no representa toda la memoria compartida de esta iGPU. Arquitectura y presupuesto: [ARQUITECTURA_P1_AB.md](docs/ARQUITECTURA_P1_AB.md).

**Licencias/coste:** seis mapas JPG 1K de Dark Wood y Marble 01 (Poly Haven, CC0) guardados localmente, con autores, URL, MD5 publicado y SHA-256 por archivo en [LICENSES.md](assets/LICENSES.md) y [P1_ASSET_MANIFEST.json](assets/P1_ASSET_MANIFEST.json). Geometría, skyline y señalética originales; Three.js/R3F/Drei y sus dependencias gratuitas inventariadas en [LICENCIAS_P1.md](docs/LICENCIAS_P1.md). Recursos solicitados en runtime: solo origen `127.0.0.1`, sin CDN ni claves. **Coste adicional de servicios: 0 EUR**; ninguna compra, despliegue ni API de pago.

### Pruebas y seguridad de P1.A–B

| Comprobación | Resultado real, 14-10-2026 |
|---|---|
| `python scripts/manage.py check` | **47/47 pytest, 13/13 Vitest, TypeScript y build Vite correctos.** Los cuatro tests nuevos comprueban plano, pasillos/cota única, cámaras y presupuesto geométrico. |
| `python scripts/manage.py audit` | pip-audit: sin vulnerabilidades conocidas; npm audit: 0 vulnerabilidades en las bases consultadas. |
| Navegador Chrome, build de producción | Arranque directo en WebGL; nueve nodos 3D presentes; vistas y selector gráfico funcionales. Capturas reales a 1920 × 1080: [Recepción](docs/evidencias/P1B/01-recepcion.png), [planta completa](docs/evidencias/P1B/02-planta.png), [Trading Floor](docs/evidencias/P1B/03-trading.png), [Comité](docs/evidencias/P1B/04-comite.png). Sin errores de renderizado en la carga normal; dos avisos se describen abajo. |
| Backend ausente | `/health` sustituido **solo en el navegador de prueba** por HTTP 503; la escena siguió visible y la información marcó «Servicios locales: NO DISPONIBLE». [Captura de esta simulación](docs/evidencias/P1B/05-backend-no-disponible-simulado.png). Se retiró la sustitución al terminar. |
| P0 y paper trading | GET `/health`: 200, `PAPER_ONLY`, `orders_enabled=false`, SQLite/migración correctas. POST local `/api/orders` con `mode=LIVE`: **403 P0_EXECUTION_DISABLED**. El diagnóstico P0 volvió a mostrar `BASE LOCAL DISPONIBLE`. Backend y ruta de órdenes sin cambios de código en P1.A–B. |
| Red, assets y secretos | Solicitudes inspeccionadas: solo JS/CSS/mapas locales y `/health` en `127.0.0.1:5174` (preview con proxy local); los seis archivos coinciden con tamaño y SHA-256 del manifiesto. Sin peticiones a brókeres, fuentes externas ni claves en el frontend. `git diff --check` sin errores. |

### Rendimiento medido

Chrome/ANGLE sobre la Intel integrada, viewport 1920 × 1080, perfil Equilibrado DPR 1 y sombras 1024, benchmark visible de 12 s de render continuo. Se guardó cada lectura completa en [evidencias P1.B](docs/evidencias/P1B/). El modo quieto renderiza bajo demanda: no se anuncia un FPS de reposo.

| Vista | FPS medio | p95/frame | Llamadas de dibujo | Triángulos | Condición |
|---|---:|---:|---:|---:|---|
| Recepción | 35,0 | 66,7 ms | 137 | 161.184 | Primera medición, compilación/carga del navegador y otras tareas simultáneas. |
| Recepción | **59,1** | 18,3 ms | 137 | 161.184 | Nueva medición con build final ya calentado. |
| Planta completa | 60,0 | 18,2 ms | 157 | 166.892 | Equilibrado. |
| Trading Floor | 47,5 | 38,8 ms | 94 | 123.556 | Equilibrado. |
| Comité | 60,0 | 17,2 ms | 60 | 79.572 | Equilibrado. |
| Comité, Detalle | **34,9** | 60,6 ms | 60 | 79.572 | DPR 1,35/sombras 2048; conviene usar Equilibrado en esta iGPU. |

En una navegación nueva, `loadMs` (escena preparada) fue 3,21 s y `firstFrameMs` (primer frame WebGL sincronizado) 5,35 s; otra recarga con respuesta de salud simulada tardó 9,89 s al primer frame bajo distinta carga. No se garantiza este tiempo en otros equipos. En las mediciones la escena contiene 153–154 geometrías y 28–34 texturas según vista/calentamiento; el plano muestra las nueve zonas.

**Incidencias y límites:** Vite advierte un chunk Three/R3F de 918,45 kB minificados (244,62 kB gzip), que eleva el arranque frío. Chrome muestra un aviso de API `THREE.Clock` de la dependencia y uno de precisión del shader en el driver Intel; cero errores en carga normal. El perfil Detalle cae por debajo del objetivo de 45 FPS; Equilibrado queda por defecto. La pérdida simulada de `/health` produce el error HTTP esperado en consola, sin bloquear la oficina. La revisión visual del usuario y la calidad final de toda P1 siguen pendientes. No se ha iniciado P1.C–F.

**Para comprobar:** `python scripts/manage.py check`; arrancar `python scripts/manage.py backend` y `python scripts/manage.py frontend` en dos terminales, abrir `http://127.0.0.1:5173`, cambiar las cuatro cámaras y pulsar «Medir FPS» en Equilibrado. Abrir `/?diagnostico=1` para P0. Al cerrar esta verificación, backend y frontend dev escuchaban exclusivamente en `127.0.0.1:8000` y `127.0.0.1:5173`; pueden no persistir entre sesiones y no requieren credenciales.

---

## Checkpoint P0 (histórico)

- **2026-10-13 · P0_BASE terminada técnicamente; pendiente de revisión del usuario. P1 NO iniciada.**
- Aplicación ejecutable: **SÍ**, base técnica local de frontend, backend y SQLite. Sin oficina 3D simplificada ni assets 3D incorporados.
- Servicios contratados, créditos comprados y despliegues: **NINGUNO**. Coste adicional de servicios: **0 EUR**.
- Órdenes live y paper: **BLOQUEADAS en P0**, sin transporte de ejecución.
- Integraciones con claves reales: **NO**. Alpaca Paper, Trading 212 Demo y Twelve Data: **NO DISPONIBLE**, acceso no comprobado.
- Cotizaciones, trades, beneficios y actividad de agentes: **no generados**. Registro de instrumentos inicialmente vacío.
- Ledger de 10.000 EUR ficticios: **pendiente de P3**, separado por diseño de cuentas demo. No se ha creado un saldo provisional ni sumado cuentas.
- Secretos nuevos: **NINGUNO**. `.env` local creado desde el ejemplo, credenciales vacías, excluido de Git.
- Modelo/esfuerzo seleccionado por el usuario: no consta confirmación del selector; no se ha cambiado automáticamente ni se han lanzado subagentes.

## Implementado

| Área | Archivos y resultado |
|---|---|
| Frontend | `frontend/src/`, `index.html`, TS/Vite. React 19.3.0, TypeScript 7.0.2, Vite 8.3.4, TanStack Query 5.104.2. Página técnica P0 en español; comprobación real de salud, recuperación de errores y adaptación móvil. |
| Backend | `backend/app/{main,config,contracts,database,providers,security}.py`. FastAPI 0.143.0, Pydantic 2.14.1, SQLAlchemy 2.1.4, Uvicorn 0.54.0. Salud, proveedores, instrumentos, bloqueo de órdenes y OpenAPI local. |
| Base de datos | `alembic.ini`, `backend/migrations/`, revisión `0001_instruments`. Alembic 1.20.0, SQLite WAL, claves foráneas y busy_timeout. Registro vacío con UUID y unicidad símbolo/mercado/divisa. Arranque exige migración. |
| Contratos | Instrumentos multiactivo, capacidades independientes con fecha/licencia/motivo, términos de bono, cotización Decimal con procedencia, ámbitos MASTER/ALPACA_PAPER/T212_DEMO. Interfaces de datos y broker bloqueado sin red ni credenciales. |
| Seguridad | Configuración congelada; rechazo de live y URLs fuera de allowlist exacta; denegación incondicional de órdenes en dominio/API; hosts/CORS locales; sin access logs ni Swagger/CDN; sin exposición de `.env` al navegador. |
| Reproducción | `pyproject.toml`, `uv.lock`, `.python-version`, `frontend/package-lock.json`; `scripts/{setup,manage,license_inventory}.py`. Herramientas `.tools/`, entorno `.venv/`, DB `data/`, ignorados por Git. |
| Pruebas y documentación | `backend/tests/`, `frontend/src/api.test.ts`, `output/playwright/`; README, decisiones D010–D015, `docs/ARQUITECTURA_P0.md`, `docs/LICENCIAS_P0.md` e índice actualizados. |

## Entorno y licencias

Windows 11 Pro x64 10.0.26200; Node v26.3.0; npm 11.16.0; Python 3.14.4; SQLite 3.50.4; Git 2.55.0.windows.3; uv 0.13.0. No se modificó la política de PowerShell ni se instalaron servicios de sistema. Otros sistemas/versiones no certificados por esta fase.

Dependencias directas y transitivas inventariadas desde METADATA/LICENSE y package-lock: [LICENCIAS_P0.md](docs/LICENCIAS_P0.md), con versiones y fuentes oficiales. Sin suscripciones de software, fuentes descargadas ni assets de terceros en P0. Recursos y rendimiento 3D pendientes de P1.

## Pruebas ejecutadas: resultados reales

| Comando / comprobación | Resultado final |
|---|---|
| `python scripts/setup.py` | OK: uv sync --locked, npm ci, creación no destructiva de .env y migración local. |
| `python scripts/manage.py check` | **47 tests pytest + 9 tests Vitest aprobados; TypeScript y build Vite correctos.** Última batería completa: 13-10-2026, 18:35 Madrid. Un aviso de deprecación, descrito abajo. |
| Backend | Salud/arranque, DB ausente/degradada, migración up/down/up e idempotencia, Alembic sin drift, WAL/FK, persistencia tras reconexión, unicidad, contratos/Decimal/procedencia, CORS/hosts, live y URLs manipuladas rechazados, órdenes paper/live denegadas, secretos no expuestos. Tests permiten solo loopback para asyncio Windows; sin conexiones externas. |
| Frontend | Acepta contrato paper válido; rechaza LIVE, órdenes habilitadas, DB fallida, fecha inválida y respuestas incompletas; maneja HTTP 503 y desconexión. |
| `python scripts/manage.py audit` | **pip-audit: sin vulnerabilidades conocidas. npm audit: 0 vulnerabilidades**, según bases consultadas el 13-10-2026. No equivale a garantía absoluta. |
| HTTP real local | Health/proveedores/instrumentos/OpenAPI: 200. Instrumentos `[]`; proveedores NO DISPONIBLE y checked_at nulo. POST local `/api/orders` con modo live: **403 P0_EXECUTION_DISABLED**, sin contacto con bróker. `/docs`: 404, sin CDN. |
| Red | `Get-NetTCPConnection`: 8000 y 5173 escuchan exclusivamente en 127.0.0.1. Recursos del frontend observados únicamente desde origen local. |
| Playwright/Chromium | Escritorio 1440×1000 y móvil 390×844 revisados visualmente. Botón funcional; backend detenido → NO DISPONIBLE; reiniciado → BASE LOCAL DISPONIBLE. |
| Variables frontend | Build con marcador ficticio VITE_SECRET_SENTINEL: marcador ausente de dist. Variable retirada después; ningún secreto real usado. |
| Git/seguridad | .env, DB/WAL, entornos y node_modules excluidos; credenciales locales vacías. Revisión manual: sin cliente de ejecución ni ruta de órdenes habilitable. |

Evidencia real sin credenciales: [escritorio](output/playwright/p0-desktop.png), [móvil](output/playwright/p0-mobile.png), [backend desconectado](output/playwright/p0-offline.png). No son renders de una oficina futura.

## Incidencias y limitaciones

1. PowerShell bloqueó `npm.ps1`: resuelto con `npm.cmd`, sin modificar la política del equipo.
2. Primer aislamiento de red bloqueó socketpair interno de asyncio Windows (2 fallos y 10 errores). Corregido permitiendo solo loopback; batería final aprobada.
3. Primera llamada de pip-audit llevaba `--disable-pip` sin requirements: corregida; auditoría final OK.
4. Una llamada a Vitest coincidió con la reinstalación npm ci y no encontró el binario. Se terminó setup y se repitió check secuencialmente: 9/9 y build correctos. Ejecutar setup y check en secuencia.
5. Favicon inicialmente ausente: corregido con SVG propio embebido. La caída intencionada del backend produjo el error HTTP esperado y NO DISPONIBLE.
6. **Mantenimiento no bloqueante:** Starlette 1.8.0 avisa que TestClient con httpx está deprecado a favor de httpx2. Los 47 tests pasan con el lock actual; evaluar la migración del cliente al actualizar dependencias. El aviso no se oculta.
7. uv informa que ignora el entorno `.tools` del bootstrap y utiliza `.venv`, comportamiento previsto. Sin cambios globales.
8. No hay autenticación de red, backups automáticos, feeds, jobs, ledger, motor de riesgo ni ejecución. La aplicación es exclusivamente local. Guardas de redirects, preflight, kill switch y reconciliación UNKNOWN deberán implementarse antes de permitir órdenes paper en P6.

## Comandos de comprobación

Desde la raíz, en PowerShell:

```powershell
python scripts/setup.py
python scripts/manage.py check
```

Después, en dos terminales distintas:

```powershell
# Terminal 1
python scripts/manage.py backend
```

```powershell
# Terminal 2
python scripts/manage.py frontend
```

Abrir **http://127.0.0.1:5173**, pulsar «Comprobar conexión» y comprobar «BASE LOCAL DISPONIBLE». Salud: **http://127.0.0.1:8000/health**. Parar con Ctrl+C. No hacen falta claves. Más detalles en [README](README.md).

Se dejaron los servidores de comprobación ejecutándose en localhost para facilitar la revisión; no son servicios permanentes ni se garantiza que sobrevivan al cierre de la sesión. Si un puerto está ocupado, comprobar la instancia existente antes de arrancar otra.

## Siguiente paso

**Sin bloqueos técnicos de aceptación de P0. Falta revisión y autorización del usuario para P1.** Al iniciarla, comprobar hardware/rendimiento y seleccionar recursos gratuitos con licencias y atribuciones verificadas. No se ha adelantado trabajo artístico. La entrada final deberá ser el mundo 3D con nueve departamentos reales conectados.

Datos externos corresponden a P2, ledger de 10.000 EUR a P3, agentes a P4, riesgo a P5, ejecución paper a P6 y auditoría global a P7. Ninguna de esas funciones se declara implementada aquí. **Detenido tras P0.**
