# P4 avanzado — validación y límites

## Arquitectura y causas

El checkpoint inicial conservó P1–P3, `0004_research`, treinta roles y los límites 1 LLM / 2 quant / 4 fetch. El checkpoint posterior de datos aplica `0005_data_history`, sin modificar tablas financieras; ver `P2_REFRESH_Y_PERSISTENCIA.md`. El commit `5fd14e2` separa objetivo, ejecución y calidad. No se atribuye el problema únicamente al tamaño del modelo: el contrato anterior uniforme, la pérdida de IDs en la vista del modelo y la pregunta informativa BCE contribuían al debate repetitivo.

Ahora existe EvidencePack con alias estables, identificador inmutable, tipo de dato, feed, venue, divisa, unidad, frecuencia, fecha, derechos y alcance. El modelo no recibe instrucciones ejecutables desde contenido externo. Los contratos Bull, Bear y Chair son diferentes; las citas cruzadas, las cifras y los duplicados se validan. Los rechazos pueden reintentarse una vez con otra semilla; no se convierte un texto rechazado en resultado válido. Una validación estructural/léxica **no prueba razonamiento financiero**.

`macro_reference` y `data_quality` producen cuatro jobs deterministas. `investable_thesis` necesita al menos tres fechas de mercado comparables del mismo feed; esta condición mínima no demuestra suficiencia fundamental ni habilita una recomendación. Si no se cumple, la salida es `ABSTAINED`, no una tesis inventada.

## Prueba real y experimentos aislados

Caso informativo BCE `66dc5f17-849a-4e32-a90a-76e45a7ba447`: cuatro jobs, 32 evidencias y `NOT_APPLICABLE` para debate direccional. Caso de tesis con esas mismas referencias `65885284-5037-4346-b1fa-06808398f0cd`: nueve jobs deterministas de abstención, sin inferencia ni supuesto debate. No cuenta como pipeline generativo aceptado.

Los benchmarks generativos son **TEST_ONLY** y no escriben en la base de datos operativa. Qwen3-1.7B Q8_0 repitió tesis y justificó caja positiva con evidencia de plazos de cobro crecientes; Chair agotó timeout. Qwen2.5-1.5B Q4_K_M repitió mecanismos y negó hechos aportados. Llama-3.2-3B Q4_K_M, solicitado explícitamente como candidato en el nuevo encargo, repitió tesis tanto en el primer intento como tras la corrección y semilla 18. Bear/Chair quedan bloqueados cuando Bull es rechazado. **Ninguno está aceptado para debate autónomo.** Se preservan las salidas originales y sus hashes, sin presentarlas como investigación real.

Llama: cuantización comunitaria de bartowski, revisión `5ab33fa94d1d04e903623ae72c95d1696f09f9e8`, SHA-256 `6c1a2b41161032677be168d354123594c0e6e67d2b9227c84f296ad037c728ff`, 2.019.377.696 bytes. Pesos locales, fuera de Git. Licencia, atribución y manifest en `assets/local-ai/llama32-*`. **Built with Llama**. El candidato no reemplaza silenciosamente el modelo del manifest principal. Launcher explícito `--candidate llama32`; sin descarga automática.

## HUD y datos

Rails negros de 340 px (300 px a 1280), texto principal sans serif de 16 px, detalles plegables, tabs con teclado y clic sobre los nueve NPC principales. Los históricos exigen al menos tres observaciones comparables con derechos; no se crean velas ni cambios diarios desde referencias. Dos series de referencia tienen histórico; no se han conseguido cotizaciones autorizadas de los símbolos de la captura. Sin histórico se muestra «—». Nunca se copia el dinero ni los precios del ejemplo del usuario.

Capturas iniciales encontraron el videowall sin datos mientras la API respondía. Comprobaciones posteriores del contrato HTTP y tres arranques verificaron su actualización. Se amplió el margen de arranque a 15 s y se añadió un único reintento para fallos de red/timeout, sin reintentar contratos inválidos. Las capturas de aceptación esperan datos y fuentes tipográficas antes de guardar. No se afirma que esto certifique todas las condiciones de carga.

## Integraciones read-only

| Herramienta | Pin y capacidad | Prueba / estado | Coste y límite |
|---|---|---|---|
| Agent Reach | 1.5.0, `94f06c1969dfc1834001269d79d3ad0972d9dee6`, MIT; canal RSS BCE A20 ya auditado | Recogida real de evidencia mediante cliente seguro P2; no se importa el runtime Agent Reach ni se suman proveedores ficticios | 0 EUR; GET público con allowlist, cuota y caché; sin cuentas/cookies/escritura |
| Vibe-Trading | 0.1.16, `d7f1b9e22b42c10197497a8e2cac4f0e2cc9ca1e`, MIT; 30 presets catalogados | `METADATA_ONLY`; inspeccionados adicionalmente `academic/strev.py` y `academic/high52w.py`: requieren cierres diarios y normalización transversal | No hay panel de cierres diarios verificables suficiente; **no se portan como si fueran factores operativos** ni se fabrican OHLCV. Los ocho descriptores HQ son código propio, no resultados Vibe. Sin runtime, shell, código generado o brokers |
| Liquid Co-Invest | [Documentación oficial](https://www.liquid.trade/coinvest-docs), revisada 2026-10-19 | Sigue describiendo token OAuth con scopes read y trade; `BLOCKED_TRADE_SCOPE` | Sin conexión/OAuth/credenciales. No se afirma inexistencia universal de un producto read-only; no se ha verificado uno utilizable |
| Herramientas no identificadas | Sin nombre concreto | `REQUIRES_USER_IDENTIFICATION` | No se habilita una integración por inferencia |

Los pins y auditorías anteriores siguen vigentes; no se actualizó ningún paquete upstream. Los resultados de este checkpoint no habilitan P5 ni P6.

## Estado de cierre

P4 avanzado sigue pendiente de aceptación semántica. El informe determinista y la abstención son funcionales; no sustituyen el requisito de un debate invertible con evidencia real y razonamiento fiable. El detalle de pruebas, capturas y mediciones se registra en `docs/evidencias/P4/avanzado/README.md` y `STATUS.md`. PAPER ONLY, `orders_enabled=false`, `/api/orders=403`, cero órdenes, cero cambios de cash/ledger/NAV/posiciones y 0 EUR de servicios.

## Reanudación de 20-10-2026

El histórico CoinPaprika autorizado para IA personal aporta 90 instantáneas diarias, separadas del spot y sin fabricar OHLCV. No convierte los factores Vibe pendientes en operativos ni concede redistribución. La prueba generativa BTC p4.8 detectó una afirmación falsa de crecimiento diario: la muestra real contenía movimientos en ambos sentidos. Ese resultado no se acepta.

Corrección p4.9 en validación: selección acotada del histórico independiente de noticias/macro; comprobación determinista de que microestructura/liquidez necesitan evidencia específica, sin inferir libro o costes desde precios agregados. Python añade una descripción verificable de la trayectoria completa para impedir que solo tres puntos elegidos aparenten monotonía. Se preserva el resultado rechazado y no se rellena su narrativa con una respuesta ficticia.

## Cierre acotado 22-10-2026 — PARTIAL

El run p4.11 termina con Bull TIMEOUT en ambos intentos y Bear/Chair bloqueados. No se repite el pipeline. Se completan 212 tests backend, 54 frontend, TypeScript/build, auditoría, restart y UI. Diagnóstico de dos peticiones cortas muestra presión de memoria y paginación, con rendimiento distinto según candidato y condiciones de alimentación/carga. No certifica semántica. Véase [evidencia final](evidencias/P4/cierre-20261022/README.md) y [profundidad adaptativa](P4_PROFUNDIDAD_Y_CIERRE.md). P4 sigue sin aceptación; se espera nueva instrucción del usuario. P5/P6 no iniciados.
