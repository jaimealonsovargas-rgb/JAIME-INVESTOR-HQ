# Fuentes de las pruebas de navegador

Snippets utilizados con Playwright CLI sobre Chrome local real. Se conservan junto a los resultados para auditar los inputs y sondas. No son código runtime de la oficina ni modifican la posición del jugador: las rutas leen colliders/pose, y se recorren mediante teclado y ratón reales.

`walk-one.js` es el ayudante compartido; `GOAL` se sustituye por el destino XZ. Los snippets que contienen `WALK` lo expanden antes de enviarlos a `run-code`. `d-one.js` y `f-benchmark.js` reciben además `SPEC`: departamento/etiqueta/destino/panel o escenario de benchmark. Los parámetros y poses quedan registrados en los JSON vecinos.

Para repetir con una instalación existente de Playwright CLI, abrir una sesión aislada Chrome a `http://127.0.0.1:5174/`, viewport 1920×1080. También se puede usar 5173 para desarrollo; los resultados de aceptación corresponden al build de producción en 5174. No hay que instalar dependencias para arrancar la app ni para sus tests unitarios.

Ejemplo de expansión de la comprobación de colisiones en PowerShell (`$cli` debe apuntar al ejecutable existente):

```powershell
$walk = (Get-Content docs/evidencias/P1F/qa/walk-one.js -Raw -Encoding UTF8).Replace('GOAL', 'destination')
$code = (Get-Content docs/evidencias/P1F/qa/f-collision-smoke.js -Raw -Encoding UTF8).Replace('WALK', $walk) -replace '\r?\n', ' '
& $cli -s=revision-p1 run-code $code --raw
```

Para offline, sustituir GOAL por `[10.5,10.85]`; para galería por `[15.85,4.5]`; para terminal/benchmark por `spec.goal`. Las plantillas escriben capturas en las rutas originales: **cambiar las rutas a `output/playwright/revision-p1/` antes de repetir para conservar la evidencia de aceptación**. Crear ese directorio previamente. Las sondas de cámara/cuerpo deben cancelarse al finalizar, como hacen los snippets de cierre; no dejarlas activas al medir FPS.

La prueba adicional de foco amplía el terminal Sistemas con tres Tab y tres Mayús+Tab, comprobando que todos mantienen `document.activeElement.closest('dialog')`; resultado en `../accesibilidad.json`. Se volvió a verificar congelación/restauración, E y clic después de ese ciclo.

Pruebas unitarias, contratos, seguridad y build reproducibles con `python scripts/manage.py check`; hashes/estructura glTF con `python scripts/check_p1_assets.py`.
