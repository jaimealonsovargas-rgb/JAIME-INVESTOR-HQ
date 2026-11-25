# B6.2 · Cola durable de envíos PAPER

La entrada de envío comparte la transacción SQLite con la intención aprobada y su reserva. La repetición de un recibo admitido recupera los mismos identificadores. Las decisiones de observación, veto o mantener producen cero envíos.

## Entrega y recuperación

El trabajador reclama una entrada durante diez segundos y registra el intento con su propio token. Antes de entregar la orden al simulador, comprueba el riesgo y la caducidad. El identificador de la orden permanece estable entre intentos. El diario distingue el intento de entrega y el evento registrado por el simulador.

Si caduca la reclamación o se pierde la respuesta, el trabajador consulta el identificador antes de volver a enviar. Una consulta inconcluyente mantiene la reserva. Cuando el simulador confirma la ausencia, la orden puede volver a intentarse si sigue vigente y supera la comprobación de riesgo.

## Almacenamiento y reproducción

El formato 2 de la base privada del simulador incorpora la cola y migra las bases del laboratorio en formato 1. El destinatario de la entrega es el simulador local. La conciliación de ejecuciones y posiciones precede a la futura apertura de Alpaca PAPER.

La sonda reproducible está en [scripts/probe_paper_outbox.py](../../scripts/probe_paper_outbox.py). [Contrato del simulador](ENTREGA_B6_1.md) · [Mandato archivado](../archive/2026-11-22-b6-cola/ACTUAL.md) · [Próxima entrega](../../tasks/ACTUAL.md).

## Verificación del 25 de noviembre de 2026

El ciclo que n8n inició a las 13:00 de Madrid (`n8n:14`) produjo el recibo de riesgo `70f276b76883bc24113c2023e648d91604b96163e181a12d63617cd795273e9c`. BRK.B siguió en observación. La cola registró **cero intenciones y cero envíos**.

| Fallo introducido en la cuenta ficticia | Recuperación registrada |
|---|---|
| El simulador acepta la orden y se pierde la respuesta | Una consulta encuentra la orden aceptada. |
| El proceso cae tras reclamar el trabajo y antes de entregarlo | Una consulta confirma la ausencia. El siguiente intento envía la orden una vez. |
| El proceso cae después de entregar y antes de confirmar la cola | Una consulta confirma la aceptación y cierra la entrada pendiente. |

Los tres escenarios dan la huella `c4a5240b1b26e1893ae04d98eb3bdfb07c9178901ae7bf61fd79634de51f2d8b`. En una prueba adicional se terminó un proceso inmediatamente después de una ejecución parcial de cuatro acciones. El siguiente trabajador recuperó esa cantidad. El aviso tardío también dejó el total en cuatro. Las pruebas de migración cubrieron seis estados de órdenes que ya existían en el formato 1.

Desde la raíz del proyecto, el modo predeterminado procesa una tanda y termina. El modo continuo revisa nuevos recibos y recupera los pendientes mientras el proceso está activo. Tras reiniciar Windows, el mismo comando retoma la base conservada en disco.

```powershell
.\.venv\Scripts\python.exe scripts/probe_paper_outbox.py --cycle latest
.\.venv\Scripts\python.exe scripts/probe_paper_outbox.py --demo
.\.venv\Scripts\python.exe scripts/probe_paper_outbox.py --continuous --worker hq-b6-local --poll-seconds 5
```

Pasaron las **910 pruebas del backend**, incluidas **23 específicas de la cola**, y las **115 de la interfaz**. La compilación de producción terminó correctamente. Durante la primera ejecución en paralelo, la consulta de la interfaz al resumen de la sede superó su límite de cinco segundos. La suite completa de interfaz pasó al repetirla con dos trabajadores y acceso a localhost.

Las cuatro tablas de MASTER conservaron sus recuentos y huellas antes y después de la prueba con el recibo real. La web, la API y n8n respondieron en localhost. `POST /api/orders` devolvió HTTP 403. El trabajador local quedó activo con un intervalo de cinco segundos.
