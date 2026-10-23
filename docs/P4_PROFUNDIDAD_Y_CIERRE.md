# P4 — profundidad adaptativa y cierre acotado

## Estado actual · 23-10-2026

Actualización posterior: `debate-wire.v2` ya elimina el truncamiento observado en la campaña acotada, manteniendo 384 tokens/90 s por llamada. Se añadieron comparaciones Python, diagnósticos persistentes, cuarentena de rechazos y revalidación de dossiers. Los modelos todavía repiten observaciones/argumentos y no completan un debate financieramente válido; **P4 sigue PARTIAL**. No repetir los ensayos ni aprobar modelos por velocidad o por JSON válido. [Reparación, pruebas reales y continuación exacta](evidencias/P4/reparacion-debate-20261023/README.md).

La propuesta de este documento ya se implementó para las ejecuciones nuevas: `ordinary` por defecto con tres jobs Python, síntesis local opcional única, y `deep` explícito con Bull/Bear/Chair secuenciales. Profundidad y opción de síntesis se persisten en el run y su idempotencia; los runs antiguos no se reinterpretan. Se aplican presupuestos de una llamada por rol, 90 s por llamada LLM, 256/384 tokens y 90/270 s por caso. El dossier conserva resultados Python y muestra `PARTIAL`/`INCOMPLETE` cuando la síntesis falla.

La campaña real del 23-10 verificó A ordinario y C insuficiente, pero B profundo no completó Bull/Bear/Chair tras **dos** intentos con una causa técnica modificada entre ellos. Qwen2.5 produjo una síntesis semánticamente contradictoria y Qwen3 una salida sin grounding suficiente; ambas se retiran del dossier. **P4 permanece PARTIAL.** Resultados, tiempos y límites: [evidencia de profundidad adaptativa](evidencias/P4/adaptativo-20261023/README.md). Los apartados siguientes conservan el diseño y el diagnóstico históricos de 22-10; no son el estado de implementación actual.

Decisión del usuario del 22-10-2026: cerrar con evidencia, incluso PARTIAL/BLOCKED si el debate no cumple; no repetir inferencias indefinidamente. No se rebaja la aceptación semántica ni se permite ejecutar órdenes. El informe de cierre distingue implementación, ejecución técnica y calidad financiera.

## Estado y propuesta de profundidad

| Consulta | Implementación actual | Evolución propuesta, aún no implementada |
|---|---|---|
| Calidad / referencia | `data_quality` y `macro_reference`: cuatro jobs Python; sin debate forzado | Mantener como vía ordinaria cuando ese sea el objetivo explícito |
| Descripción de un instrumento | Features Python disponibles, pero `investable_thesis` abre el pipeline amplio | Nuevo objetivo explícito `descriptive_research`, con métricas Python y como máximo una síntesis compacta opcional. No convertir silenciosamente una tesis en informe de datos |
| Investigación profunda | Pipeline según activo, Bull/Bear/Chair separados; guardas de suficiencia/mandato | Selección explícita del usuario y evidencia relevante suficiente. Debates secuenciales con presupuestos por rol y total del caso; ninguna promoción automática desde una consulta ordinaria |
| Fallo del modelo | Jobs persistentes FAILED/TIMEOUT/NO_LOCAL_MODEL y dependencias BLOCKED; API/3D siguen funcionando | Conservar todos los intentos y resultados Python. Mostrar qué especialista no terminó. Nunca rellenar la síntesis ni sustituirla por una conclusión favorable |

La profundidad debe persistirse dentro del run y su clave idempotente, no ser una propiedad mutable global. El registro de treinta roles y sus permisos permanece separado de la selección de roles de cada caso. Un mismo expediente puede conservar varios runs con objetivos/profundidades explícitos sin sobreescribir resultados anteriores. No se requieren treinta modelos ni procesos.

Los límites actuales son una inferencia, dos trabajos quant y cuatro fetches, con timeout de 300 s y máximo de dos intentos por job. No constituyen un SLA aceptado. Propuesta para siguiente autorización: evitar retry automático de TIMEOUT sin cambiar las condiciones; un presupuesto total explícito y una única síntesis breve en modo ordinario. Reintento de contrato solo si existe diagnóstico nuevo. Si se implementa, probar idempotencia, cancelación, recuperación y que el presupuesto incluye todos los intentos. No se eleva el timeout para esconder lentitud.

Las contradicciones numéricas, retornos, frescura, unidades, features y controles financieros pertenecen a Python. JSON válido y evidencia citada no demuestran que un mecanismo causal sea correcto. Las nuevas restricciones de salida cualitativa no relajan los validadores anteriores ni certifican semántica.

## Límite del experimento de cierre

Se conserva el run p4.11 ya terminado: Bull TIMEOUT en dos intentos, Bear/Chair BLOCKED. No se vuelve a lanzar. Diagnóstico: una petición sintética de hasta 128 tokens y 120 s para cada uno de los dos modelos existentes, sin escribir resultados ficticios en Research. Sin descargas, sin cambio de seguridad de Windows, sin cerrar aplicaciones del usuario. `scripts/diagnose_p4_runtime.py` conserva tokens, TTFT, timings del servidor, CPU, RAM, fallos de página y contadores globales de page-in.

Los fallos de página del proceso incluyen fallos blandos; los contadores de lecturas/páginas entrantes son del sistema completo. No atribuir todas las lecturas de disco al LLM. El TTFT por streaming incluye preparación/contexto y no equivale al tiempo de carga. El arranque se mide por separado; la caché del SO no se fuerza ni se afirma una carga fría.

## Encaje futuro — requisito registrado, no implementación

Se ha leído el documento [Plan_JAIME_P5_P6.md](Plan_JAIME_P5_P6.md). Sus propuestas de broker, tarifas y regulación siguen pendientes de verificación primaria; no se adopta ninguna integración. Por instrucción más reciente del usuario se registra su encaje y se difiere su auditoría detallada/plan de implementación a una nueva autorización.

- Conservar los treinta `role_id`, en especial Quant, Risk, Bull, Bear y Chair. Risk actual sigue advisory; no se crea veto P5.
- Reutilizar conceptualmente jobs/versiones/hashes/evidencia, manteniendo futuros experimentos y sus descartes en un dominio propio. Un ResearchCase no debe convertirse en un ledger ni en un backtest.
- El futuro LLM propone hipótesis mediante contratos tipados y recibe resúmenes compactos. Python ejecutaría cálculos/experimentos preaprobados; no código generado arbitrario.
- El archivo P2 conserva observación/ingesta y revisiones, pero **no demuestra** universos históricos, corporate actions, publicaciones point-in-time, costes ni un calendario exhaustivo. Estas carencias impiden certificar hoy un laboratorio multiactivo libre de sesgos.
- Registrar todos los intentos, genealogía, datos/código/configuración y descarte; sellar OOS y contabilizar búsqueda múltiple. No implementar todavía esos motores ni producir supuestos resultados.
- Mantener research, MASTER y cualquier ejecución futura aislados. MASTER 10.000 EUR ficticios, PAPER ONLY, orders_enabled=false y POST /api/orders=403 permanecen invariantes.

P5/P6 no iniciados. No se conecta un broker, OAuth con trading, runtime completo Vibe-Trading ni nuevos canales Agent Reach.

## Siguiente paso técnico propuesto tras compactar el HUD (no implementado)

1. **Contrato del run:** añadir profundidad explícita `ordinary | deep` a `RunCase`, con objetivo `descriptive_research` para descripción. Incluirla en idempotencia, payload persistido, hash y versión del plan. Runs históricos sin el campo conservan su significado anterior; el formulario nuevo propone ordinario. No reinterpretar una tesis profunda ni sobrescribir un dossier antiguo.
2. **Planificador:** ordinario selecciona Data Quality y features Python pertinentes al instrumento, y como máximo una síntesis opcional por un rol existente con mandato aplicable. Profundo conserva especialistas pertinentes y Bull → Bear → Chair; abre esa ruta solo tras suficiencia y selección explícita. No se añaden roles/modelos ni se alteran capacidades 1/2/4.
3. **Contrato compacto:** `CompactResearch` con resumen, IDs de evidencia y limitaciones; cifras/contradicciones se presentan desde Python. Es distinto del contrato Chair que exige Bull/Bear previos. No fabricar esos argumentos para satisfacer el esquema. Guardas actuales de datos, derechos, grounding, inyección y prohibición de órdenes siguen activas.
4. **Presupuesto experimental inicial:** probar contexto seleccionado y 256–384 tokens máximos, sin thinking largo, 90 s por llamada; un intento y ningún retry automático de timeout. Para profundo, techo total inicial de 270 s para los tres especialistas, sujeto a medición antes de aceptarlo. Estos límites son una propuesta, no una promesa de latencia/calidad. No arrancar otro modelo ni aumentar concurrencia para eludirlos.
5. **Degradación:** conservar resultados Python y jobs fallidos, mostrar `INCOMPLETE`/`NO_LOCAL_MODEL` con causa y retorno inmediato a la oficina. Sin fallback externo, conclusiones sintéticas ni bloqueo global de UI. Cancelar el run debe detener su llamada pendiente y conservar trazabilidad.
6. **Aceptación antes de dar P4 por listo:** tests de selección, idempotencia por profundidad, presupuestos, cancelación/reinicio y regresión financiera; después una campaña acotada con un caso ordinario real, uno insuficiente y un profundo suficiente. Revisar semánticamente Bull/Bear/Chair contra fuentes y medir memoria/latencia/FPS con condiciones registradas. Si falla, conservar PARTIAL; no repetir automáticamente el mismo experimento.

La futura fábrica de estrategias mantiene Python para experimentos masivos y roles para hipótesis/crítica, con registro de descartes y aislamiento de ejecución según `Plan_JAIME_P5_P6.md`. Ese requisito arquitectónico no autoriza a iniciar P5/P6.
