> ARCHIVO INACTIVO · copia anterior a la auditoría del 11-11-2026. Los próximos pasos históricos no gobiernan el trabajo. Enlaces relativos reubicados.

# Piloto IBKR de contratos — solo lectura



11-11-2026, Europe/Madrid. Prueba manual aislada, sin integración de runtime en el

backend ni agenda automática. No obtiene precios/históricos, no escribe en SQLite,

no modifica MASTER y no ofrece métodos de ejecución.



## Instalación local verificada



- Instalador oficial TWS API **1052.01**, descargado de

  https://download2.interactivebrokers.com/installers/tws-api/latest/tws-api-latest-windows-x64.exe

  el 11-11-2026. La URL `latest` es mutable: verificar versión/hash antes de reutilizar.

- SHA-256: `de5ad23355080490224f4b9b6060f3d3882cead34fc922cbcd93c4721642a859`.

- Firma Authenticode válida: Interactive Brokers Group, Inc.

- Licencia GPL v3 mostrada por instalador, aceptada con autorización expresa del

  usuario. `setup.py` declara GPL-3.0-or-later. Uso local; no se redistribuye el SDK.

- Fuente en `.tools/ibkr/sdk-1052.01/source/pythonclient`; instalación Python desde

  esa fuente, **no** desde el paquete `ibapi` de PyPI. Solo componentes Python/Core.

- Entorno `.tools/ibkr/venv`: Python 3.14.4, `ibapi==1052.1`,

  `protobuf==7.36.2`, `setuptools==80.9.0`, `wheel==0.45.1`, pip 26.0.1.

  Dependencias del backend y `uv.lock` sin cambios por este piloto.

- Instalación TWS realizada por el usuario en `tws/`, ahora ignorada por Git, igual

  que `.tools/` y `output/`. No mover ni borrar su instalación o configuración.



## Configuración y operación



TWS debe permanecer autenticado en **Simulated Trading**. Configuración observada:

API habilitada, Read-Only activado, localhost-only activado, puerto 7497.

El puerto no acredita por sí solo el tipo de cuenta.



Configuración privada existente `.tools/ibkr/pilot.json`: host `127.0.0.1`, puerto

7497, client_id 27, `read_only_confirmed_in_tws: true` y SHA-256 de la cuenta Paper

observada (`paper_account_sha256`). Sin contraseña, cookies ni cuenta en claro.

Reconfirmar Read-Only en TWS si se cambia la sesión/configuración: el protocolo

de esta prueba no verifica ese ajuste; se registra como evidencia visual.



```powershell

.\.venv\Scripts\python.exe -m pytest backend/tests/test_ibkr_probe_policy.py -q

.\.tools\ibkr\venv\Scripts\python.exe integrations/ibkr/test_offline.py -v

.\.tools\ibkr\venv\Scripts\python.exe -m pip check

# Archivo NUEVO: no sobrescribir la evidencia anterior.

.\.venv\Scripts\python.exe -B scripts/ibkr_readonly_probe.py --contracts --output output/ibkr-contract-probe-NUEVA-FECHA.json

```



El padre usa StorageGovernor (1 MiB reservado) antes de la red/escritura; ejecuta

un proceso aislado con límite de 50 segundos. El cliente permite únicamente IDs

de mensaje 71/49/9, tanto legacy como Protobuf: inicio, reloj y contrato. Bloquea

órdenes, cancelaciones, precios, históricos y demás mensajes. Cuenta única exacta

con prefijo de simulación y hash local requerido antes de consultar instrumentos.

Máximo tres consultas secuenciales y diez candidatos por respuesta, con plazo.

No ejecutar los ejemplos Testbed del proveedor: incluyen operaciones ajenas al piloto.



La consulta filtra acciones SMART/USD: la moneda recibida confirma el candidato

seleccionado, no demuestra que todas las cotizaciones de ese emisor sean USD.

SMART es enrutamiento, no una plaza ni MIC. Una coincidencia actual no prueba CIK,

continuidad histórica, acciones corporativas, permisos de datos o aptitud para backtest.



## Resultado real



Evidencia privada: `output/ibkr-contract-probe-20261111.json`, 09:38 Madrid.

Handshake/identidad Paper/reloj correctos, servidor 226; tres candidatos únicos,

en USD, plaza primaria NASDAQ devuelta por IBKR. Cuenta no expuesta en informe.

Mensajes salientes `[71,49,9,9,9]`, desconexión al terminar. Avisos 2104/2106/2158

se conservan por código, sin textos privados. No se solicitan datos de mercado.



Validación: 10 tests de política, 3 tests offline del SDK (798 intentos de mensajes

prohibidos rechazados), 37 tests de seguridad, `pip check` y sintaxis correctos.

El bloqueo de órdenes de JAIME continúa en 403; no se repitió suite completa/UI.

Herramientas fuera del presupuesto data/output: ~243 MB SDK/entorno/instalador y

~560 MB TWS al medir; no se han borrado archivos para reducir estas cifras.



11-11, revisión posterior entregada: contratos/divisa USD contrastados con SEC/Alpaca y archivados en data/ibkr/contracts/raw, bajo presupuesto. El diagnóstico y la ficha muestran la observación y su fecha, sin confirmar continuidad histórica. [Entrega y pruebas](../../docs/actual/ENTREGA_B2_3_CONTRATOS_IBKR.md).



Reproducción local del archivo revisado (sin conexión ni cambios SQLite):

```powershell

.\.venv\Scripts\python.exe scripts/archive_ibkr_contract_review.py --source output/ibkr-contract-probe-20261111.json

```

El hash y los vínculos están fijados; no admite otro informe sin revisión explícita.

Siguiente: identidad histórica del piloto; después ampliación de series y piloto europeo sujetos a derechos/coste cero. B2 abierto; no activa minería ni ejecución.

