# B2.5 — coordinación n8n en sombra

06-11-2026, Europe/Madrid. Implementado y probado el recorrido **n8n → CycleRequest → cola SEC existente → modelos contables → estado consultable**. n8n Community 2.46.6 y Node 24.22.1 están instalados aisladamente; el flujo está publicado y el servidor escucha en 127.0.0.1. Esta entrega utiliza investigación contable determinista; no implementa minería, inferencia ni ejecución de órdenes.

## Agenda y contrato

`sec-company-review-v1` revisa Apple, Microsoft y Walmart cada seis horas, a las 00:00/06:00/12:00/18:00 UTC. n8n es su único propietario de programación. El worker SEC de JAIME consume solicitudes, sin añadir un reloj interno para esta agenda. El ciclo descriptivo A21 conserva su agenda independiente. No se ha trasladado toda la autonomía a n8n.

La solicitud incluye versión 1, objetivo fijo `SEC_COMPANY_REVIEW`, modo `shadow`, ventana UTC, ID del evento derivado de la ventana, correlación de entrega y presupuesto. El ID del ciclo lo deriva JAIME. El hash de intención excluye solo la correlación: dos ejecuciones de n8n pueden entregar la misma intención y recuperar el mismo ciclo. Se conserva la correlación de la primera entrega.

| Operación | Contrato |
|---|---|
| `POST /api/cycles` | Bearer privado, cliente loopback, sin Origin; cuerpo máximo 4 KiB y campos adicionales prohibidos. 202 nuevo; 200 repetido; 409 conflicto, agenda deshabilitada o ventana no admitida |
| `GET /api/cycles/{id}` | Misma autenticación; consulta de estado y referencias, sin corpus financiero |
| `GET /api/automation/status` | Estado resumido local para la interfaz; no expone credenciales |
| `POST /api/universe/automation/control` | Control local/origen permitido: propietario `n8n` o `disabled` |
| `POST /api/universe/automation/cycles/{id}/cancel` | Cancela solo el ciclo indicado y sus tareas SEC; no modifica trabajos manuales ajenos |

Presupuesto fijo: seis tareas SEC (submissions/companyfacts de tres CIKs), tres construcciones contables, cero llamadas LLM, coste obligatorio cero y plazo de 20 minutos. Las seis tareas pueden reintentar hasta tres intentos con la política existente de cuota/backoff; no equivalen a una garantía de seis conexiones HTTP ante fallos. Una petición no puede aportar empresas adicionales, URLs, código, instrucciones a agentes ni operaciones de trading. Un solo ciclo activo y 10.000 registros máximos, sin borrado automático.

Se admite una nueva solicitud solo para la ventana actual. Los recibos ya guardados se pueden consultar/repetir después, sin volver a ejecutarse. No se acumulan ventanas antiguas: n8n registra `misfirePolicy=skip`. La agenda es documental; no acredita un calendario bursátil. Un ciclo nuevo mientras otro sigue activo se rechaza. Si la cola SEC está ocupada, espera dentro del plazo, sin desplazar el trabajo previo.

## Persistencia y recuperación

Migración aditiva **0013_shadow_cycles**: `cycle_agendas` y `automation_cycles`. Backup privado `output/b25-before-0013.db`. Las **38 tablas anteriores** conservan conteos y hashes tras migrar; integridad y claves foráneas correctas. Los estados son QUEUED → FETCHING → REVIEWING → SUCCEEDED/PARTIAL, además de BLOCKED, CANCEL_REQUESTED, CANCELLED y TIMED_OUT.

La creación del job SEC y el avance del ciclo se confirman en una sola transacción. Los recibos y snapshots usan el almacenamiento existente; las tareas conservan sus leases y tokens. La revisión fija los snapshots obtenidos y una fecha de corte. Cada modelo tiene una clave idempotente: una interrupción después de guardarlo y antes de confirmar el avance devuelve ese mismo modelo al reanudar. La actualización del checkpoint evita sobrescribir uno posterior. El outbox SEC existente sigue procesando nuevas evidencias.

Cancelar invalida inmediatamente los tokens de tareas pendientes/en curso, y el worker confirma el estado del ciclo. Una respuesta HTTP que ya está viajando puede acabar de descargarse, pero su commit queda rechazado tras esa invalidación. Un GET recibido antes de una caída y aún sin commit puede necesitar repetirse; la garantía de no duplicar resultados corresponde al estado persistido. El plazo vencido cancela el trabajo propio; los errores de configuración/derechos bloquean el ciclo. No se pierde el registro ni se borra la base para recuperarse.

Pausar impide aceptar nuevos ciclos. Los ya aceptados pueden terminar y disponen de cancelación individual. No funciona con el equipo apagado. Tras un reinicio se conserva el estado, se respetan los leases y se verifica el plazo; no se fuerza la finalización de un ciclo ya caducado.

## Prueba real

El flujo real de n8n se ejecutó desde su CLI y consultó el resultado. Creó **un ciclo, un job SEC y seis recibos**. Resultado contable: Apple v6 PASSED, Microsoft v5 PASSED, Walmart v5 PARTIAL. La actualización conserva los **13 modelos anteriores** y deja 16 modelos en total. El estado del ciclo es PARTIAL por las carencias de su revisión contable; no se presenta el éxito de transporte de n8n como aceptación financiera completa. El ratio pasivos/activos de Walmart sigue pendiente.

Una segunda ejecución real de n8n, con otra correlación, recuperó el mismo ciclo: mismos modelos, eventos, jobs y recibos. Después de reiniciar el backend, el reenvío autenticado también devolvió el mismo resultado. Ledger y cartera conservan sus huellas. Las valoraciones rutinarias de arranque del backend siguen su comportamiento previo; no son órdenes ni cambios de posición.

La publicación y el registro persistido del scheduler se comprobaron el 06-11: workflow activo, cron `0 0 */6 * * *` y zona UTC. En esa primera comprobación las dos ejecuciones completas observadas fueron iniciadas con el CLI real de n8n. La verificación automática del 07-11 se detalla a continuación.

### Cierre del temporizador — 07-11-2026

Una agenda temporal del mismo workflow produjo un disparo a las **09:22 UTC / 10:22 Madrid**. Se observaron la tarea del scheduler `succeeded` y la ejecución n8n `4`, modo `trigger`, `success` (09:22:21–09:22:41 UTC). JAIME recibió un segundo ciclo y terminó la revisión: **Apple v7 PASSED, Microsoft v5 PASSED, Walmart v6 PARTIAL**. Hay 18 modelos; los 16 previos mantienen exactamente sus huellas y también ledger, asientos y cartera. Microsoft reutilizó su modelo. Estas versiones de revisión no se presentan como nuevos filings.

La hora temporal inicial venció con n8n detenido; se reprogramó conservando la evidencia. El scheduler necesita terminar su inicialización antes de consultar la agenda vigente. Tras observar el ciclo completo se restauró el JSON original de seis horas. La prueba valida el disparador real con una hora acotada, no un periodo de funcionamiento ininterrumpido de varios días. Evidencia privada: `output/b25-schedule-check.json` y `output/b25-final-runtime.json`.

Verificación final a las 10:26 de Madrid: publicación original contrastada con nodos/conexiones y referencias de credencial, cron `0 0 */6 * * *` activo en UTC, siguiente ejecución 07-11 a las **13:00 Madrid**. Backend, interfaz y n8n responden HTTP 200 y sus puertos solo escuchan en 127.0.0.1; órdenes HTTP 403. Totales: dos ciclos, cinco jobs SEC, 232 recibos, tres eventos de actualización y 18 modelos. La comparación de huellas preserva todos los modelos previos y el ledger/cartera. El catálogo MCP opcional queda desactivado y el log final no contiene sus consultas ni secretos de coordinación.

En **Sistemas → Casos y entregas** se muestra un panel compacto con estado, resultados por empresa, pausa/reanudación y cancelación. Diferencia «solicitudes habilitadas» de un proceso n8n comprobado: la UI no inventa un heartbeat del coordinador. Pruebas de navegador con API real: resultado parcial visible, pausa/reanudación, ocultación de controles ante desconexión, 1366/390 px y ausencia de errores JavaScript/desbordamiento. Capturas privadas en `output/playwright/b25/`.

## Verificación y operación

`manage.py check` final: **485 pruebas backend y 98 frontend superadas**, una omisión frontend preexistente; TypeScript/build correctos. Las 17 pruebas de ciclos cubren concurrencia, rollback al despachar, interrupción tras guardar un modelo, cancelación de una descarga en curso, timeout, cola ocupada, replay, permisos, ventana y cuerpos inválidos. Tres pruebas de interfaz comprueban estados veraces y controles. La primera ronda completa detectó el inventario antiguo de rutas OpenAPI; fue actualizado junto con el esquema de solicitud. La primera ejecución de n8n detectó una expresión incompatible; se corrigió y se añadió validación con su parser antes de importar.

Autenticación independiente generada en `.env`, credencial cifrada en n8n, proceso sin claves heredadas de proveedores. El flujo contiene solo cinco tipos de nodo permitidos. No hay herramientas de broker, gasto, Redis ni despliegue público. El bloqueo `POST /api/orders=403` continúa comprobado; P4 PARTIAL. Avisos preexistentes de httpx/TestClient y chunk 3D. El 07-11 se desactiva el módulo opcional `mcp-registry` para evitar sus consultas al catálogo externo. Persisten avisos de un runner Python ausente y futuras deprecaciones de n8n, sin uso de Python/Code en este flujo; ver el runbook. La suite completa indicada corresponde al 06-11; el 07-11 se verifica la integración del temporizador y el estado final de los servicios.

Evidencia privada: `output/b25-migration.json`, `output/b25-real-cycle.json`, `output/b25-readiness.json`, `output/b25-browser.json`, `output/b25-full-check.log` y logs de n8n. El token se comprobó ausente de logs y entregables. Runtime aproximado **2,18 GB**, más base n8n y caché npm. [Arranque, configuración, lock y límites](../../integrations/n8n/README.md).

## Continuación

B2.5 queda cerrado dentro de este piloto. B2 sigue abierto: el siguiente trabajo es el pendiente B2.3 de identidad SEC–instrumento–listing y admisibilidad de históricos para la primera familia diaria de B3. Streaming, retención/presupuesto agregado, valoración y ampliación de cobertura conservan sus límites. Un filing nuevo sin documentos XBRL archivados puede producir un modelo parcial: este flujo no añade una descarga masiva de archivos de estados ni convierte esos modelos en datos listos para backtest.
