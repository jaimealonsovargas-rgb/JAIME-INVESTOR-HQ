# Mundo 3D: arquitectura, interacción y calidad

## Planta única
Dimensiones objetivo aproximadas: 34 m (X) × 28 m (Z); eje Y vertical. Retícula abierta 3×3, pasillos de 2–3 m, tabiques de vidrio para conservar visibilidad.

| | Oeste X -11 | Centro X 0 | Este X +11 |
|---|---|---|---|
| Norte Z -9 | Research | Comité de Inversión | Quant Lab |
| Medio Z 0 | Riesgos | Trading Floor | Ejecución |
| Sur Z +9 | Performance | Recepción | Sistemas |

Spawn del jugador cerca de Recepción (X 0, Z +11). Cámaras: elevada detrás del avatar para desplazamiento y panorámica para navegación; transiciones suaves y opción de reducir movimiento. Colisiones y navegación con raycast, WASD, ratón, zoom, E/clic, Escape, minimapa/HUD y teletransporte.

## Calidad visual P1
Estilo Manhattan/Londres hedge fund: piedra negra, nogal oscuro, cristal claro, metal bronce champán, luz LED cálida, skyline y pantallas azul noche. PBR, sombras horneadas donde convenga, HDRI con licencia, texturas comprimidas, GLB con LOD, instancing y reutilización de materiales. Humanos realistas y mobiliario creíble, no cubos ni avatares low-poly caricaturescos. Ver assets/REFERENCIAS.md y SVG.

## Rendimiento
Objetivo 45–60 FPS en equipo desktop de referencia, degradación a 30 FPS; medir hardware y FPS reales. Evitar una luz dinámica por monitor y pantallas financieras texturizadas ilegibles. Los monitores son meshes interactivos que abren React DOM overlays. El contenido financiero es accesible con teclado.

## Criterios
Todas las zonas físicamente accesibles, monitores identificables, escena navegable, calidad visual coherente, cargas razonables y capturas reales en STATUS. Una imagen generada no cuenta como escena funcional.
