# P1 Sims · capturas y validación real

Entrega local 2026-10-15. React Three Fiber/Three.js real, no imagen conceptual. Nueve departamentos, 16 NPC sentados más avatar, flechas en direcciones de pantalla, cámara elevada fija con seguimiento, paredes cutaway, nueve paneles por proximidad y videowall físico de nueve módulos. Se conservan los componentes y assets anteriores. [Arquitectura](../../ARQUITECTURA_SIMS.md).

## Capturas auténticas

- [Planta completa y videowall](final-general.png).
- [Recepción](final-recepcion.png), [Trading](final-trading.png), [Comité](final-comite.png), [Sistemas](final-sistemas.png).
- [Performance](recorrido-performance.png), [Research](recorrido-research.png), [Riesgos](recorrido-risk.png), [Quant](recorrido-quant.png), [Ejecución](recorrido-execution.png).
- [Centro de control](videowall-referencia.png), [Sistemas/Data Quality](../P2/sistemas-data-quality.png), [RSS real](../P2/sistemas-noticias.png).

Los PNG originales en `assets/reference_images/` son **referencias conceptuales**, verificadas por hash en a3547bc. No son evidencia de implementación. Las capturas anteriores se tomaron en Chrome local; salas finales, planta y centro de control corresponden al build final DPR 0,8. `capturas-finales80.json` registra nueve módulos y control recuperado. Los PNG del recorrido completo se tomaron antes del ajuste de resolución, con la misma geometría a DPR 0,85.

## Navegación y seguridad

`recorrido-final-referencia.json`: recorrido continuo **9/9 salas**, solo flechas nativas; sin teletransportes ni escrituras de posición desde scripts. Nueve aperturas automáticas, cierre e histéresis. Dieciséis NPC sentados y 17 rigs independientes, con typing/reading/writing ambientales, sin agentes operativos.

`controles-fps-entrega80.json`: ↑↓←→ proyectados en pantalla; WASD, arrastre derecho y rueda no alteran jugador/cámara. `offline-foco-entrega.json`: pausa, Tab/Shift+Tab, Escape, pose/cámara conservadas, vuelta del movimiento, API abortada solo en navegador y diagnóstico P0. `../P2/backend-offline-real.json` además detiene realmente el backend propio, sin mocks: NO DISPONIBLE y recuperación inmediata de control/foco CANVAS.

Tests, build y auditoría completos en `check-entrega.txt`, `audit-entrega.txt` y códigos reales de salida en `comandos-entrega.json`. Se conserva `check-intento-timeout.txt`: un fixture construyó toda la oficina en 5,35 s y agotó su timeout de 5 s. Se ajustó únicamente ese presupuesto a 15 s, igual que el otro test de geometría, y se actualizó su rayo a la cámara isométrica vigente. Verificación offline de assets/hashes en `assets-verificados.json`: 33 fuentes humanas, seis mapas PBR, cinco mapas humanos, GLB con 163 huesos y ocho clips; LOD 41.114/24.714/13.240/4.040 triángulos. `animaciones-verificadas.json`: FK real de keyframes exportados, apoyo de marcha sin deriva y postura sentada. No sustituye la revisión visual de todas las poses de cada clip.

## Rendimiento final Intel

Chrome/Windows, ANGLE Intel Graphics 0xA7AC / D3D11, viewport 1920×1080, **Equilibrado DPR 0,8**, buffer 1536×864, MSAA y sombras 1024. Dieciséis NPC y videowall activos, backend/P2 conectado. Ventanas instrumentadas de 12 s con entrada nativa; las muestras de movimiento se separan del tiempo de panel pausado. No se usa FPS estático para acreditar marcha. Sin tests, compilación o smokes externos simultáneos.

| Escenario | FPS medio moviéndose | Peor ventana de 5 s móvil | p95 móvil ms | Draw calls / triángulos |
|---|---:|---:|---:|---:|
| Recepción | 36,38 | 32,73 | 62,2 | 172 / 355.202 |
| Trading | 46,60 | 43,75 | 42,5 | 116 / 323.902 |
| Comité | 41,69 | 38,92 | 49,6 | 147 / 408.578 |
| Sistemas | 46,13 | 43,34 | 37,6 | 171 / 340.816 |
| Pasillo | 40,76 | 36,97 | 53,6 | 178 / 400.896 |
| Recorrido + panel automático | 40,93 | 40,15 | 49,4 | 172 / 364.402 |

Datos crudos: `controles-fps-entrega80.json` y `controles-fps-combinado80.json`. Ventana móvil de 5 s: intervalos consecutivos de frames clasificados como movimiento que suman al menos 5.000 ms; no mide el panel pausado ni garantiza el mínimo de cada frame individual. Hay tirones. **45–60 FPS no se alcanzan en todas las zonas; Detalle no certificado.** Arranque observado en la confirmación final: callback 3,41 s y primer frame GPU 6,11 s; no es certificación de arranque frío de todo el equipo.

Ensayos conservados: baseline anterior con diez NPC, Trading 31,29 FPS DPR 1; primeros Sims con zonas inferiores a 30; ensayos de caché de poses/matrices; DPR 0,85 inicial 42–49. La última escena DPR 0,85 dio Recepción 31,74 FPS medios y **28,79 en cinco segundos**, insuficiente para el mínimo sostenido. Se corrigió el perfil a 0,8 sin cambiar número de personajes, muebles, materiales o luces. No son comparaciones controladas de idéntica carga del sistema.

Scripts reproducibles: `scripts/qa_p1_corrective/sims-tour.js`, `sims-controls-fps.js`, `sims-combined-fps.js`, `sims-offline.js`, `p2-ui.js`, mediante Playwright CLI sobre la aplicación local. Los benchmarks usan teletransportes seguros para aislar escenarios; el recorrido 9/9 no los usa. Intentos fallidos de automatización conservados en output y no cuentan como pruebas.

## Límites

Una base humana CC0 reutilizada con variaciones; luz indirecta/reflejos aproximados y skyline conceptual. No se garantiza 60 FPS ni ausencia de tirones bajo otras cargas. Los NPC solo ambientan: P4 NO DISPONIBLE. Cartera/posiciones P3, agentes P4, riesgo/comité P5 y órdenes P6 no están implementados. P0 permanece PAPER_ONLY y POST /api/orders = 403. Coste adicional servicios **0 EUR**. STOP antes de P3.
