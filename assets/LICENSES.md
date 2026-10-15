# Licencias de arte y recursos

## Distrito financiero retirado de runtime · 2026-10-15

**Canary Wharf**, Andreas Mischok / [Poly Haven](https://polyhaven.com/a/canary_wharf), **CC0-1.0**. La [licencia oficial](https://polyhaven.com/license) permite modificar y redistribuir gratuitamente. Descarga pública real del JPG tonemapped 8K, reducido localmente a 4K. URL, tamaños y SHA-256 de fuente/derivado en [P1_CITY_MANIFEST.json](P1_CITY_MANIFEST.json). **Retirado por la nueva petición de fondo negro puro**: el derivado se conserva en `assets/retired/canary_wharf_4k.jpg` para trazabilidad y no se carga ni se incluye en el build público. La oficina sigue siendo geometría Three.js real. No se añade ningún recurso externo ni servicio para el fondo negro.

## Humanos P1.C/E · 2026-10-14

| Recurso | Autor / fuente | Licencia y redistribución | Archivos / versión |
|---|---|---|---|
| Anatomía, rig, pesos, piel joven, ojos marrones, pelo Short02 y Shoes01 | MakeHuman Community; Data Collection AB, Joel Palmius, Jonas Hauquier y colaboradores | **CC0-1.0 para assets gráficos**, permite modificar y redistribuir. No se incorpora código AGPL de MakeHuman. [Licencia oficial](https://static.makehumancommunity.org/about/license.html), [separación código/assets](https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md), [reutilización en otro generador](https://static.makehumancommunity.org/mpfb/faq/build_other_chargen.html) | Núcleo fijado a `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`; fuentes y hashes por fichero en `assets/source-humans/SOURCE_MANIFEST.json`. Avisos originales conservados. |
| Traje formal `toigo_male_suit_tie_and_jacket` (chaqueta, corbata, pantalón) | Margaret Toigo / MRT · [pack oficial Suits01 CC0](https://static.makehumancommunity.org/assets/assetpacks/suits01.html) | **CC0-1.0**, corroborada en ficha y cabecera `.mhclo`; redistribución/adaptación permitidas sin pago | Fuentes OBJ, proxy, mapas y declaración en `assets/source-humans/clothes/toigo_male_suit_tie_and_jacket/`; hashes en el manifiesto de fuentes. |
| `professional.glb`, ocho clips y conversión | Derivado local de las fuentes anteriores; animaciones y conversor originales del proyecto | Se conserva CC0 para el modelo derivado. Skinning real; no imagen ni humano de primitivas | `frontend/public/models/professional.glb`, base nominal 1,78 m / mesh vestido medido 1,803 m, 41.114 triángulos, 163 huesos; hash y texturas 1K en `assets/P1_HUMAN_MANIFEST.json`. Ocho clips: idle, walk, turn, observe, focus, typing, reading, writing. Reproducible con `python scripts/build_p1_human.py` y `scripts/human_motion.py`. |

Todos los modelos y mapas se sirven localmente. Se descargaron entradas concretas mediante HTTP Range desde los paquetes gratuitos oficiales, sin instalar Blender/MakeHuman, cuentas, créditos o APIs facturables. `scripts/fetch_p1_humans.py` es una herramienta de mantenimiento opcional, nunca se ejecuta en runtime. Los originales se conservan para verificar procedencia; los cinco mapas runtime se redujeron a 1K mediante Canvas, conservando alpha en pelo/ojos. **Coste adicional 0 EUR**. CC0 permite redistribución; no se depende de licencias de Mixamo ni de assets sin autor identificable.

Los diagramas SVG son originales de este proyecto. P1.A–B incorpora materiales gratuitos de Poly Haven y modelado original en Three.js. No se han usado fotografías como sustituto de la escena ni modelos de pago. Las dos referencias Sims originales facilitadas por el usuario se conservan en `assets/reference_images/`, con hashes verificados en a3547bc. Son conceptos de dirección visual, no texturas runtime ni capturas; no se les atribuye una licencia CC0 ajena.

Los índices LOD derivados también son CC0 y se registran con hash en `assets/P1_HUMAN_MANIFEST.json`: avatar 41.114; NPC 24.714 / 13.240 / 4.040 triángulos. `scripts/optimize_p1_human.mjs` usa **meshoptimizer 1.1.1**, Arseny Kapoulkine, **MIT**, ya incluido en el lockfile; [fuente oficial](https://github.com/zeux/meshoptimizer) y aviso en `frontend/node_modules/meshoptimizer/LICENSE.md`. El optimizador se ejecuta offline, conserva UV, normales, pesos y animaciones; no se carga WASM del simplificador en la aplicación. Marcha con IK y ambientación sentada originales del proyecto, CC0. No hay Mixamo, compras ni herramientas pesadas instaladas.

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

## Revisión visual de P1.B · 2026-10-14

Respaldos ergonómicos, hojas curvas, jardineras torneadas, teclados, tejido, fachadas de edificios, cielo degradado, esculturas abstractas y placas discretas son creaciones procedurales originales en `world/details.ts`, `model.ts`, `materials.ts` y `Office.tsx`. No se han descargado nuevos assets ni imágenes generadas. La iluminación usa luces compartidas y PMREM procedural de Three.js, MIT, incluido en la dependencia ya inventariada; no usa un servicio externo. Los seis mapas CC0 anteriores permanecen sin modificación.

## Sims / integraciones P2 · 2026-10-15

La adaptación marfil/roble conserva los seis mapas CC0 originales: color, UV y parámetros de material modificados en código, no nuevos assets de terceros. Los 16 NPC y el avatar reutilizan el humano CC0 con rigs independientes y LOD; no se descargaron personajes de licencia incierta.

Agent Reach 1.5.0 y Vibe-Trading 0.1.16 se inspeccionaron en entornos aislados, no se incorporaron como dependencias runtime. Licencias MIT originales y NOTICE de Vibe preservados en `assets/integrations/`, con SHA-256 y commits en `licenses.json`. NOTICE distingue los materiales Qlib/Apache y tipografías/OFL upstream; no se copian sus assets de demostración ni se habilitan sus herramientas. [Alcance y límites de auditoría](../docs/INTEGRACIONES_TERCEROS_VERIFICACION.md).

Los datos financieros tienen permisos propios por modalidad, separados de la licencia del software: [matriz P2](../docs/P2_PROVIDERS_VERIFICACION.md). El RSS BCE solo conserva metadatos propios con atribución. No se redistribuyen cuerpos de noticias, imágenes de editoriales ni valores de feeds personales/restringidos en el videowall o evidencias públicas. Coste adicional de servicios 0 EUR.
