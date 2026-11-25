# Próxima entrega · B6, cola durable de envíos PAPER

22 de noviembre de 2026. El simulador local ya identifica cada intención, reserva capital o acciones y recupera los intentos ambiguos. El ciclo real de BRK.B sigue en observación. [Entrega del simulador](../../actual/ENTREGA_B6_1.md) · [Mandato anterior](../2026-11-22-b6-simulador/ACTUAL.md) · [Hoja de ruta](../../../tasks/ROADMAP.md).

## Qué entregar

1. Guardar la intención validada, su reserva y la entrada de envío en una misma transacción. La repetición de un recibo debe recuperar la misma entrada. Una decisión de observación, veto o mantener produce cero envíos.
2. Incorporar un trabajador local que reclame los envíos pendientes por tiempo limitado. Registrar cada intento y comprobar riesgo y caducidad antes de entregarlo al simulador con su identificador original.
3. Ensayar caídas antes y después de la entrega, reinicio y dos trabajadores competidores. Si se pierde la respuesta, consultar primero el identificador. Comprobar que un envío ambiguo conserva la reserva y que la recuperación nunca duplica una ejecución.

## Punto de parada

Este hito termina cuando la cola se recupere por sí sola frente al simulador, con evidencia reproducible de los tres casos y de la integridad de MASTER. La siguiente entrega cubrirá la conciliación de ejecuciones y posiciones. El conector de Alpaca PAPER se habilitará en una entrega posterior, sujeta a los controles de la hoja de ruta. Coste externo de 0 EUR y órdenes públicas con HTTP 403.
