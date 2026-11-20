# Próxima entrega · B6, simulador de órdenes PAPER

20 de noviembre de 2026. B5 ya registra decisiones de riesgo en cada ventana de n8n. La evidencia BRK.B vigente entrega observación. [Entrega B5](../docs/actual/ENTREGA_B5.md) · [Mandato B5 archivado](../docs/archive/2026-11-20-b5/ACTUAL.md) · [Hoja de ruta](ROADMAP.md).

## Primer paso de B6

1. Definir la intención de orden y una clave estable vinculada a una decisión de riesgo, instrumento, lado y cantidad. Comprobar el vencimiento y las reservas al consumir una decisión. El recibo real de observación produce cero intenciones.
2. Ejercitar un simulador local de broker con aceptación, rechazo, respuesta perdida, duplicado, fill parcial y cancelación. Conservar el identificador de cada intento y distinguir un estado desconocido mientras se reconcilia.
3. Comprobar que los mismos eventos, repetidos o tras reinicio, producen una sola intención y el mismo estado final. Usar una cuenta de prueba separada de MASTER.

## Punto de parada

El primer hito de B6 termina con el contrato y el simulador verificados. Las entregas posteriores cubren la cola durable de envíos, la reconciliación y la apertura controlada a Alpaca PAPER según la hoja de ruta. Siguen vigentes el coste externo de 0 EUR, el bloqueo de LIVE y el 403 del endpoint público de órdenes.
