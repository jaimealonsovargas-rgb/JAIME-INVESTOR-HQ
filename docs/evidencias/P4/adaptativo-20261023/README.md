# P4 · profundidad adaptativa, campaña acotada del 23-10-2026

**Resultado: PARTIAL.** El modo ordinario determinista funciona con datos reales; Bull/Bear/Chair no completaron un debate validado en el hardware local. Ningún JSON válido o job Python se cuenta como aceptación del Comité. No se inició P5/P6 ni se envió una orden.

## Cambios comprobados

- `descriptive_research` es el objetivo por defecto del formulario; `ordinary` y `deep` se seleccionan explícitamente por ejecución y forman parte de idempotencia, payload persistido y hash del plan. Los runs históricos conservan su significado.
- El modo ordinario programa tres roles Python (`data_quality`, `momentum_trend`, `volatility_regime`) y permite **una** síntesis local opcional. El modo profundo programa siete roles según clase de activo, incluidos Bull, Bear y Chair secuenciales. Siguen existiendo treinta roles lógicos y un solo LLM local a la vez.
- Cálculos de retorno, volatilidad, trayectoria, drawdown y comprobaciones de cifras se ejecutan en Python Decimal. La síntesis compacta no puede introducir cifras ajenas a extractos vinculados ni afirmar que faltan métricas que Python sí obtuvo. El rechazo conserva la salida bruta solo para auditoría privada y oculta la narrativa inválida en el dossier.
- Una ejecución nueva tiene un intento por job; 90 s por llamada LLM, máximo 384 tokens profundos o 256 ordinarios, y presupuesto de caso 270/90 s. No se eleva el plazo para ocultar la lentitud. La UI mantiene los resultados Python y muestra el fallo local. El resumen rápido presenta cuatro métricas descriptivas con conteo de evidencias, únicamente cuando la calidad actual sigue `VERIFIED_DATA`.
- `NO_LOCAL_MODEL` no afecta al modo ordinario Python. Los controles históricos de derechos, frescura, procedencia, inyección, permisos y abstención continúan activos.

## E2E real por HTTP y navegador

| Caso | Instrumento y derecho | Resultado real | Tiempo total |
|---|---|---|---:|
| A ordinario | BTC, histórico CoinPaprika para uso personal local autorizado; no redistribuir el payload | `COMPLETE / VERIFIED_DATA`, 3/3 jobs Python, 91 evidencias; refresco del 23-10 tras quedar obsoleta la captura anterior | 1,416 s |
| B profundo, intento 1 | El mismo histórico, evidencia suficiente para iniciar el debate | `INCOMPLETE`: 4 jobs Python correctos, Bull `INVALID_RESULT_OR_RUNTIME` al agotar 384 tokens, Bear/Chair `BLOCKED` | 88,529 s |
| B profundo, intento 2 | Esquema de salida acortado tras diagnosticar el error del primer intento | `INCOMPLETE`: 4 jobs Python correctos, Bull `TRUNCATED_OUTPUT` a 384 tokens, Bear/Chair `BLOCKED` | 92,650 s |
| C insuficiente | BTC-USD, sin serie directa autorizada comparable para research | `COMPLETE / ABSTAINED`, 3/3 jobs Python, cero hechos financieros fabricados; no se llama al LLM | ejecución guardada en archivo privado |

IDs: A `1a89a2d0-d831-4ada-83ad-60f7208d0c3d`, B final `d9bf0eee-9a4b-48f4-b42d-1fe115aae651`, C `af7dfc20-a977-42e3-b3e9-91f5694f2829`. La captura A de la noche anterior pasó de `VERIFIED_DATA` a `ABSTAINED` al caducar sus observaciones; el nuevo caso refrescado restituyó la serie. Es una degradación correcta por frescura, no una modificación retroactiva de los cálculos guardados.

Dos síntesis breves opcionales tampoco superaron la aceptación: Qwen2.5 completó una salida en 33,913 s, pero dijo que no había estadísticas pese a las features Python; la revalidación actual la rechaza y el dossier es `PARTIAL / REJECTED`. Qwen3 tardó 66,787 s y falló `NUMBERS_OUTSIDE_CLAIMS`; conservó los cálculos Python con `PARTIAL / VERIFIED_DATA` mientras la serie estaba vigente. Al caducar la evidencia, el dossier pasa correctamente a `PARTIAL / ABSTAINED`; la síntesis fallida jamás restituye la vigencia. No se hicieron más inferencias.

## Diagnóstico de los dos modelos ya instalados

Peticiones sintéticas equivalentes, una por modelo, máximo 128 tokens/120 s, llama.cpp local, corriente alterna y batería al 100 %. No certifican calidad financiera; la RAM libre inicial y la longitud exacta de la salida difirieron. TTFT incluye prefill; la carga del servidor se midió por separado en diagnósticos previos. Fallos de página blandos del proceso no son todos I/O; las lecturas de página son del sistema completo, no atribuibles enteramente al LLM.

| Medida | Qwen2.5-1.5B Q4_K_M | Qwen3-1.7B Q8_0 |
|---|---:|---:|
| Tokens entrada/salida | 586 / 28 | 590 / 38 |
| Prefill | 8,257 s | 14,862 s |
| TTFT | 8,469 s | 14,871 s |
| Generación | 14,58 tok/s | 9,87 tok/s |
| Tiempo total | 10,136 s | 18,622 s |
| RAM libre mínima del sistema | 1455 MiB | 724 MiB |
| RSS máximo proceso | 1787 MiB | 2319 MiB |
| Lecturas de página/s, media global | 13,05 | 179,64 |
| JSON del fixture | válido | válido |

Los pesos existentes están verificados en el [registro previo de licencia y hashes](../cierre-20261022/README.md): Apache-2.0, sin nuevas descargas. Qwen2.5 fue más rápido en este fixture, pero su respuesta real falló semánticamente; no se selecciona como modelo financiero aprobado. Qwen3 tampoco superó el debate. Con ~16 GB de RAM y 724 MiB libres durante Qwen3, la presión de memoria es un factor plausible; no se atribuye la diferencia a una sola causa.

## QA, capturas y seguridad

- `python scripts/manage.py check`: **220 pytest**, **54 Vitest** y una prueba opt-in omitida, TypeScript y build correctos. `python scripts/manage.py audit`: cero vulnerabilidades conocidas. `git diff --check`: sin errores. `backend/tests/test_research.py`: 50 pruebas, incluida abstención ordinaria sin invocar modelo y degradación al caducar la evidencia.
- Navegador real 1920×1080: oficina, clic en NPC Research, selector ordinario/profundo, caso A con métricas visibles, C con abstención y B `INCOMPLETE` visibles. Tras reiniciar el backend hubo siete 502 transitorios en la pestaña abierta; recarga posterior: cero errores de consola. La watchlist y MASTER respondieron por API y reaparecieron. Un ensayo de FPS a DPR 0,8 mostró 60 FPS con teclas, pero se abrió el panel de Recepción por proximidad durante la ventana; **no se usa como benchmark continuo de movimiento**. La última medición válida bajo LLM sigue siendo la del 21-10 (31,68–37,71 FPS, registrada en STATUS).
- `GET /api/portfolio/master/summary`: MASTER, caja ficticia `10000.00`, cero posiciones, un evento, hash `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`; `PAPER_ONLY`, `orders_enabled=false`. HTTP real `POST /api/orders`: **403**. Sin brókeres, APIs LLM de pago ni coste adicional.
- Capturas auténticas y payloads financieros de uso personal permanecen fuera de Git en `output/p4-adaptive/`: `office-1920.png` (SHA-256 `f134ca1f...ed17627c45`), `case-a-ui.png` (`901aee94...79418fa5`), `case-b-ui.png` (`b2ba81bb...da5a09f`), `case-c-ui.png` (`4808c61e...1d807449`). Los dossiers completos, diagnósticos y logs están en el mismo directorio ignorado. Este documento publica estados y tiempos, no precios ni extractos con redistribución no autorizada.

**Pendiente para SUCCESS P4:** un debate Bull/Bear/Chair completo y semánticamente validado con evidencia real, sin ampliar ciegamente contexto, RAM, plazo o aceptación. La ruta ordinaria permite investigar mientras el modelo esté apagado; el modo profundo informa con precisión `INCOMPLETE`. P5/P6 siguen sin iniciar.
