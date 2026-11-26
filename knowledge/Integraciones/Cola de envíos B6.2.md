---
tipo: integración
revisado: 2026-11-25
---

# Cola de envíos B6.2

**Entregada el 25 de noviembre de 2026.** La intención aprobada, la reserva y la entrada pendiente se confirman en una transacción de la base privada de [[Simulador local B6.1]]. Cada intento de envío lleva su propio identificador y una reclamación de diez segundos.

Cuando vence una reclamación o se pierde una respuesta, el trabajador consulta el identificador estable **antes de reintentar**. La incertidumbre conserva la reserva. Si el simulador confirma la ausencia, una intención aún vigente debe superar de nuevo los controles de riesgo.

El formato 2 admite bases de laboratorio del formato 1. Los tres escenarios publicados de caída o pérdida de respuesta comparten la huella `c4a5240b1b26e1893ae04d98eb3bdfb07c9178901ae7bf61fd79634de51f2d8b`. El historial de envíos alimenta [[B6.3 Conciliación del simulador]]. [Entrega y evidencia de recuperación](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/blob/bf4a5b9d61071a94228f529876eb33d1bf18d3db/docs/actual/ENTREGA_B6_2.md).
