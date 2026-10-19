# Evidencias P4 e interfaz

**Estado: P4 no aceptada semánticamente.** La infraestructura funciona y la interfaz solicitada está implementada. Los benchmarks de JSON/grounding no prueban que el modelo produzca un debate financiero fiable. No se inicia P5 ni P6.

## Cambios visibles

- [Paneles laterales simplificados](simple-sidebars.png): negro, Arial local, texto ampliado, lista bajo el logo y procedencia desplegable. Sin cotizaciones ni sparklines inventados.
- [Clic en nueve NPC](npc-clicks.json): eventos nativos del ratón; nueve paneles abiertos, pausa/cierre y control recuperado. Los dieciséis NPC están conectados al mismo manejador; se probaron los nueve principales.
- Capturas reales: [Research](click-research.png), [Quant](click-quant.png), [Comité](click-committee.png), [Sistemas](click-systems.png). Estas capturas prueban apertura; no certifican calidad de un dossier.
- [Responsive y diagnóstico](responsive-diagnostic.json), [móvil](mobile-ui.png), [P0](diagnostic.png). Sin overflow horizontal; el zoom local produce un viewport CSS distinto del tamaño de captura.

## Pruebas y rendimiento

[Check](check.txt): 182 pytest, 49 Vitest, TypeScript y build, exit 0. [Audit](audit.txt): cero vulnerabilidades conocidas. Persiste aviso deprecación TestClient/httpx y chunk 3D grande. Alembic check sin cambios pendientes.

[Regresión HTTP](http-regression.json): 30 roles, 98 instrumentos P2, MASTER EUR 10000 ficticios, cero posiciones, orders_enabled=false y POST /api/orders=403. [Backup/reopen](restore-result.json): dos ciclos de apertura/recovery conservan historial e integridad. [Runtime realmente apagado](no-local-model-real.json): NO_LOCAL_MODEL, sin fallback externo.

[FPS tras simplificar paneles](fps-after-ui.json), Intel Graphics/D3D11, movimiento con flechas, 16 NPC, inferencia local simultánea: Recepción 58,09; Trading 58,68; Comité 58,32; Sistemas 59,44. DPR 0,81–0,84, p95 18,6–21,7 ms. Captura 1920×1080, canvas CSS reportado 2133×1200 debido al zoom; CDP focus emulation evita throttling por oclusión. Sin builds/tests durante la medición. Muestra anterior [59,59–59,91 FPS](fps-moving.json); no es A/B controlado ni garantía universal. Un intento interrumpido por proximidad se excluyó y repitió. [Recorrido anterior nueve salas](nine-room-tour.json) preservado.

## Runtime y calidad

Dos candidatos, sin descargar más: Qwen2.5-1.5B-Instruct Q4_K_M y Qwen3-1.7B Q8_0, ambos Apache-2.0; llama.cpp b11696 MIT. [Manifest y hashes](../../../assets/local-ai/manifest.json), licencias en esa carpeta. Modelos y bases de datos fuera de Git.

- [Qwen2.5 fixture](benchmark-qwen25.json): JSON/grounding/injection 2/2; TTFT frío 16,17 s, 9,64 tokens/s; segundo prompt caliente 0,43 s y 15,71 tokens/s. [Memoria](memory-qwen25.json), pico aproximado 1,78 GiB.
- [Qwen3 fixture](benchmark-qwen3.json): JSON/grounding/injection 2/2; TTFT frío 9,53 s, 10,14 tokens/s; segundo caliente 0,94 s y 10,19 tokens/s. [Memoria](memory-qwen3.json), pico previo aproximado 2,96 GiB.
- Fixture TEST_ONLY, nunca escrito como mercado real. Python extrae hechos exactos y valida sus IDs; las interpretaciones son UNVERIFIED. Pasar este fixture no equivale a precisión semántica financiera.
- [p4.5 Qwen3](e2e-p45.json): nueve jobs mecánicamente finalizados, tesis Bull/Bear repetida; **no aceptado**.
- [p4.6 Qwen3](e2e-p46.json): contexto aislado y rechazo de duplicados; Bear falló, Chair quedó bloqueado. No se borra ni reescribe el historial.

Pipeline base nueve roles: Data Quality, Market Structure, Liquidity/Slippage, Macro Global, Momentum/Trend, Volatility/Regime, Bull, Bear, Chair. Un instrumento FX real de P2; no cartera nueva ni órdenes. Los otros roles tienen contratos y permisos; no se afirma haber validado treinta especialistas financieros.

## Límites

Claims numéricos se contrastan con evidencia; eso no verifica causalidad ni interpretación. Los modelos pequeños han mostrado repetición y confusión entre referencia, spread e identificador de serie. P4 permanece pendiente hasta que el debate auténtico sea suficiente. Riesgo es advisory; sin veto P5, backtesting ni ejecución P6. Fuentes stale se degradan; no se verifican todas las URLs remotas continuamente. Historial listado máximo 500 registros. PC apagado: sin inferencia, cola persistente.

PAPER ONLY · servicios 0 EUR · sin API LLM de pago · MASTER intacto · STOP antes de P5.


## Resultado final del segundo candidato

[Qwen2.5, p4.6](e2e-qwen25-p46.json), run `08dec597-8a6b-4a6a-9426-ad5dd3e29545`: siete jobs SUCCEEDED, Bear FAILED tras dos intentos por DEBATE_DUPLICATE_THESIS y Chair BLOCKED por dependencia. Tampoco supera la aceptación; no hay modelo aprobado para el debate. Runtime de prueba detenido al terminar: NO_LOCAL_MODEL refleja que no hay servidor activo, no que se hayan borrado los pesos. No se descargó un tercer candidato. P4 **bloqueada por calidad semántica**.

El siguiente paso es resolver ese bloqueo; no repetir UI, investigación de proveedores, migración ni recorrido. Los cambios pedidos de watchlist/tipografía/clic NPC están implementados y comprobados.


## Capturas finales de lectura

Contexto de navegador nuevo para neutralizar el zoom heredado: **1920×1080 CSS, devicePixelRatio 1**. Texto principal de paneles a 16 px; títulos mayores, notas a 14 px. [Research](final-research-header.png), [dossier](final-research-dossier.png), [Quant](final-quant-dossier.png), [Comité incompleto](final-committee-header.png), [Sistemas](final-systems-header.png), [videowall](final-videowall.png), [registro UI](final-panels.json). No se presenta una imagen conceptual como aplicación terminada. [Frontend tras ajuste final de legibilidad](frontend-legibility.txt): 49 tests y build/TypeScript pasan.

[Inventario persistente final](final-counts.json): 30 roles, 3 casos, 90 jobs históricos, 254 evidencias, 52 resultados, 148 claims, 165 eventos de auditoría. Jobs: 52 SUCCEEDED, 28 CANCELLED, 6 FAILED, 4 BLOCKED. Estos totales incluyen intentos anteriores y **no representan 52 análisis aceptados**. [Runtime final](final-runtime-status.json): cola y trabajos activos cero, servidor LLM detenido.
