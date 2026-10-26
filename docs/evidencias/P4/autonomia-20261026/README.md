# Primer ciclo autónomo P4 · evidencia 25–26-10-2026

**Ciclo acotado completado; P4 global sigue PARTIAL.** No se ejecutaron Bull/Bear/Chair, no se cargó ningún modelo, no hay P5/P6 ni operaciones financieras. Contrato/configuración: [P4_AUTONOMIA_PRIMER_CICLO](../../../P4_AUTONOMIA_PRIMER_CICLO.md).

## Demostración real sin UI ni pregunta

`scripts/qa_p4_autonomy.py` arrancó el backend con el navegador de pruebas cerrado, `NO_LOCAL_MODEL` y refresco general P2 desactivado para aislar la medición. El script no envió `POST /research/cases` ni `/run`: solo observó hasta que venció el reloj y, después del resultado, probó órdenes403 y pausa/reanudación. Para esta comprobación se configuró la espera inicial en 12 s; el valor predeterminado es 30 s y la cadencia es diaria.

| Ejecución | Tarea / caso | Resultado |
|---|---|---|
| 25-10, 17:02:25 UTC | `60386707-9008-53cc-a18f-eb40748928f2` / `dfe75707-8357-4423-8240-28eb8c410ddf` | SUCCEEDED / VERIFIED_DATA, **1,739 s**, 3 jobs Python, 81 evidencias |
| 26-10, 20:11:59 UTC | `9de4081c-285f-5648-a07f-e1c6112581fd` / `b757038b-8650-4c7a-a1d7-6ce0ba23823a` | Siguiente revisión vencida al reiniciar, SUCCEEDED, **6,132 s**, 3 jobs Python, 81 evidencias |

Fuente A21 CoinPaprika, 90 observaciones históricas diarias disponibles; los cálculos usan una serie comparable acotada a 60 observaciones y añaden evidencia derivada/contexto MASTER de lectura. Primera ejecución: **cache hit** real vigente, comprobación original 25-10 16:46:43 UTC; sus 3265 ms de proveedor son históricos, no latencia de este ciclo. Segunda ejecución: **cache miss / petición nueva**, 26-10 20:12:00 UTC, latencia P2 **1627 ms**, `real_connection=true`. No se presentan como precios de ejecución, OHLCV, recomendación o tesis de inversión.

Dos reinicios reales conservaron IDs/estados de la primera tarea y jobs; la pausa persistió tras el segundo. Reanudar no duplicó la revisión. Un vencimiento del día siguiente originó una nueva tarea legítima, no una duplicación del día anterior. El siguiente vencimiento quedó en 27-10 20:11:59 UTC. API y reloj siguen activos, pausa disponible en Sistemas/Research.

## Abstención, seguridad y recursos

Prueba adicional con backend auténtico y SQLite aislada, fuente A21 deshabilitada por configuración: tarea `a2bbdb66-7219-5da3-9a80-2ada21139c88` **ABSTAINED / DISABLED**, sin caso, sin cifras ni análisis inventados. Esto prueba ausencia de fuente utilizable, no un fallo real del proveedor. Tests `TEST_ONLY` separados cubren una sola observación, cero observaciones, derechos retirados, OFFLINE/cuota/credenciales, sin contarlos como conexiones.

Medición del primer ciclo: **21 muestras de aproximadamente 1 s**, Windows en batería (`ACLineStatus=0`); no es comparación con corriente ni benchmark de GPU. RSS máximo backend **115,75 MiB**, memoria privada máxima **96,83 MiB**, RAM libre mínima del sistema **1386,57 MiB**. CPU pico del proceso **7,719 % del total lógico**; media en los 12 s de reposo posteriores **0,151 %**. No hubo inferencias ni reintentos; una consulta P2 como máximo por tarea. No se ha repetido el benchmark de FPS, pues no se modifica el render loop. El plazo lógico es 90 s; el límite de interrupción de DNS/hilos se documenta expresamente en el contrato.

Comprobación final: schema **0006_autonomy**, `PRAGMA integrity_check=ok`, 30 roles, cola0/activos0, `NO_LOCAL_MODEL`; MASTER cash/NAV **10000.00 EUR** ficticios, posiciones0, `orders_enabled=false`, `/api/orders=403`, hash `fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`. Comparación fila a fila contra backup previo: **21 casos, 219 jobs, 1783 evidencias, 152 resultados, 172 claims y 1 evento de ledger**, ninguno modificado ni perdido. Coste adicional **0 EUR**.

## Pruebas y navegador

- `python scripts/manage.py check`: **317 pytest**, **63 Vitest** y 1 opt-in omitido, TypeScript/build correctos. Incluye 38 tests nuevos de autonomía: reserva concurrente, contratos, derechos, idempotencia, reinicio, plazos, callback bajo lock, pausa/cancelación y fronteras financieras.
- Primera regresión: 300 tests pasaron y falló la lista explícita de rutas OpenAPI al añadir tres APIs. Se actualizó esa expectativa y se repitió el check completo con éxito; no se ocultó el fallo.
- `python scripts/manage.py audit`: detectó seis CVEs en filelock4.1.1, dependencia transitiva de herramientas. Se actualizó únicamente a **4.2.1** en `uv.lock` y `.venv`; auditoría final Python/npm **0 vulnerabilidades conocidas**, `pip check` correcto.
- Migración real y `alembic check`: sin operaciones pendientes. `git diff --check` correcto.
- Chrome real: Sistemas y Research abiertos por clic NPC, tarea real, «Ver dossier», pausa/reanudación confirmadas por API y sin desbordamiento a1920×1080 y1366×768. **0 errores JS**; avisos existentes de Three.Clock y precisión del shader. Un error inicial del script Playwright por URL relativa y una doble pulsación se corrigieron en el harness antes de las capturas finales; no cuentan como PASS inicial.
- Tras el cambio del rótulo «P4 LOCAL», repetidos frontend63/TypeScript/build. El bundle3D conserva el aviso existente de tamaño>500kB; no se ha rediseñado la oficina.

Capturas reales privadas: `output/playwright/p4-autonomy/systems-1920.png`, `research-1920.png`, `systems-1366.png`, `office.png`. No se publican porque el HUD puede incluir precios de uso personal. [Metadatos verificables](acceptance.json) y [hashes de artefactos locales](artifacts.json) sí están versionados. El dossier completo y logs de aceptación permanecen en `output/p4-autonomy/`.

## Limitaciones pendientes

Una fuente y un objetivo descriptivo, no autonomía financiera general. No hay selección multiactivo libre, backtesting, agentes de riesgo formal ni ejecución. Los resultados de tareas son históricos: el dossier puede degradarlos a abstención cuando caduquen sus datos. La UI muestra esta distinción. La síntesis manual opcional sigue separada; el ciclo autónomo utiliza cero LLM. **El debate profundo sigue sin validación financiera: P4 PARTIAL.** Se detiene este Goal; P5/P6 no se inician.
