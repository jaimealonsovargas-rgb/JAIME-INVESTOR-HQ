# Licencias de arte y recursos

Los diagramas SVG son originales de este proyecto. P1.A–B incorpora materiales gratuitos de Poly Haven y modelado original en Three.js. No se han usado fotografías como sustituto de la escena ni modelos de pago. Las referencias de Runway siguen sin estar disponibles como imágenes locales.

## Recursos de P1.A–B

| Recurso | Autor / origen | Fuente | Licencia | Fecha y versión | Uso / atribución |
|---|---|---|---|---|---|
| Dark Wood, Diffuse + Normal GL + Roughness, JPG 1K | Dario Barresi (baking), Dimitrios Savva (fotografía), Rico Cilliers (tiling), Poly Haven | https://polyhaven.com/a/dark_wood | CC0-1.0, licencia indicada en la página del recurso | Descargado 2026-10-13; versión/hash y SHA-256 de cada mapa en P1_ASSET_MANIFEST.json | Acabado de madera adaptado al tono nogal mediante material/shader; fuente original descrita como caoba/cerezo oscuro. Créditos conservados voluntariamente. |
| Marble 01, Diffuse + Normal GL + Roughness, JPG 1K | Rob Tuytel, Poly Haven | https://polyhaven.com/a/marble_01 | CC0-1.0, licencia indicada en la página del recurso | Descargado 2026-10-13; versión/hash y SHA-256 de cada mapa en P1_ASSET_MANIFEST.json | Piedra de suelo y mostrador tintada oscura; fuente original crema. Créditos conservados voluntariamente. |
| Planta, mobiliario, vidrio, puertas, luminarias, skyline, vegetación, señalética y texturas de monitores | Creación original para JAIME INVESTOR HQ, código en frontend/src/world | Repositorio local; model.ts, materials.ts | Recursos propios del proyecto; sin licencia externa ni coste de adquisición | P1.B, 2026-10-14 | Geometría real paramétrica; skyline conceptual, no reproducción geográfica. No hay datos financieros ficticios. |
| Entorno de reflexión RoomEnvironment | Colaboradores de Three.js | https://github.com/mrdoob/three.js/blob/dev/examples/jsm/environments/RoomEnvironment.js | MIT (Three.js) | three 0.186.1, fijado en package-lock.json | Entorno procedural para iluminación/reflejos. No HDRI externo ni descarga en runtime. |
| Tipografía | Arial/Georgia/pila system-ui disponible en el sistema | Fuentes del equipo, canvas y CSS | No se redistribuyen binarios de fuentes | Sistema local | Rótulos rasterizados localmente en CanvasTexture, no se descargan fuentes. |

Condiciones CC0 verificadas: https://polyhaven.com/license y https://creativecommons.org/publicdomain/zero/1.0/. Se permite uso y adaptación sin pago ni atribución obligatoria. No se incluyen logos ni otros contenidos del sitio ajenos a los assets CC0. Los seis ficheros suman 2.180.614 bytes y se sirven localmente desde frontend/public/materials. No requieren cuentas, claves ni APIs de pago.

Reproducción de descarga: `python scripts/fetch_p1_assets.py` (opcional, requiere internet; no se ejecuta al arrancar). Comprueba MD5 publicado y registra SHA-256, autores, URL y versión en `assets/P1_ASSET_MANIFEST.json`. Conservar este registro y revisar cualquier cambio de fuente/licencia al añadir nuevos assets.
