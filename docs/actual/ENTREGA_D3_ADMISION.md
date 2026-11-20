# D3 — admisión determinista de datasets

18-11-2026, Europe/Madrid. Cierre de la implementación y pruebas realizadas el 17-11. Validadores y manifiesto congelado implementados; **ningún dataset real admitido**. El fixture positivo acredita ingeniería (`ENGINEERING_ONLY`). [Ficha D3 preservada](../archive/2026-11-17-d3/ACTUAL.md) · [Próxima entrega condicional](../../tasks/ACTUAL.md) · [Cola única](../../tasks/ROADMAP.md).

## Implementado y alcance

Motor determinista de gates, loaders read-only para snapshots D2 y archivo Alpaca y CLI `scripts/admit_dataset.py`. La admisión distingue contrato/dominio, integridad de originales y evidencias, identidad histórica, calendario, OHLCV, semántica y acciones corporativas, cronología, universo, derechos y profundidad. Fallos conservan causas; no se infieren derechos por accesibilidad, cantidad de barras o éxito del fixture.

Alcance inicial deliberadamente acotado: identidad constante durante el intervalo, sin aliases ni cambios; acciones corporativas con evidencia de cero eventos; calendario explícito con zona, plaza y cierres; disponibilidad antes de la siguiente apertura; universo predeclarado de un instrumento, sin bajas acreditadas. Los casos fuera de este alcance quedan bloqueados. El protocolo exige 252 sesiones, 60 de calentamiento y 192 útiles: es un suelo preliminar, no aceptación estadística.

El registro confiable de evidencias reales está vacío. El CLI selecciona automáticamente las evidencias revisadas por su sujeto; no importa JSON como autorización. Los derechos deberán acreditar cuenta/feed, uso, archivo/retención, destino previsto y coste cero mediante revisión de alcance concreto. La retención comprueba el plazo aportado en el registro frente a recepción y corte; no presupone 365 días ni concede archivo indefinido. El bloqueo IBKR de D2 continúa. No se han adquirido derechos, descargado precios ni incorporado proveedores.

## Operación por terminal

Desde la raíz, con la base existente en schema `0015_history_batches`:

```powershell
.\.venv\Scripts\python.exe scripts/admit_dataset.py fixture
.\.venv\Scripts\python.exe scripts/admit_dataset.py history --batch ID-LOTE --listing ID-LISTING --as-of FECHA-ISO-CON-ZONA
.\.venv\Scripts\python.exe scripts/admit_dataset.py market --listing ID-LISTING --as-of FECHA-ISO-CON-ZONA
.\.venv\Scripts\python.exe scripts/admit_dataset.py show --manifest SHA256
```

Los identificadores y la fecha son marcadores que se sustituyen por valores locales existentes. `history` también pagina objetivos con `--offset`/`--limit`. No realiza red ni escribe SQLite. Los manifiestos se publican por hash en `output/dataset-manifests/<sha256>.json`, con publicación atómica sin sobrescritura y StorageGovernor. Contienen metadatos, razones y referencias/hashes de precios, sin duplicar las barras archivadas. No hay migración nueva.

El diagnóstico legacy Alpaca y su interfaz permanecen separados; el CLI D3 es la ruta canónica de preparación de B3.2. No se ha cambiado el frontend ni ejecutado minería.

## Verificación y continuidad

134 pruebas distintas aprobadas: suite consolidada de 130 y cuatro casos nuevos en la repetición final de 31 pruebas del motor. No se suman de nuevo los casos repetidos. Logs locales `output/d3-tests.log` y `output/d3-engine-final-tests.log`; estos resultados de ingeniería no acreditan admisión financiera.

Comprobación final en `output/d3-20261117-final/acceptance.json`: las 49 tablas SQLite (incluida la versión Alembic) conservan exactamente sus filas y hashes; integridad correcta y cero fallos de claves externas. Sin migración, descargas, escrituras SQLite ni nuevas copias completas de la base. Cierre del 18-11 en `validation.json` de esa carpeta: huella final de código confirmada, 95 enlaces locales, sintaxis de 12 archivos Python y `git diff --check` correctos.

Se congelaron 14 evaluaciones: un fixture completo de 252 sesiones, diez instrumentos sintéticos D2 con 33 barras cada uno y las tres series Alpaca del piloto. El fixture completo supera ingeniería; los diez D2 carecen de las evidencias de admisión. Apple conserva 21 barras y las otras dos series no tienen histórico guardado. Ninguna serie real es BACKTEST_READY. Los ejemplos no limitan el universo del captador: el CLI procesa objetivos paginados; el protocolo inicial de admisión sí está acotado a cada instrumento y periodo.

Los cuatro comandos `fixture`, `history`, `market` y `show` se han ejecutado correctamente; salidas `output/d3-20261117-final/cli-*.json`. Los manifiestos conservan plaza, divisa, identidad, universo, feed y ajustes, además de los hashes de precios. La revisión independiente comprobó las correcciones de calendario, cutoff, identidad, universo y retención sin defectos bloqueantes pendientes.

Runtime verificado el 17-11 a las 23:45:59 Europe/Madrid: base 0015 correcta, MASTER NAV/cash 10.000 EUR ficticios, cero posiciones y órdenes 403; `output/d3-runtime.json`.

La siguiente entrega es B3.2, condicionada a admitir un dataset concreto con fuentes ya existentes. Primero resolver evidencias/derechos; no ampliar infraestructura de motor ni iniciar una campaña con datos bloqueados. B4, riesgo y OMS conservan sus gates. PAPER ONLY, 0 EUR, órdenes 403, MASTER separado y P4 PARTIAL vigentes.
