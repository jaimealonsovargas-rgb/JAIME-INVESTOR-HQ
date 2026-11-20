# D2 — captación histórica por lotes

17-11-2026, Europe/Madrid. Infraestructura entregada con fixtures; archivo real IBKR bloqueado por derechos no acreditados. No se ha ejecutado el SDK contra red ni descargado mercado real en D2. [Ficha D2 preservada](../archive/2026-11-17-d2/ACTUAL.md) · [Siguiente D3](../../tasks/ACTUAL.md) · [Cola única](../../tasks/ROADMAP.md).

## Implementado y límites

Contratos y cola SQLite durable en `backend/app/history_*`, transporte aislado `backend/app/ibkr_history_transport.py`, coordinador manual `scripts/history_batches.py` y worker `scripts/ibkr_history_worker.py`. Peticiones de 1–5.000 instrumentos y máximo 20.000 unidades, ventanas diarias de hasta 31 días, checkpoints, idempotencia, pausa/cancelación, recuperación con lease de 100 segundos y hasta tres intentos. Contrato/identidad fijados en la petición no equivalen a identidad histórica validada.

Presupuesto compartido conservador IBKR: 30 peticiones/10 minutos y separación de 20 segundos; no es una cuota universal concedida por el proveedor. Sesión/cliente controlados, allowlist sin órdenes ni snapshot regulatorio. 2188 es aviso; pacing, permisos, ausencia de datos y sesión caída conservan causas diferenciadas. Sin nueva agenda n8n ni fallback de proveedor.

Snapshots deduplicados, evidencia inmutable y StorageGovernor antes de escribir. Caché de 24 horas solo para reutilización: no es retención autorizada ni política de borrado. No se borran originales, ensayos perdedores ni evidencia. Cobertura/fallos observables por unidad; calendario/gaps, identidad temporal y acciones corporativas siguen pendientes de admisión D3. TRADES ajusta splits, no dividendos; no mezclar series sin transformación versionada.

## Operación por terminal

CLI manual, sin nueva agenda automática ni panel. Ejemplo solo TEST sintético: elegir un ID nuevo en cada prueba; no repetir ni modificar un lote ya completado. Ejecutar desde la raíz del repositorio, con la base migrada. Pausa/reanudación/cancelación se aplican según el estado del lote; los comandos siguientes ilustran alternativas, no una secuencia obligatoria tras completarlo.

```powershell
# Sustituir TEST-ID-NUEVO por un ID único antes de ejecutar.
.\.venv\Scripts\python.exe scripts/history_batches.py fixture TEST-ID-NUEVO --targets 10
.\.venv\Scripts\python.exe scripts/history_batches.py status TEST-ID-NUEVO
.\.venv\Scripts\python.exe scripts/history_batches.py step TEST-ID-NUEVO --max-units 10
.\.venv\Scripts\python.exe scripts/history_batches.py pause TEST-ID-NUEVO
.\.venv\Scripts\python.exe scripts/history_batches.py resume TEST-ID-NUEVO
.\.venv\Scripts\python.exe scripts/history_batches.py cancel TEST-ID-NUEVO
```

Estos comandos no conceden derechos IBKR ni habilitan descarga real.

## Derechos

`history_rights.py` mantiene `UNVERIFIED_ACCOUNT_AND_USE_SCOPE`, persistencia `DENIED_PENDING_EVIDENCE`, investigación algorítmica `DENIED_PENDING_SCOPE_CONFIRMATION` y retención sin plazo acreditado. Gate IBKR denegado en código: CLI, entorno y JSON no conceden derechos. Los fixtures solo prueban ingeniería.

Revisión pública: [GFIS 3089, 01-05-2026](https://gdcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=3089), §2 uso personal y §4 non-display; [suplemento API 4569, 20-04-2026](https://ndcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=4569), §1.2 analítica ligada a cuenta IBKR, §2 restricciones y §3 no sustitución de feed. No se acredita licencia de archivo/retención ni compatibilidad del uso de esta cuenta local o del circuito Alpaca PAPER. Es falta de evidencia del ámbito concreto, no prohibición universal de IBKR. El acceso D1 no resuelve estos derechos; no hay licencia nueva, pago ni cambio de fuente.

Para revisar el bloqueo hacen falta las condiciones aplicables y aceptadas por la cuenta, el ámbito de los feeds/instrumentos, permiso de archivo y análisis automatizado local (incluido el destino Alpaca PAPER previsto), reglas de retención/cese y ausencia de coste obligatorio. Los formularios públicos son modelos de contrato, no prueba de aceptación de esta cuenta. No se han solicitado credenciales ni contactado con terceros. Si los términos aplicables no resuelven ese alcance, se necesitará aclaración del proveedor antes de habilitarlo.

## Verificación y estado de base

92 pruebas distintas: 69 backend (`test_history_batches`, `test_base`, `test_security`), dos regresiones adicionales y 21 offline SDK. Logs locales `output/d2-tests.log` y `output/d2-sdk-tests.log`; offline no acredita aceptación externa. Fixture 1.000 instrumentos/1.000 unidades en 11,457 segundos con StorageGovernor simulado: ingeniería local, no benchmark de red/producción ni cobertura de 1.000 activos reales.

Migración `0015_history_batches` ensayada en copia y aplicada: 43 tablas anteriores preservadas exactamente, incluidas quant y modelos; integridad SQLite correcta y cero fallos FK. Evidencias privadas `output/d2-20261117/before.json`, `rehearsal.json` y `applied.json`. Copia previa de 502.427.648 bytes y ensayo de 502.562.816 bytes: 958,43 MiB conjuntos; se conservan.

Minilote local sintético: diez objetivos/20 unidades completadas; segundo lote reutiliza las 20 con intento cero y recepción original. Total: dos lotes, 40 unidades, 20 snapshots. CLI status comprobado (`output/d2-20261117/cli-status.json`). No son precios IBKR reales.

Runtime verificado 17-11-2026, 12:29:49 Europe/Madrid (11:29:49Z): schema 0015, base correcta, órdenes 403, MASTER NAV/cash 10.000,00 EUR ficticios, cero posiciones y un evento; hash del ledger idéntico. Evidencia `output/d2-20261117/runtime.json`.

Cierre consolidado en `output/d2-20261117/validation.json`: 121 enlaces locales válidos, sintaxis de 13 archivos Python y `git diff --check` correctos; código igual al ensayado/aplicado. StorageGovernor permite otra unidad de 8 MiB: data 588.751.221 bytes, output 9.971.443.511 bytes en esa comprobación, sin limpieza automática.

PAPER ONLY, 0 EUR, MASTER separado, órdenes 403 y P4 PARTIAL vigentes. Sin backtest ni ejecución habilitados. D2 termina aquí: D3 debe sustituir bloqueos fijos por validadores y manifiesto congelado con razones reales antes de B3.2.
