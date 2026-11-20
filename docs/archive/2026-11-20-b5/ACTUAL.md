# Próxima entrega única · B5, autonomía y riesgo

19 de noviembre de 2026. B4 entregó un expediente verificado para los diez ensayos BRK.B/IEX. El resultado es `NO_CANDIDATES`, con cero candidatos y acción `OBSERVE`. P4 continúa en PARTIAL. [Entrega B4](../../actual/ENTREGA_B4.md) · [Mandato B4 archivado](../2026-11-19-b4/ACTUAL.md) · [Hoja de ruta](../../../tasks/ROADMAP.md).

## Entrada real

Revisión del 20-11-2026. El expediente B4 se reprodujo con el mismo identificador. El piloto de optimización utiliza datos sintéticos y se mantiene separado de la entrada real a riesgo. [Comparación de los cinco repositorios y ampliación prevista de minería](../../actual/MINERIA_REPOS_2026_11_20.md).

El primer ciclo de B5 puede ejercitarse con la decisión de observación que ya existe. El lector local de B4 comprueba el expediente por su identificador. Si está ausente, alterado, incompleto o caducado para el uso solicitado, el ciclo debe registrar el motivo y abstenerse de generar una propuesta operativa. El detalle de vigencia corresponde al tipo de evidencia y a la decisión de riesgo.

## Trabajo del bloque

1. Conectar la lectura del expediente con el ciclo autónomo existente de JAIME/n8n. Registrar el identificador de origen, decisión, vencimiento y motivo. Recuperar y deduplicar ciclos ante reintentos o interrupciones.
2. Desarrollar el motor de riesgo determinista para propuestas PAPER con controles de capital, exposición, concentración, liquidez, vigencia y disponibilidad de los datos. Dar trazabilidad a la decisión y al veto. Los casos aptos y los fallos del contrato pueden probarse con fixtures.
3. Verificar los presupuestos de recursos, los límites de concurrencia y la recuperación del trabajo autónomo en el ámbito de este bloque. Mantener el caso BRK.B en observación y las pruebas de propuestas separadas de MASTER.

## Punto de parada

B5 termina al demostrar un ciclo repetible desde la evidencia hasta la decisión registrada de riesgo u observación. B6 se ocupa del OMS, los fills y la reconciliación de Alpaca PAPER. El expediente actual permite avanzar en B5 con 0 EUR de coste externo. La ampliación de minería a más hipótesis y activos requiere sus propios datos admisibles y una muestra reservada de antemano.
