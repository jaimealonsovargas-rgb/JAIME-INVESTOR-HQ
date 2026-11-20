# B5 · Decisión de riesgo en el ciclo autónomo

20-11-2026, Europe/Madrid. **BRK.B queda en observación.** Las tres hipótesis de B4 se descartaron y el ciclo registró cero propuestas y cero órdenes. Se puede ver el motivo en Sistemas → Casos y entregas → Detalle del ciclo. [Sistemas](http://127.0.0.1:5173/?especialista=personal-systems) · [Mandato de B5](../archive/2026-11-20-b5/ACTUAL.md) · [Origen B4](ENTREGA_B4.md).

## Verificación con el ciclo publicado

n8n entregó la ventana del 20 de noviembre de 07:00 a 13:00 de Madrid. A las **11:29:10** JAIME verificó el expediente privado de B4 y guardó `OBSERVE / NO_CANDIDATES`. Al repetir la solicitud con otra correlación, la API devolvió HTTP 200, `duplicate=true` y el mismo recibo. La revisión contable de esa ventana generó Apple v8 y Microsoft v6 con controles superados y Walmart v7 con pendientes. El ciclo contable terminó en `PARTIAL`.

| Registro local | Identificador |
|---|---|
| Expediente B4 | `5b3f92b437746935f3a4d58991c84962e5f1f2dd7f774083659b66fbe5a35421` |
| Ventana de n8n | `6f35f80d4be289f19752bfc8789345b6c27c5441a3d942e5fbda471d4854c09c` |
| Decisión guardada con la política inicial v1 | `91789760c724d36cb579bd14e7b5617190b473537b63a1da1f5ccd299b259101` |
| Política PAPER v2 activa tras la revisión de Day Trader | `3692abe36657123b854acc283a1ada8c7f6e32b9935e0269d0890383dd1f7fdc` |

La política v2 reprodujo la misma observación usando el expediente, la ventana y el instante originales. Cambiaron las referencias a la política y el identificador del cálculo. El recibo persistido de v1 sigue siendo el original. El estado de la API expone la política activa y cada decisión conserva la suya. [Estado local](http://127.0.0.1:8000/api/automation/status).

## Controles PAPER

Se evalúan propuestas largas, por acciones enteras y en una sola divisa por cuenta. Una compra o venta requiere una candidata seleccionada con evidencia temporal independiente, un paquete revisado del comité, cuenta simulada reconciliada, precios vigentes, liquidez y sesión elegible. Las entradas con referencias de contenido incorrectas, expedientes caducados o datos incompletos se detienen con un motivo. Las pruebas favorables de compra y venta usan datos ficticios aislados.

| Control de ingeniería | Política inicial del simulador |
|---|---|
| Capital y concentración | Reserva en efectivo del 10 % del patrimonio. Exposición bruta hasta el 80 %, por emisor 15 %, sector 35 % y factor 50 %. |
| Propuestas y rotación | Una propuesta hasta el 5 % del patrimonio. Rotación diaria hasta el 25 % y diez órdenes abiertas como máximo. La evaluación reserva capacidad en el orden fijado por el expediente. |
| Liquidez | Diferencial máximo del 0,5 %. Participación agregada pendiente por instrumento hasta el 0,5 % del volumen medio diario. Margen de costes del 0,2 % por lado. |
| Pérdidas | Se bloquean compras desde el 3 % de pérdida diaria o el 10 % de caída desde máximos. En v2, la pérdida estimada del instrumento al precio de salida estresado admite hasta el 0,5 % del patrimonio. |
| Vigencia | Hasta 60 s para la cuenta, 30 s para las cotizaciones y siete días para la estadística de liquidez. El recibo de cada caso vence al primero de los límites aplicables, incluida la expiración del comité. |
| Recursos | Un evaluador local por ventana. Un expediente de hasta 4 MiB y un paquete de hasta 1 MiB. Hasta 32 propuestas y 256 instrumentos. Una evaluación que alcanza cinco segundos pierde su validez. Cero llamadas de red o de IA en el motor de riesgo. |

Los límites son provisionales para ingeniería PAPER. El cálculo de pérdida utiliza el precio de una salida adversa y costes en ambos sentidos. Incluye las acciones ya poseídas, las compras pendientes y las aceptadas durante el lote. La pérdida efectiva podría superar la estimación si la salida se produce a peor precio. El recibo registra la cantidad máxima según este control y el motivo si se veta la cantidad solicitada. [Adaptación de Day Trader](DAY_TRADER_ADAPTACION.md).

## Persistencia y recuperación

La reserva de ventana y su decisión de riesgo se confirman juntas en SQLite. Un fallo antes de confirmar permite el reintento. Después de confirmar, los duplicados recuperan la decisión guardada. El trabajador SEC puede reanudar la captación y la revisión contable conservando el resultado de riesgo. Los ciclos históricos que preceden a B5 siguen consultables.

Pasaron las **853 pruebas del backend** y las **115 de la interfaz**, incluida la consulta de solo lectura a JAIME encendido. La compilación de producción terminó correctamente. Se comprobó en un navegador la vista de Sistemas y el motivo de observación. El proceso de n8n quedó con su flujo publicado y su agenda activa.

La comparación de las cuatro tablas de MASTER inmediatamente antes y después del ciclo real dio los mismos recuentos y huellas. La prueba HTTP de `POST /api/orders` devolvió **403**. El modo operativo continúa en PAPER, el coste externo obligatorio es de 0 EUR y P4 sigue PARTIAL. Próximo hito en B6, simulación local del contrato de órdenes, envíos con resultado desconocido y reconciliación. [Ficha activa](../../tasks/ACTUAL.md).
