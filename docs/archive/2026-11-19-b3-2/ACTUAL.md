# Entrega activa — B3.2 · primera campaña real, pendiente de datos

18-11-2026, Europe/Madrid. Cierre de la implementación y pruebas realizadas el 17-11. [D3 implementado](../../actual/ENTREGA_D3_ADMISION.md): validadores deterministas, loaders read-only y manifiestos inmutables por CLI. Registro confiable real vacío; **ningún dataset real admitido**. El fixture positivo es ENGINEERING_ONLY. [Ficha D3 preservada](../../archive/2026-11-17-d3/ACTUAL.md) · [Cola única](../../../tasks/ROADMAP.md).

## Punto de continuación del 18-11

[Preparación concreta B3.2](../../actual/B3_2_PRIMERA_CAMPANA.md) y [protocolo v1](../../actual/B3_2_PROTOCOLO_v1.json) fijados: candidato BRK.B / Alpaca IEX, últimas 252 sesiones hasta 31-12-2025, calentamiento común 60, SMA20/40/60 y controles efectivo/comprar-mantener, dos escenarios de coste; 10 ensayos previstos, cero ejecutados.

El usuario confirma cuenta real Alpaca además de Paper. Uso personal/backtesting respaldado en documentación general, pero copia persistente y reutilización local pendientes de aclarar frente al §30 del contrato público: `RIGHTS_SCOPE_UNRESOLVED`, no prohibición universal. [Consulta lista, sin enviar](../../actual/B3_2_CONSULTA_ALPACA.md). Reanudar con condiciones aplicables o respuesta concreta del proveedor, no con otra auditoría general ni más infraestructura. No habilitar descarga por un simple acceso HTTP correcto.

D050 especifica un alcance retrospectivo explícito, separado de validación PIT/OOS: no inventar publicación histórica por barra ni elección del universo anterior al periodo. **El protocolo todavía no está implementado en D3/quant.** Sus validadores actuales y el registro vacío se conservan. Tras resolver derechos, completar el dataset y adaptar únicamente lo necesario para su admisión y los 10 ensayos. El control comprar/mantener deberá respetar el calentamiento común.

## Primer requisito: resolver un dataset concreto

El instrumento/periodo candidato ya está fijado en el protocolo. Reunir evidencias revisables de identidad constante, calendario, acciones corporativas, cronología, universo y derechos del uso concreto. El registro confiable exige revisión; un JSON de usuario o el acceso a un feed no concede derechos. IBKR conserva su bloqueo de archivo. Si falta evidencia, conservar el rechazo con razones y no iniciar campaña.

Usar `scripts/admit_dataset.py` como ruta canónica: `history` para snapshots D2, `market` para archivo Alpaca y `show` para inspeccionar el manifiesto. El diagnóstico legacy de UI no sustituye esta admisión. No crear D3.1 ni más infraestructura de motor antes de la campaña; no añadir proveedores para aparentar cobertura.

## Campaña, solo cuando el dataset esté admitido

Ejecutar el protocolo fijado, sin volver a elegir parámetros tras observar resultados; registrar todos los ensayos, fallos y descartes. Todo el intervalo evaluado queda marcado como exploratorio ya observado, sin OOS reservado. El mínimo preliminar de 252 sesiones (60 de calentamiento, 192 útiles) no equivale a aceptación estadística. Resultados exploratorios separados de aceptación B4; cero candidatos aptos es válido.

## Aceptación y punto de parada

- Manifiesto concreto admitido por los gates aplicables, con evidencia confiable y alcance explícito, antes de minería real.
- Campaña reproducible y acotada con registro total de pruebas y limitaciones; B4/riesgo/OMS conservan sus gates.
- Sin UI nueva, descargas no autorizadas, órdenes ni cambios MASTER. PAPER ONLY, 0 EUR y P4 PARTIAL vigentes.

Si los derechos/evidencias siguen sin resolverse, documentar el bloqueo concreto; no declarar conseguida la campaña ni admisible un dataset por haber terminado D3.
