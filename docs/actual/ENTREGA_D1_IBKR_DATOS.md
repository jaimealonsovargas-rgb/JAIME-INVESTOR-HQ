# D1 — acceso a datos IBKR comprobado

16-11-2026, Europe/Madrid. **D1 terminado con acceso observado**: la sesión Paper existente devolvió histórico diario y una cotización diferida para AAPL, contrato 265598. No se habilita un proveedor continuo ni se certifica cobertura de otros instrumentos. Próximo: D2, captación por lotes; [ficha activa](../../tasks/ACTUAL.md).

## Evidencia real

Prueba terminada el 16-11 a las **13:06:18 Europe/Madrid**. Cuenta única Paper cotejada por hash privado, servidor 226, reloj contrastado, SDK aislado 1052.1. Sin cuentas en claro ni secretos en el informe.

| Petición | Resultado |
|---|---|
| Histórico `5 D`, `1 day`, `TRADES`, RTH, fin 16-11 00:00 UTC | Cinco barras: 9, 10, 11, 12 y 13 de noviembre; OHLCV coherente en memoria, ordenadas y final de respuesta recibido |
| Snapshot ordinario, `regulatorySnapshot=False`, solicitado tipo 3 | Callback confirmó **tipo 3 diferido** y ticks bid/ask/last 66/67/68; final recibido |
| Fecha del último negocio / recepción | 12:51:11 / 13:06:18 Madrid: **907,31 segundos** de antigüedad; no es la hora de cada bid/ask |
| Coste/control | Sin contratar servicios ni usar snapshots regulatorios facturables; no se ha auditado la facturación preexistente de la cuenta |
| Transporte | 2.042 bytes recibidos; mensajes `[71,49,59,20,1,2]`; desconexión confirmada |
| Archivo | Solo diagnóstico, fechas, códigos, contadores y huella de evidencia; **ningún precio/barra cruda persistido**, ninguna escritura SQLite |

Informe privado: `output/ibkr-data-probe-20261116-r2.json`; SHA-256 `1d1af47f0a500db336fa0c9eecd81a0cc3b9d8bb7eb13d216a51622d760280f6`. Validación y hashes de fuentes: `output/d1-validation-20261116.json`.

## Qué se ha implementado

[Cliente aislado](../../scripts/ibkr_data_probe.py), [política pura](../../backend/app/ibkr_data_policy.py), pruebas [de política](../../backend/tests/test_ibkr_data_policy.py), [del proceso padre](../../backend/tests/test_ibkr_data_runner.py) y [del SDK](../../integrations/ibkr/test_data_offline.py). Se conserva intacto el cliente previo de contratos.

- Localhost/7497/client 27 y coincidencia exacta de cuenta de simulación antes de cualquier consulta. El ajuste Read-Only procede de la configuración previa confirmada; no se infiere del puerto. El guard de mensajes excluye toda orden independientemente de ese ajuste.
- Allowlist separada de siete comandos de lectura/cancelación de datos; los métodos fijan contrato y parámetros. Tanto legacy como Protobuf rechazan mensajes fuera del contexto permitido, incluso IDs de datos enviados directamente; máximo una emisión por ID. No se permite el snapshot regulatorio.
- Una historia y una cotización por ejecución, sin reintentos automáticos. Presupuesto de recepción 128 KiB (lectura en bloques de hasta 4 KiB, detección al superar), ocho barras como máximo y 64 callbacks de precios; informe máximo 32 KiB. Plazo de trabajo 55 s, padre 70 s, cancelación/desconexión al terminar. No es una cuota general de IBKR.
- Antes de conectar, StorageGovernor reserva 1 MiB. Si otra tarea escribe, se informa `STORAGE_BUSY` y no se lanza el SDK. Un proceso expirado, salida inválida o exceso de respuesta produce diagnóstico y código de salida no exitoso.
- El callback, no el feed solicitado, determina la modalidad observada. Se conserva la diferencia entre instante del dato y recepción; fecha diaria es etiqueta de sesión, no publicación histórica ni disponibilidad PIT.

## Hallazgo y corrección durante D1

Una primera ejecución fue aplazada por reserva ocupada, sin conexión. La primera respuesta real reveló dos defectos del comprobador: el aviso **2188** activaba la finalización prematura, y cinco días naturales no cubrían las sesiones diarias devueltas. Se preserva `output/ibkr-data-probe-20261116.json` como intento fallido, no como prueba de que IBKR carezca de datos.

Corrección: 2188 se conserva como aviso sobre acceso al histórico más reciente y se espera `historicalDataEnd`; no se suprime una denegación 162. Para el diagnóstico diario, se comprueban fechas anteriores al fin, orden/unicidad, precios y OHLCV con un margen de seguridad de 14 días naturales y máximo ocho barras. **El calendario de mercado y la interpretación exacta del periodo siguen pendientes de D3.** La repetición r2 recibió las cinco sesiones completas, sin errores de petición. Se añadieron pruebas de regresión antes de repetir.

## Fuentes oficiales y límites de derechos

La [FAQ actual de IBKR](https://www.interactivebrokers.com/support/faq/content/tws-api-compatible-delayed-data-29091333) permite históricos diferidos cuando están disponibles. La [documentación antigua](https://interactivebrokers.github.io/tws-api/historical_data.html) exigía suscripción en todos los históricos. D1 registra la discrepancia y la respuesta real; no extrapola disponibilidad a toda la cuenta o mercado.

El [catálogo oficial de errores](https://www.interactivebrokers.com/docs/tws-api/doc/error/codes) describe 2188 como requisito de suscripción para histórico al segundo. Su recepción junto a barras completas se registra como aviso de histórico diferido, no como medida exacta del retraso de cada barra. Los [tipos de datos](https://www.interactivebrokers.com/docs/tws-api/doc/md/delayed-data) distinguen diferido, frozen y live; el tipo 3 está confirmado por callback en esta prueba.

La [especificación de barras](https://www.interactivebrokers.com/docs/tws-api/doc/md/historical-bars) distingue sesiones diarias, actualizaciones y ajustes: `TRADES` ajusta splits, no dividendos. No equivale a precios brutos para fills ni a retorno total. Las [limitaciones de mercado](https://www.interactivebrokers.com/docs/tws-api/doc/md/market-data-limitations) advierten sobre revisiones/filtrado, valores retirados y cambios de plaza. ConId actual no acredita identidad durante toda la historia.

**Acceso técnico observado; derechos de archivo/minería masivos todavía no verificados para la cuenta y el dataset.** No se inventa una licencia por poder consultar. D1 procesa precios en memoria y conserva exclusivamente diagnóstico privado; no redistribuye datos ni habilita almacenamiento de precios. D2 debe resolver/registrar alcance y retención antes de persistir datos del proveedor; si no puede, conserva el bloqueo explícito y construye la cola con fixtures. No cambia automáticamente a otra fuente.

## Aceptación y parada

**64 pruebas distintas pasadas:** 21 política/padre D1, 9 SDK aislado, 10 política previa de contratos y 24 evaluación de datasets. La primera tanda fue 49 backend; tras las correcciones se repitieron los 15 afectados y se añadieron seis pruebas del padre. Logs `output/d1-policy-tests.log`, `d1-policy-tests-final.log`, `d1-sdk-tests-final.log`. Aviso preexistente de deprecación Starlette/httpx, sin fallos finales.

Huella y recuentos de **12 tablas protegidas idénticos** antes/después: 18 modelos, MASTER, histórico de mercado y ensayos B3.1 incluidos. Base permanece `0014_quant_lab`; salud correcta, MASTER NAV/efectivo 10.000 EUR ficticios, cero posiciones, **POST /api/orders=403** comprobado contra el backend. No migración, nuevas copias de base, cambios visuales ni reinicio de servicios.

Parada D1: acceso demostrado con límites, sin pasar a D2 en esta entrega. IBKR sigue en la ruta de datos; SEC conserva cuentas y Alpaca PAPER la ejecución futura. P4 PARTIAL, coste obligatorio cero, BACKTEST_READY y ejecución deshabilitados. Cinco barras son una prueba de integración, no un límite de universo ni suficiente historial para minería.

Reproducción manual, con TWS Paper abierto y un archivo de salida nuevo:

```powershell
& ./.venv/Scripts/python.exe -B scripts/ibkr_data_probe.py --output output/ibkr-data-probe-NUEVA-FECHA.json
```

No programar este diagnóstico repetidamente: D2 implementará captación y cuotas compartidas.
