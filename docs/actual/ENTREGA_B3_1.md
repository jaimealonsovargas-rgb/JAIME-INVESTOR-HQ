# B3.1 — núcleo determinista del laboratorio

11-11-2026, Europe/Madrid. **Entregado y comprobado con datos sintéticos.** No es una campaña con precios reales ni una estrategia aceptada para invertir. Siguiente entrega única: D1, definida en [ACTUAL](../../tasks/ACTUAL.md).

## Qué funciona

- `StrategyGenome` versionado: tendencia diaria long/cash con SMA, efectivo y buy-and-hold. Contratos cerrados, parámetros acotados, mecanismo y falsación registrados, sin código arbitrario ni llamadas LLM.
- Motor Python puro: señal con cierres ya disponibles; ejecución en una apertura posterior. Acciones enteras, sin cortos/apalancamiento; comisión fija y por importe, slippage adverso que incluye spread. Todos los costes deben declararse; los ceros del fixture son supuestos de prueba, no tarifas de un broker.
- Precios y dinero con Decimal y contexto local fijo; comisiones redondeadas a céntimos HALF_UP. Cantidad máxima asequible calculada incluyendo el redondeo. El saldo no se vuelve negativo; si la salida no cubre costes, el ensayo se rechaza con razón.
- El último inventario se valora al cierre sin inventar una venta final. La curva muestra efectivo, acciones y patrimonio. Incluye P&L, retorno simple, drawdown observado, costes, señales y fills internos. Sin Sharpe, OOS ni sellos estadísticos sobre seis sesiones.
- SQLite: `quant_datasets` comparte una sola copia por hash; `quant_trials` conserva configuración, hashes de datos/código/configuración/resultado, versión Python, estado y razón; `quant_trial_events` conserva el historial de intentos.
- El registro se confirma antes de validar/calcular. JSON acotado y válido es la admisión de transporte; solicitudes no JSON, mayores de 1 MiB o sin ID válido se rechazan antes de ser ensayos. Contratos financieros inválidos y datos reales sí producen un ensayo `REJECTED` registrado. Fallos del motor producen `FAILED`, sin copiar mensajes potencialmente sensibles.
- Identificador idempotente: repetir la misma solicitud devuelve el ensayo existente; reutilizarlo con entradas distintas da conflicto. Claim persistente con lease de 60 s, cálculo limitado a 30 s, hasta tres intentos y recuperación de interrupciones; un trabajador antiguo no puede sobrescribir al nuevo. Fallos terminales se preservan; repetir una investigación requiere un nuevo ID.

## Demostración exacta, exclusivamente sintética

Seis sesiones inventadas, un instrumento `TEST_ONLY`, unidad ficticia `TEST_CCU`, capital inicial 1.000 y comisión de una unidad por fill. No representa EUR, USD, MASTER ni ningún activo negociable.

| Control | Cálculo | Patrimonio final de prueba |
|---|---|---|
| Tendencia SMA de 2 cierres | Compra 83 a 12 + comisión 1; efectivo 3. Vende 83 a 8 − comisión 1 | 666 |
| Efectivo | Sin operaciones | 1.000 |
| Buy-and-hold | Compra 99 a 10 + comisión 1; efectivo 9. Valora las 99 al cierre 11 | 1.098 |

Prueba adicional de costes: con comisión fija 1, comisión variable 100 bps y slippage 100 bps, la tendencia compra 81 a 12,12, vende a 7,92 y termina en **641,56**. Ambos lados pagan costes. Estos números solo contrastan aritmética; no indican rendimiento esperado.

## Operación local

Desde la raíz, usando el entorno ya instalado:

```powershell
& ./.venv/Scripts/python.exe scripts/run_quant_fixture.py
```

La orden muestra los resultados completos y es idempotente. Usa el gobernador de almacenamiento antes de escribir. No arranca un scheduler, no descarga datos, no llama a los agentes y no publica órdenes. El servicio interno de registro requiere que su invocador admita almacenamiento; el CLI es la única entrada operativa de esta entrega. Sin endpoint ni panel nuevo.

Límites B3.1: un instrumento sintético por ensayo, 3–2.048 sesiones explícitas, lookback 2–252, ejecución por petición local y resultados `ENGINEERING_ONLY`. Los controles usan el mismo periodo y costes; buy-and-hold fija exposición larga desde el inicio e intenta comprar si todavía no dispone de una acción asequible. El corpus de mercado existente no se admite cambiando flags. La futura ruta real exigirá un contrato/manifiesto admitido en D3, no renombrar datos como sintéticos.

## Verificación y conservación

- **104 pruebas pasadas**: 33 nuevas de laboratorio, más base, seguridad y evaluación de datasets. Cálculo manual, costes, disponibilidad temporal, invariancia del pasado ante cambios futuros, determinismo, concurrencia, idempotencia, interrupciones, fencing, límite de recuperación, fallos, hashes, migración y MASTER.
- `POST /api/orders` sigue devolviendo **403** en las pruebas de integración. La suite conserva el bloqueo de los históricos actuales.
- Backend local reiniciado para cargar la nueva revisión; comprobación real a las **17:44:53 Europe/Madrid**: salud correcta, schema 0014, órdenes 403, MASTER con NAV/efectivo 10.000 EUR ficticios, cero posiciones y un evento. Evidencia `output/b31-20261111/runtime.json`.
- Migración aditiva `0013_shadow_cycles` → **`0014_quant_lab`**, primero sobre copia SQLite consistente y después en la base local. `integrity_check=ok`, sin errores de claves foráneas ni drift Alembic. **40 tablas anteriores con los mismos recuentos y hashes**, incluyendo modelos y contabilidad. Solo se añaden las tres tablas quant y la revisión Alembic.
- Base local: tres ensayos `COMPLETED`, nueve eventos y un único dataset de seis sesiones. Resultados idénticos a la copia de ensayo y al relanzar el CLI; ninguna solicitud de mercado.
- Las pruebas HTTP necesitaron ejecutarse fuera del aislamiento de Windows por un bloqueo de su socketpair local. La prohibición de conexiones externas de los tests se mantuvo. Un aviso de deprecación ya existente de Starlette/httpx no produjo fallos.
- Evidencias privadas: `output/b31-tests.log`, `output/b31-cli.json`, `output/b31-20261111/before.json`, `rehearsal.json`, `applied.json`. Copias conservadas: `before-0013.db` y `rehearsal.db`, 500.477.952 bytes cada una, **954,59 MiB en total**. Son copias de seguridad/verificación de la base existente, no nuevas descargas del mercado. No se activa borrado automático.

Código: [contratos](../../backend/app/quant_contracts.py), [motor](../../backend/app/quant_engine.py), [registro](../../backend/app/quant_store.py), [migración](../../backend/migrations/versions/0014_quant_lab.py), [pruebas](../../backend/tests/test_quant_lab.py), [CLI](../../scripts/run_quant_fixture.py).

## Punto de parada

B3.1 termina aquí. No se ha iniciado D1, captación masiva, minería real, validación OOS, riesgo ni ejecución PAPER. P4 sigue PARTIAL, coste obligatorio cero, órdenes bloqueadas y MASTER intacto. La cola sigue D1 → D2 → D3 → B3.2 → B4 → B5 → B6. La retención selectiva de respuestas temporales se diseñará con D2; esta entrega solo deduplica el fixture y conserva evidencia.
