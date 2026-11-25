# Próxima entrega · B6, conciliación de ejecuciones y posiciones

El simulador conserva las intenciones, las reservas y el historial de envío. La siguiente entrega debe contrastar lo registrado localmente con las ejecuciones y posiciones de la cuenta ficticia. [Cola de envíos](../docs/actual/ENTREGA_B6_2.md) · [Mandato anterior](../docs/archive/2026-11-22-b6-cola/ACTUAL.md) · [Hoja de ruta](ROADMAP.md).

## Qué entregar

1. Contrastar las ejecuciones del simulador por identificador y orden. Recuperar notificaciones perdidas y contabilizar una sola vez las repetidas.
2. Reconstruir las cantidades ejecutadas y las posiciones a partir de la cuenta inicial, incluidas las ejecuciones parciales seguidas de cancelación. Identificar diferencias pendientes de resolver.
3. Ensayar el reinicio durante la conciliación y la repetición sobre los mismos datos. Documentar los saldos y las diferencias observadas antes y después.

## Punto de parada

El hito termina con evidencia reproducible de la conciliación en la cuenta ficticia y de la integridad de MASTER. La apertura a Alpaca PAPER corresponde a una entrega posterior. Siguen vigentes el coste externo de 0 EUR y el bloqueo HTTP 403 de las órdenes públicas.
