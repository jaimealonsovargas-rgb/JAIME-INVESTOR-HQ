# Reparación acotada Bull / Bear / Chair · 23-10-2026

**Resultado: PARTIAL. No hay debate completo financieramente validado.** Se reparó el transporte y mejoró el diagnóstico; no se atribuye fiabilidad financiera a ninguno de los dos modelos. Prioridades 1–4 siguen sin cierre de aceptación. No se inició autonomía programada ni P5/P6.

## Implementación comprobada

- Transporte `debate-wire.v2`: un argumento por llamada, claves cortas y aliases de evidencia reversibles. Se conservan todos los campos públicos de Bull/Bear/Chair. El mapa y los prompts tienen hashes; Python reconstruye únicamente estructura e IDs, nunca razonamiento. Las citas siguen vinculadas a fuentes originales.
- Gramática acotada a dos citas y prosa cualitativa; longitudes expresadas también dentro del patrón. Se excluyen comillas, escapes y saltos de línea del texto generado para evitar JSON roto en la conversión de patrones. La salida vuelve a validarse en Python, incluidos campos/IDs desconocidos, duplicados, cifras, presupuesto y truncamiento. No se completa un JSON parcial.
- Python aporta comparaciones exactas del retorno, posición respecto a la media, dispersión y drawdown. Se distinguen observaciones de hipótesis; no se delega aritmética al LLM.
- Guardas compartidas contra negación de métricas existentes, contradicción explícita del signo del retorno, cantidades financieras escritas, garantías y afirmaciones contables sustentadas solo en precios. Son comprobaciones concretas, **no un verificador semántico universal**.
- Se rechaza copiar una observación en el campo de mecanismo, repetir la tesis como supuesto, repetir literalmente etiquetas del contrato y dejar ciertas cláusulas incompletas. Bear conserva el control de solapamiento y Chair necesita el par válido. Una guarda experimental basada en verbos se descartó por riesgo de falsos positivos; hay un test que protege formulaciones causales alternativas.
- Fallos conservan modelo, tokens, tiempos, motivo de terminación y hash de salida. Los candidatos estructurados rechazados se ponen en cuarentena en `audit_events` local, fuera de resultados/claims publicados. Al abrir dossiers antiguos se revalidan los argumentos y se retiran los que ahora fallan, sin alterar el registro histórico del job.
- `p4.14-debate-wire`; sin migración, sigue `0005_data_history`. Treinta roles, capacidad 1 LLM / 2 quant / 4 fetch, máximo un intento por job nuevo, 384 tokens y 90 s por llamada profunda / 270 s por caso. Sin ampliar timeouts ni retries.

## Ensayos reales y límites

Datos P2 reales: histórico diario BTC CoinPaprika autorizado para investigación personal local; 91 evidencias por caso, incluidas derivaciones y contexto. No equivale a disponer de fundamentales, flujos, libro de órdenes ni evidencia causal. No se publican precios ni payloads en Git.

| Ensayo | Tiempo del caso | Resultado observado |
|---|---:|---|
| Qwen2.5, wire v1 · `f61e8fea…` | 31,334 s | Bull cerró JSON en 139 tokens; rechazado por longitud. Bear/Chair bloqueados. |
| Qwen2.5, wire v2 · `80fd08ed…` | 47,824 s | Bull cerró en 118 tokens; Bear cerró en 126 pero repitió el argumento: `DEBATE_SEMANTIC_OVERLAP`. Bull fue retirado posteriormente: una observación no es un mecanismo favorable. |
| Qwen3, guarda experimental · `a56caf5f…` | 46,155 s | Bull cerró en 152 tokens; guarda causal demasiado amplia lo rechazó. No se usa este rechazo aislado como prueba de incapacidad semántica. Se corrigió esa guarda antes del siguiente ensayo. |
| Qwen3, guarda revisada · `fcbb1bb9…` | 84,682 s | Bull cerró en 161 tokens y Bear en 152. Bull repitió tesis/supuesto y dejó cláusulas incompletas; Bear copió su postura y mecanismo. Bear rechazado, Chair bloqueado. La revalidación final retira también Bull. |

Campaña limitada a esos **cuatro casos, seis inferencias financieras**, con una causa técnica modificada entre ensayos; además canarios breves de JSON/longitud. Ninguna llamada financiera nueva terminó en TIMEOUT o `TRUNCATED_OUTPUT`. Esto resuelve el fallo de serialización en la muestra, **no** el problema financiero. No se ejecutó Chair con datos de debate inválidos ni se sintetizó su respuesta en Python. No se realizarán más inferencias de esta campaña.

El canario Qwen2.5 confirmó ambas variantes de `response_format`; no se culpó sin prueba al formato JSON de la API. Un canario posterior detectó un patrón que permitía texto incompatible con JSON; la clase explícita de caracteres y longitudes pasó el canario siguiente. Un canario es solo formato, nunca aceptación financiera.

## Medición local

Windows / Intel / ~16 GB, alimentación de red `AC=1` en todas las muestras, tres threads CPU, contexto 4096, una ranura, sin thinking. Solo pesos previamente instalados con hashes verificados y licencia Apache-2.0: Qwen2.5-1.5B-Instruct Q4_K_M y Qwen3-1.7B Q8_0. Runtime llama.cpp b11696; no nuevas descargas ni APIs externas de IA.

| Medida | Qwen2.5 wire v2 | Qwen3 ensayo final |
|---|---:|---:|
| Entrada / salida Bull | 1201 / 118 tokens | 1205 / 161 tokens |
| Entrada / salida Bear | 1361 / 126 tokens | 1398 / 152 tokens |
| Tiempo cliente Bull / Bear | 19,270 / 20,305 s | 29,314 / 45,384 s |
| Prefill Bull / Bear | 11,952 / 12,784 s | 14,399 / 28,061 s |
| Generación Bull / Bear | 18,60 / 18,94 tok/s | 11,54 / 9,24 tok/s |
| RAM libre mínima | 620,5 MiB | 1066,6 MiB |
| RSS máximo del proceso | 1159,3 MiB | 2649,2 MiB |
| CPU media (% de todos los procesadores lógicos) | 19,43 % | 21,33 % |
| Lecturas de paginación del sistema, media | 51,80/s | 96,61/s |

No es un A/B causal: difieren caché de prefijo, carga y RAM disponible. Qwen3 Bull reutilizó 515 tokens de contexto. Las lecturas de paginación son globales, no atribuibles enteramente al LLM. TTFT y carga fría no se midieron en estos POST no streaming; no confundir prefill con TTFT. Se descargó el runtime de RAM al terminar. El menor tiempo de Qwen2.5 no lo convierte en modelo financiero aprobado.

## Regresión y seguridad

- `manage.py check`: **278 pytest, 54 Vitest + 1 opt-in omitido**, TypeScript y build correctos. Después del último ajuste de IDs: **21 pruebas focalizadas correctas**, incluida una parametrización nueva; no se afirma que la suite completa se repitiera después.
- `manage.py audit`: cero vulnerabilidades conocidas. `git diff --check` correcto. Avisos preexistentes de deprecación Starlette/Three y chunk grande Vite, sin error de build.
- Sin modelo: caso ordinario `9949fc53…`, `COMPLETE / VERIFIED_DATA`, tres jobs Python, **1,036 s**. Caso insuficiente `28e49d72…`, `COMPLETE / ABSTAINED`, tres jobs Python, **1,031 s**; sin salida ficticia de IA.
- Reinicio real conserva jobs, errores, evidencias y revalida el Bull anterior como `REJECTED`. UI real 1920×1080: clics NPC Research/Quant/Comité/Sistemas, cuatro paneles sin overflow ni errores JS; videowall muestra `NO_LOCAL_MODEL` y estados reales.
- Oficina: **56,74 FPS en movimiento**, 670 muestras móviles, p95 22,5 ms, Intel Graphics D3D11, Equilibrado/DPR 0,8, 1920×1080. Flechas durante 12 s en el pasillo, 48/48 muestras de posición en movimiento, sin pausa/modal. **LLM apagado**: no certifica rendimiento bajo inferencia ni una mejora gráfica causada por este cambio.
- MASTER mantiene caja/NAV `10000.00 EUR` ficticios, cero posiciones y hash `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`. Treinta roles, cola/activos cero, `PAPER_ONLY`, `orders_enabled=false`, POST `/api/orders` **403**. Sin brokers, órdenes ni gastos.

Evidencias completas privadas: `output/p4-debate-repair/`. Capturas auténticas: `office.png`, `research.png`, `quant.png`, `committee.png`, `systems.png`, `videowall.png`, `moving-no-llm.png`. Ver `artifacts.json` para hashes sin publicar datos licenciados. El wrapper de diagnóstico termina con exit 2 si el caso sigue incompleto; un JSON válido nunca equivale a aprobación financiera.

## Punto de continuación

**P4 PARTIAL: siguen pendientes prioridades 1–4 en su aceptación financiera y la autonomía del punto 9.** No hay caso completo Bull/Bear/Chair aprobado. Los validadores detectan fallos, pero no confieren fiabilidad general a los modelos.

Antes de otra campaña, cambiar la tarea semántica y el suministro de evidencia: plantear una hipótesis concreta respaldada por evidencia económica relevante, no pedir un caso favorable genérico a partir de unas métricas de precio. Probar una defensa causal breve por separado, después una objeción dirigida y solo entonces Chair; sin preguntas compuestas, relleno, palabras cortadas ni más retries del pipeline actual. Conservar cálculos/comparaciones Python y revisión independiente. El laboratorio `Plan_JAIME_P5_P6.md` y la autonomía siguen como diseño futuro; no se implementan para ocultar este bloqueo.
