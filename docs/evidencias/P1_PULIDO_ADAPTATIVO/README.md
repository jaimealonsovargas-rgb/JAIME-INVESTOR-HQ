# Cierre visual antes de P3 · 2026-10-15

Capturas auténticas de Chrome sobre la aplicación React Three Fiber/Three.js local. Las imágenes conceptuales del usuario no son capturas de este resultado.

## Versión final

- [Planta compactada, fondo negro y Ejecución bajo Sistemas](planta-final.png).
- [Vista inicial del jugador](recepcion-jugador-final.png).
- [Recepción y videowall completo](recepcion-final.png).
- [Videowall ampliado](videowall-final.png).
- [Trading](trading-final.png) y [Comité](comite-final.png).
- [Sistemas y Data Quality](panel-02.png), [Ejecución](panel-08.png) y [centro de control](centro-control.png).

## Interacción y regresión

[Recorrido nativo](recorrido-final.json): nueve departamentos y sus nueve paneles abiertos caminando con flechas, sin teletransportes ni escrituras de pose. Guarda coordenadas, rutas y texto de cada panel. `recorrido-*.png` y `panel-01.png` a `panel-09.png` corresponden a este recorrido. [Cristal interior atravesable](cristal-atravesable.png); los seis laterales exteriores marcados ahora son muros sólidos.

[Controles](controles-final.json): cuatro direcciones de pantalla y ausencia de movimiento/orientación mediante WASD, ratón o rueda. [Backend inaccesible](offline-final.json): peticiones abortadas desde el navegador, estado NO DISPONIBLE, movimiento conservado, foco contenido en el diálogo, pausa y recuperación de control. [Captura offline](offline-videowall.png), [diagnóstico P0](diagnostico-p0.png).

[HTTP local P0/P2](p0-p2-http-final.json): salud y esquema 0002_data, 98 instrumentos, Data Quality y nueve secciones HQ; POST /api/orders = 403. Estas lecturas no refrescan fuentes externas ni cuentan como nuevas conexiones de proveedores.

## Rendimiento

La comparación definitiva se recoge en `comparacion-fijo-adaptativo.json` y `rendimiento-resumen.json`: mismo build, Chrome con ventana, Intel Graphics/D3D11, 1920×1080, cuatro zonas, fijo 0,8 → adaptativo → fijo 0,8; entrada de flechas durante las muestras. El análisis usa exclusivamente fotogramas en movimiento. Los relojes sintéticos de Vitest prueban la política del controlador, no el rendimiento del ordenador.

Adaptativo: **Recepción 58,37 / Trading 57,70 / Comité 60,00 / Sistemas 59,83 FPS**; DPR final 0,99/1,00/1,00/1,00. Peor ventana móvil de cinco segundos **54,56 FPS**. Una muestra interrumpida al abrir Sistemas se conserva como excluida y se repite; las 12 muestras finales tienen más de nueve segundos móviles. La comprobación DOM 1,00 frente a 0,80 da la misma fuente 38 px/caja 320×46.

Después se elimina el alias PCFSoft retirado, manteniendo el mismo modo PCF que Three ya usaba por fallback. [Smoke del build final](smoke-pcf-final.json): **59,74 FPS móviles**, p95 17,8 ms. Las capturas finales corresponden al modo PCF directo. [Pruebas y avisos](pruebas-resumen.json); [equipo](equipo.json). No se compilaron ni ejecutaron suites durante los intervalos; hubo inspección/edición ligera de archivos durante la recuperación.

Las evidencias de [historial](historial/) pertenecen a iteraciones anteriores con otra geometría y/o fondo. No se usan para atribuir mejoras de FPS a esta compilación final.
