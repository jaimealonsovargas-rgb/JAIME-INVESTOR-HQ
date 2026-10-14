# Mundo 3D: arquitectura, interacción y calidad

## Planta única
Dimensiones objetivo aproximadas: 34 m (X) × 28 m (Z); eje Y vertical. Retícula abierta 3×3, pasillos de 2–3 m, tabiques de vidrio para conservar visibilidad.

| | Oeste X -11 | Centro X 0 | Este X +11 |
|---|---|---|---|
| Norte Z -9 | Research | Comité de Inversión | Quant Lab |
| Medio Z 0 | Riesgos | Trading Floor | Ejecución |
| Sur Z +9 | Performance | Recepción | Sistemas |

Spawn del jugador cerca de Recepción (X 0, Z +11). La cámara principal del producto **no es ninguna de las cámaras panorámicas de P1.B**: será una cámara de seguimiento en tercera persona detrás del avatar humano. Colisiones y navegación con raycast, WASD, ratón, zoom, E/clic, Escape, minimapa/HUD y teletransporte.

## Perspectiva definitiva del jugador (obligatoria desde P1.C hasta P7)
- **Tercera persona real**: el usuario ve a su personaje humano de cuerpo entero desde detrás, ligeramente por encima de los hombros; puede ver el suelo, los pasillos y el destino de su desplazamiento. La cámara acompaña al personaje al caminar y girar; no es una cámara de vigilancia, vista aérea, isométrica ni primera persona.
- **Parámetros de partida ajustables**, no medidas inmutables: separación horizontal de cámara-avatar aprox. 2,5–4,5 m, elevación suficiente para ver el entorno (aprox. 2,0–3,2 m sobre el suelo), FOV aprox. 60–75°, encuadre ligeramente elevado y con inclinación suave hacia el personaje y el frente. Afinar mediante pruebas reales y evitar mareo, recortes del avatar o distorsión.
- **Controles**: WASD para caminar; ratón para girar/orientar la cámara; zoom limitado; movimiento suave y configurable; interacción con E o clic directo en monitor. Avatar siempre visible mientras se explora; minimapa y teletransporte no sustituyen la navegación física.
- **Colisiones y cámara**: no atravesar paredes, vidrio, mesas o NPC; la cámara evita obstáculos y no queda detrás de techos, columnas o cristales que tapen la escena. Implementar raycast/spring arm, acercamiento automático o tratamiento visual del techo cuando sea necesario, sin teletransportes bruscos.
- **Diseño a escala humana**: comprobar ancho de pasillos, accesos, alturas de monitores, muebles, rótulos y distancias de interacción desde el punto de vista del avatar. Los nueve departamentos deben ser reconocibles y alcanzables caminando.
- **Cámaras de inspección de P1.B** (Recepción, Trading, Comité, planta completa): se conservan solo como herramientas auxiliares de revisión/mapa si aportan valor; no pueden ser la cámara inicial ni el modo normal de juego a partir de P1.C.
- **Aceptación visual**: capturas y vídeo opcional desde la cámara real detrás del avatar, tanto en recepción como al entrar, recorrer y usar monitores de distintos departamentos. Medir FPS mientras el personaje se mueve, no solo con escena estática. Añadir pruebas de oclusión en puertas, paredes de vidrio, muebles y techos; el modo panorámico no basta para aprobar P1.C–P1.F.

## Calidad visual P1
Estilo Manhattan/Londres hedge fund: piedra negra, nogal oscuro, cristal claro, metal bronce champán, luz LED cálida, skyline y pantallas azul noche. PBR, sombras horneadas donde convenga, HDRI con licencia, texturas comprimidas, GLB con LOD, instancing y reutilización de materiales. Humanos realistas y mobiliario creíble, no cubos ni avatares low-poly caricaturescos. Ver assets/REFERENCIAS.md y SVG.

## Rendimiento
Objetivo 45–60 FPS en equipo desktop de referencia, degradación a 30 FPS; medir hardware y FPS reales. Evitar una luz dinámica por monitor y pantallas financieras texturizadas ilegibles. Los monitores son meshes interactivos que abren React DOM overlays. El contenido financiero es accesible con teclado.

## Criterios
Todas las zonas físicamente accesibles, monitores identificables, escena navegable, calidad visual coherente, cargas razonables y capturas reales en STATUS. Una imagen generada no cuenta como escena funcional.
