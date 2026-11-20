# Sede antracita y paneles simplificados

## Ajustes solicitados el 31-10-2026

Continuación y comprobación final: 04-11-2026 (Europe/Madrid), conservando los cambios anteriores.

La segunda referencia autoriza cambiar las proporciones del mobiliario y corregir la ubicación de Riesgos. Esta intervención sustituye, solo en esos puntos, la restricción anterior de conservar dimensiones/posiciones.

- LED de pasillo de 2,2 a 3,8 cm, núcleo amarillo luminoso y halo amarillo más amplio sobre superficies; las tiras de paredes y perímetro comparten el mismo acabado. Corregido el tono marfil de la primera captura de esta revisión.
- Mostrador centrado de 6,30 m (antes 4,92 m), tapa de nogal, frente oscuro retranqueado, laterales estriados y zócalo iluminado. Un único mostrador con monitor/silla, sin la mesa pequeña superpuesta anterior. Fondo de piedra gris desaturada, listones de nogal, iluminación estrecha en los bordes, rótulo JAIME ampliado y dos plantas simétricas.
- Mesas simples de 1,90 a 2,30 m y dobles de 2,40 a 2,85 m; fondo de 1,02 a 1,14 m. Asientos conservados y colisiones regeneradas con las dimensiones reales.
- Apliques cálidos horizontales y bajos al final de ambos pasillos, pared de remate bajo el videowall y luz localizada sobre pared/suelo; corregidos los focos redondos excesivos de la primera captura. Cuatro luces puntuales sin sombras, compartiendo el presupuesto de sombras existente.
- Riesgos trasladado de x=9 a x=12, alineado con Trading y Performance. Mobiliario, NPC, accesos y terminal se trasladan conjuntamente; el pasillo derecho queda libre. Nueva comprobación de anchura a partir de los límites reales de las salas.

Verificación de código del 31-10: **90 pruebas frontend aprobadas, una omisión preexistente y build TypeScript/Vite correcto**. La prueba de escena conserva menos de 250 mallas y 450.000 triángulos, 16 NPC, nueve departamentos, accesos a personas/terminales y rutas transitables. La huella de colisiones anterior no se reutiliza como evidencia de esta nueva distribución.

El 04-11, después de la corrección de materiales/luces: **13 pruebas relevantes de escena/navegación y build TypeScript/Vite correctos**. Son una repetición de la parte afectada, no 13 casos nuevos que sumar a los 90. Detector de diseño sin hallazgos en los archivos modificados; diff sin errores de espacios.

Chromium: capturas válidas a 1836×856, 800×900 y 390×900, con los 16 NPC y el jugador cargados antes de capturar. Verificados desplazamiento y acceso de Riesgos, flechas, apertura/cierre de ficha y laterales móviles excluyentes, sin desbordamiento horizontal. **Cero errores JavaScript/compilación de shaders registrados y 208 colisiones**. La cabecera móvil opaca pendiente de la ejecución anterior queda comprobada. Datos financieros/estados proceden del backend, incluidas ausencias y errores de investigación que no constituyen errores JavaScript ni se han ocultado.

Evidencia privada: `output/playwright/visual-office/refinement-final/` (seis capturas y `report.json`). `refinement/` conserva la primera ronda. Renderizador SwiftShader por software: 201 llamadas y 332.180 triángulos en el recorrido capturado; no se ha medido FPS ni se certifica rendimiento en GPU. La composición y materiales se adaptan a la referencia dentro del modelo 3D; no se afirma identidad fotográfica.

Revisión visual independiente final: **`ship` para las cuatro correcciones puntuadas** (amarillo de LED, piedra/iluminación de recepción, luces bajas del fondo y tamaño/contraste del rótulo JAIME); todas resueltas en las nuevas capturas. La revisión anterior ya confirmó el tamaño de las mesas y la alineación de Riesgos. No equivale a certificación fotográfica ni a una nueva revisión completa de todas las superficies de la aplicación.

Las comprobaciones que siguen corresponden a la entrega anterior del 30-10.

## Primera entrega, 30-10-2026

30-10-2026, Europe/Madrid. Intervención visual solicitada antes de continuar el segundo tramo B2.4. El núcleo contable y los datos conservan su estado anterior.

## Implementación

- Paredes y panelado oscuro, suelo gris neutro con mapas de piedra existentes, madera y objetos claros conservados. Recepción con frente oscuro y luz amarilla inferior; marca del fondo legible.
- Tiras amarillas integradas en superficies 3D de paredes, esquinas y bordes de pasillos. El halo local comparte material y geometría fusionada; acompaña al ocultamiento de paredes. Sin postproceso de bloom, nuevas bibliotecas ni luces adicionales con sombras.
- Laterales ajustados al contenido. Resumen de patrimonio, caja, P&L y posiciones; resto de métricas y procedencia desplegables. Fechas y estados de precios visibles en la fila cerrada. Referencias macro separadas en desplegable. Sparklines conservadas dentro del detalle.
- Ficha de persona con mandato, trabajo y última entrega; capacidad, explicación, modelos y permisos en segundo nivel. Centro de control con fuentes y explicaciones desplegables. Los datos ausentes siguen siendo ausentes, sin cifras de demostración.
- En móvil, cabeceras de ambos laterales accesibles y un único cuerpo abierto. Redimensionar a móvil pliega ambos. Resúmenes nativos incluidos en la navegación con Tab de los diálogos.

## Archivos principales

3D: `frontend/src/world/materials.ts`, `model.ts`, `Office.tsx`.

Paneles: `FinancialHud.tsx`/`financialHud.css`, `PersonInspector.tsx`/`personInspector.css`, `HQVideowall.tsx`/`videowall.css`, `MonitorOverlay.tsx`/`panels.css` y `world.css`.

Contexto visual: `PRODUCT.md` y `DESIGN.md`. No se han editado backend, credenciales, importadores, modelos contables, movimientos de cámara ni posiciones de salas/personajes en esta intervención. Los cambios anteriores del usuario y de B2 permanecen en el árbol de trabajo.

## Verificación

- Suite frontend: **90 pruebas aprobadas y una omisión preexistente**. Build TypeScript/Vite correcto. Permanece el aviso previo de chunk 3D superior a 500 kB. Sin nuevas dependencias.
- Prueba de geometría original: menos de 250 mallas y 450.000 triángulos; nueve departamentos, 16 NPC, accesos, mobiliario y rutas válidos.
- **209 colisiones idénticas** antes/después, hash SHA-256 `970f8604ca6533175c24db30e457acaa56bf8261b54f631b556273b55fa964df`.
- Chromium: recorrido con flechas, vista general, Trading Floor y Comité; apertura/cierre de especialista y centro de control; modelos empresariales reales accesibles; móvil con laterales excluyentes. Anchos 1836, 1366, 800 y 390 px sin desbordamiento del documento; cero errores JavaScript registrados.
- `/health`, cartera MASTER y watchlist locales respondieron HTTP 200. Las capturas conservan estados reales de conexión y datos; durante el renderizado por software hubo timeouts transitorios de consultas, también presentes en la comprobación anterior al rediseño.

Evidencias privadas: `output/playwright/visual-office/before/`, `after/` y `final/`; `report.json` registra comprobaciones y huella de colisiones. Las capturas con precios no se incorporan a Git.

## Rendimiento y límites de aceptación

El renderizador de prueba es **SwiftShader por CPU**, no la GPU del usuario. La vista de recorrido pasa de 182 a 200 llamadas y de 332.942 a 333.440 triángulos (+0,15 %). La comparación consecutiva en `output/playwright/visual-office/benchmark/` fue inestable: original 0,18 FPS en recorrido con solo tres muestras; nuevo 1,08 FPS con trece. En vista general, 1,51 y 1,31 FPS respectivamente. **No acredita ausencia de regresión ni fluidez en GPU.** Se mantiene pendiente una medición con aceleración gráfica real.

El navegador integrado probado informó «WebGL no disponible» antes de crear la escena; se cerró esa pestaña de prueba. Las capturas y la verificación 3D proceden de Chromium con WebGL por software. No se han modificado opciones del navegador ni debilitado protecciones para forzar WebGL.

Se ha trasladado la paleta, iluminación arquitectónica y simplificación pedidas al modelo existente. No se afirma equivalencia fotográfica con la imagen de referencia.

## Continuidad

Retomar [ACTUAL](../../tasks/ACTUAL.md): ampliar conciliaciones contables y actualización por filing del segundo tramo B2.4. Después, B2.5; no saltar directamente a minería/ejecución por esta entrega visual.
