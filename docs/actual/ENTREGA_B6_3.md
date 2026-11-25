# B6.3 · Conciliación de ejecuciones y posiciones

25 de noviembre de 2026, Europe/Madrid. La cuenta ficticia permite verificar cada ejecución por su identificador y el de su orden. El trabajador comprueba los recibos aunque la cola ya haya terminado el envío. Una diferencia que el diario no explica queda visible y suspende nuevas admisiones y envíos del trabajador. [Reconciliador](../../backend/app/paper_reconciliation.py) · [Pruebas](../../backend/tests/test_paper_reconciliation.py).

## Una compra parcial seguida de cancelación

La cuenta de prueba abrió con 10.000 USD y cero acciones de `SIM-ONLY`. La orden de compra era de diez acciones. El simulador ejecutó una a 9,98 USD, dos a 9,99 y una a 9,97. El primer aviso llegó dos veces con identificadores de mensaje distintos. Se perdieron los otros dos avisos y la respuesta a la cancelación.

| Momento | Estado local | Acciones locales | Efectivo local USD | Extracto del simulador | Diferencias |
|---|---|---:|---:|---|---|
| Antes de conciliar | Desconocido | 1 | 9.990,02 | 4 acciones y 9.960,07 USD | Dos avisos ausentes, cantidad y estado de orden pendientes |
| Tras interrumpir el proceso en la primera recuperación | Desconocido | 1 | 9.990,02 | 4 acciones y 9.960,07 USD | Las mismas cuatro diferencias |
| Tras reiniciar y conciliar | Cancelada | 4 | 9.960,07 | 4 acciones y 9.960,07 USD | Ninguna |
| Tras repetir y entregar un aviso tardío | Cancelada | 4 | 9.960,07 | 4 acciones y 9.960,07 USD | Ninguna |

El proceso hijo terminó con código 73 después de escribir el primer evento de recuperación y antes de confirmar la transacción SQLite. Al reabrir la base, la comparación conservaba su huella inicial. La recuperación registró `fill-b` y `fill-c`. Las seis acciones pendientes se cancelaron y la reserva final quedó en cero. El segundo pase y el aviso tardío conservaron la misma huella final. [Sonda reproducible](../../scripts/probe_paper_reconciliation.py) · [Resultado completo, por orden y por ejecución](evidencias/b63-conciliacion.json).

| Huella SHA-256 | Valor |
|---|---|
| Antes de la recuperación y tras la caída | `d238088e3ae36aee91109cd2a49591c886578c34cb74bf39258510304cfa4aa6` |
| Tras conciliar, repetir y recibir el aviso tardío | `9af036d76e6278259f70613140f9247017ce5bf9872e361f9cdd32f4fd444322` |
| Expediente sintético completo | `74806b7166fa52786eadb9f89193550c9afb0334a03068de94e40c5a634692bb` |

## Diferencias que requieren revisión

En un segundo ensayo se alteró únicamente el extracto ficticio. El diario seguía justificando cuatro acciones y 9.960,07 USD, mientras el extracto mostraba cinco acciones y 9.960,06 USD. La conciliación devolvió `PENDING` e identificó el instrumento, la acción de más y el céntimo de menos. Los valores observados se conservaron. Las pruebas también cubren recibos sin ejecución correspondiente, discrepancias de cantidad o importe por orden y dos instrumentos cuyo efecto neto en efectivo es cero.

El formato 3 del laboratorio conserva el efectivo liquidado y las acciones en un extracto propio. Cada ejecución actualiza ese extracto y los acumulados de la orden en la misma transacción. La conciliación reconstruye por separado los saldos desde la cuenta inicial, usando precios efectivos y signos de compra y venta. Los mensajes repetidos cuentan una vez por ejecución. La reserva del motor de riesgo figura aparte.

Los formatos anteriores guardaban acumulados por orden. Al abrir una base de formato 1 o 2 se toma de ellos el primer extracto, una sola vez. La comparación contrasta ese punto de partida con el diario disponible. La independencia del extracto frente a cambios posteriores en esos acumulados comienza con el formato 3. La base principal de JAIME conserva su esquema `0015_history_batches`.

## Reproducción desde la raíz del proyecto

```powershell
.\.venv\Scripts\python.exe scripts/probe_paper_reconciliation.py --demo
.\.venv\Scripts\python.exe -m pytest -q backend/tests/test_paper_reconciliation.py
.\.venv\Scripts\python.exe scripts/probe_paper_reconciliation.py --inspect
```

`--demo` crea una cuenta temporal con el fixture publicado. `--inspect` consulta el laboratorio del proyecto sin registrar recuperaciones. El comando sin argumentos concilia ese laboratorio. El código de salida 2 identifica diferencias pendientes o un bloqueo. `NO_ACCOUNT` indica que aún no se ha admitido una cuenta en ese laboratorio.

## Comprobación del entorno local

El trabajador cargó la conciliación con su intervalo habitual de cinco segundos. El recibo de B5 `166165aa9df54546ef4501036ca84d615cd690044b19ce10008a3fdb92342ca4` devolvió `NO_CANDIDATES`. Hubo cero intenciones, cero entradas en cola y cero envíos. El laboratorio del proyecto devolvió `NO_ACCOUNT`. Las cuatro acciones de la tabla pertenecen al ensayo sintético.

MASTER mostró efectivo y NAV de 10.000,00 EUR, cero posiciones y modo `PAPER_ONLY`. La oficina y la API respondieron en localhost. La ruta pública `POST /api/orders` devolvió HTTP 403. Coste externo de B6.3, 0 EUR.

| Tabla de MASTER | Filas antes y después | SHA-256 antes y después |
|---|---:|---|
| `portfolios` | 1 | `0d828b325c90d10d7fc8fd928a1457a6491c9b080b6bfd76e7e200758f01af5c` |
| `ledger_events` | 1 | `879aff0b180985e01a76772f7c9a0fd744488f0546c63f22be638ad42693e4d2` |
| `ledger_entries` | 2 | `e6927e22bff6b65e2b76467dd8c695c8e77a1972b493a0efcf9683562d31f30e` |
| `valuation_snapshots` | 20 | `3c653392eaf15c805a47a94b8ec37ef3373e8200dfa8f44a1e0e37d29092490c` |

Las huellas usan todas las columnas y filas de cada tabla, ordenadas por la primera columna, en una sola transacción de lectura. Se aplica SHA-256 al JSON compacto de la matriz de filas en UTF-8. La API verificó el diario con huella `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`.

Pasaron las 73 pruebas de B6, incluidas 16 de conciliación. Una de ellas introduce el descuadre después de que el trabajador reclame una orden. La comprobación dentro de la transacción conserva la reserva y la orden vuelve a quedar pendiente sin alcanzar el simulador. También pasaron las 115 pruebas de interfaz y la compilación de producción. Durante la ejecución simultánea con el backend, el resumen HTTP de la sede superó el umbral de cinco segundos. La repetición con el backend en reposo pasó con el umbral original.
