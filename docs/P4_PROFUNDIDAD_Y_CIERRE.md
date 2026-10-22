# P4 — profundidad adaptativa y cierre acotado

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
