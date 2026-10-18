# P4 — Research local, operación y límites

## Operación

La oficina 3D continúa siendo la entrada. Ejecutar `python scripts/manage.py backend` y `python scripts/manage.py frontend`. La base local requiere `python scripts/manage.py migrate`; esquema `0004_research`, posterior a `0003_portfolio`.

El modelo es opcional para arrancar HQ. En este PC, `python scripts/start_local_llm.py` verifica los hashes del GGUF y del ejecutable contra `assets/local-ai/manifest.json`, y arranca llama.cpp oculto en 127.0.0.1:8089. No descarga ni compra nada. Los binarios y pesos permanecen en `output/p4-runtime`, excluidos de Git. En otro equipo hay que preparar explícitamente esos mismos archivos oficiales; no existe instalación ni fallback remoto automático. El modelo y runtime tienen licencias Apache-2.0 y MIT incluidas en `assets/local-ai`.

En Research: seleccionar un instrumento del registro P2, crear el caso y pulsar **Analizar · sin operar**. El refresco público es opcional y respeta las políticas P2. Cerrar un panel no cancela el trabajo. La acción Cancelar detiene los jobs pendientes del mismo run; conserva resultados anteriores. El selector de versiones permite revisar ejecuciones fallidas o anteriores sin mezclarlas con el dossier actual.

Sistemas muestra modelo, cola y fallos; Quant muestra features y procedencia; Comité muestra opiniones Bull, Bear y Chair. El videowall AGENTES y los indicadores de departamento proceden de jobs reales. Los 16 NPC no son 30 procesos LLM. PC apagado: no trabaja ningún modelo; la base conserva la cola.

## Arquitectura

Treinta contratos lógicos reutilizan los identificadores aprobados. Pipeline inicial de nueve roles: Data Quality, dos especialistas según clase de instrumento, Macro Global, Momentum/Trend, Volatility/Regime, Bull, Bear y Chair. Para FX los especialistas son Market Structure y Liquidity/Slippage. Los roles fuera del pipeline tienen contrato y estado; no se ejecutan automáticamente ni se afirma disponer de treinta análisis especializados probados end-to-end.

Siete workers con límites de una inferencia, dos tareas quant y cuatro fetches; además un semáforo limita las derivaciones CPU compartidas. Cola SQLite por prioridad, activación por eventos, dos intentos máximo, timeout y bloqueo de proceso para impedir dos schedulers sobre la misma base. Las tareas de hilo mantienen su plaza al cancelarse hasta que termina la llamada; Python no puede matar de forma segura un hilo HTTP.

Persistencia: agents, agent_jobs, research_cases, evidence, agent_results, research_claims y audit_events. Evidencias, claims, resultados y auditoría son inmutables. La conexión de escritura P4 tiene authorizer SQLite que deniega escrituras fuera de esas tablas. No es un sandbox de Python arbitrario: no se entrega ejecución de Python, shell ni SQL al modelo. P2/P3 se leen mediante servicios internos; no se exponen secretos ni herramientas de bróker.

## Evidencia y grounding

Solo fuentes P2 con derechos de acceso, almacenamiento, visualización y redistribución autorizados. Se conservan observaciones, fechas, fuente, URL, hash y alcance. Los datos MASTER son contexto virtual de solo lectura. Las features usan Decimal y series comparables; las fuentes no disponibles no producen features disponibles.

Los claims numéricos requieren evidence IDs existentes y tokens numéricos presentes en la evidencia citada. **VERIFIED_EXTRACT** significa coincidencia textual exacta con una observación fresca y disponible; no demuestra causalidad, exactitud económica del proveedor ni veracidad de una interpretación. El resto sigue UNVERIFIED. Python extrae los FACT y sus IDs de la selección de evidencia; el modelo devuelve claims vacío. El validador independiente comprueba el emparejamiento. Así no se gastan tokens en copiar hashes ni se confía al modelo la creación de hechos.

Los pasajes narrativos con cifras no vinculadas a un claim verificado se omiten completos y se muestran como NO VERIFICADO. Se guardan campo, motivo, hash del pasaje y hash de la salida original; no se inventa una corrección. Cualquier omisión fuerza INSUFFICIENT_EVIDENCE. Los claims con IDs inventados o números sin respaldo siguen provocando rechazo del job. La salida cualitativa se etiqueta interpretación; no es una recomendación de compra/venta. Este pipeline inicial es descriptivo: al no existir una rúbrica validada de suficiencia para conclusiones direccionales, research_view permanece INSUFFICIENT_EVIDENCE. No se habilitan ratings POSITIVE/NEGATIVE por mera preferencia del modelo.

La lectura del dossier reevalúa antigüedad, derechos y disponibilidad del caché. Si se retiran derechos se oculta el contenido derivado. No se comprueba continuamente la existencia remota de cada URL: la disponibilidad observable es la del repositorio local P2 y su política; una retirada remota aún no detectada es una limitación explícita. Un último HTTP 403/404/410 persistido por P2 sí degrada inmediatamente la disponibilidad de la evidencia. Las listas están limitadas a los últimos 500 registros; no se certifica una carga histórica ilimitada.

## Seguridad y APIs

GET `/api/agents`, `/api/agents/status`, `/api/research/cases`, `/api/research/cases/{id}`, `/evidence`, `/results`, `/api/agent-jobs/{id}`. POST de creación de caso, `/cases/{id}/run` y `/agent-jobs/{id}/cancel` requieren cabecera local, origen permitido e idempotency key. No hay herramientas autónomas ni POST a brókeres. Contenido externo es UNTRUSTED_CONTENT. LocalLLM solo acepta loopback, sin proxy del entorno ni redirects; no hay fallback de pago.

PAPER ONLY; orders_enabled=false; POST /api/orders=403. MASTER, ledger, NAV y posiciones no se modifican por research. Riesgo P4 es advisory; riesgo/veto P5, órdenes/fills P6: NO DISPONIBLE. STOP antes de P5.

## Validación

Resultados exactos, capturas auténticas, benchmark y limitaciones de la ejecución: [evidencias P4](evidencias/P4/README.md). Los fixtures marcados TEST_ONLY nunca se escriben en la base operativa. Ningún mock cuenta como conexión, research real ni benchmark de mercado.
