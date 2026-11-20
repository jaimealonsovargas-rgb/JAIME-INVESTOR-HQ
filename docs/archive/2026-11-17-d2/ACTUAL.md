# Ficha histórica — D2 · captación histórica por lotes

> Archivada el 17-11-2026 tras la entrega D2. No es una tarea activa; la continuidad está en [ACTUAL](../../../tasks/ACTUAL.md).

16-11-2026. **D1 terminado:** sesión IBKR Paper cotejada; cinco barras diarias AAPL y cotización diferida tipo 3 recibidas. Diagnóstico en memoria, sin archivar precios ni habilitar backtest. 64 pruebas distintas pasadas; 12 tablas protegidas/MASTER intactos. [Entrega D1](../../actual/ENTREGA_D1_IBKR_DATOS.md) · [Ficha anterior](../../archive/2026-11-16-d1/ACTUAL.md) · [Cola única](../../../tasks/ROADMAP.md).

## Resultado y punto de parada

Captación histórica recuperable para un universo configurable, con cobertura y fallos por instrumento, sin límite estructural de tres empresas. IBKR sigue en la ruta de datos. Parar al entregar y verificar la cola/adaptador y sus controles; D3 admitirá datasets y B3.2 ejecutará la primera campaña real. No iniciar minería real por haber descargado barras.

## Alcance cerrado

1. Revisar los derechos aplicables al archivo y uso local del dataset concreto. D1 solo verificó acceso técnico: no convirtió la licencia del SDK ni el permiso de consulta en licencia de almacenamiento. Registrar fuente, alcance, evidencia/revisión y retención. Sin evidencia suficiente, bloquear persistencia del proveedor con razón explícita y completar la infraestructura con fixtures. No pagos ni cambios silenciosos de fuente.
2. Definir petición tipada por identidad/contrato fijado, periodo, frecuencia, precio/ajustes y objetivo. Lista/universo configurable del catálogo; no convertir una coincidencia de ticker en identidad histórica. IDs de instrumento/cotización conservados.
3. Cola SQLite durable con idempotencia, ventanas, cursor/checkpoint, pausa/cancelación, lease, timeout, recuperación y reintentos acotados. Reutilizar componentes existentes cuando encajen; una autoridad de programación, sin añadir otra agenda n8n para aparentar autonomía antes de probar el contrato.
4. Adaptador aislado IBKR: presupuesto de peticiones compartido, una sesión/cliente controlado, diferido explícito, sin órdenes y sin snapshot regulatorio. Incorporar 2188 como aviso; distinguir pacing, permisos, ausencia de datos y sesión caída. No repetir pruebas D1 ni reinstalar SDK/TWS.
5. Deduplicar snapshots y procesar por lotes. Cache temporal limitada y separada de evidencia/manifiestos de experimentos. StorageGovernor antes de escribir; no borrar originales actuales ni ensayos perdedores. Plazos de retención condicionados a derechos; evitar almacenar copias por agente/ensayo.
6. Registrar cobertura real: recibidos/pendientes/rechazados, fechas, calidad OHLCV, calendario/gaps y cobertura de acciones corporativas. Si faltan calendario/ajustes/identidad/permiso, declararlo; no simular completitud. TRADES IBKR ajusta splits y no dividendos; no mezclar con otras series sin transformación versionada.
7. Verificación con fixtures de universo amplio, reinicios, duplicados, fallos y presupuesto. Prueba real pequeña solo con derechos y sesión disponibles; demostrar ampliabilidad por diseño y medición, no anunciar miles de activos cubiertos por probar cinco barras.

## Aceptación

- Trabajo recuperable, deduplicado y observable por activo; sin techo de tres instrumentos.
- Una interrupción no pierde ni duplica unidades; errores no provocan bucles sin límite ni gasto.
- Modalidad, periodo, unidades, identidad, origen y limitaciones acompañan al dato. Derechos no verificados bloquean el archivo real.
- MASTER, modelos y ensayos B3.1 intactos; órdenes 403, coste obligatorio cero y P4 PARTIAL. Migración aditiva, si hace falta, ensayada en copia antes de aplicarse.
- Evidencia, STATUS y esta ficha actualizados. Parar antes de D3/B3.2. Nada de obra visual, nuevos proveedores por anticipado ni ejecución PAPER.

## Después

D3: validadores de admisión y manifiesto congelado, con causas reales. B3.2: campaña acotada de tendencia y controles sobre datos admitidos. B4 → B5 → B6 conservan sus gates de validación, riesgo y ejecución. No hay que terminar todo el mercado mundial para probar cada componente, ni se reduce el objetivo a la muestra de regresión.
