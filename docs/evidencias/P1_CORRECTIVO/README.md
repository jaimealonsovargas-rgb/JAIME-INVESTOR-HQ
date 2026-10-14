# P1 correctiva · evidencia real, aceptación de rendimiento pendiente

La arquitectura original se conserva. Controles exclusivamente por flechas; diez NPC sentados; nueve paneles por proximidad al principal de cada departamento. Sin operaciones ni trabajos de agentes. Recursos locales CC0/MIT documentados en `assets/LICENSES.md`.

- `recorrido-continuo.json`: recorrido de las nueve salas con flechas reales y nueve aperturas automáticas, sin teletransportes ni escrituras sobre el transform del jugador. Los `final-{departamento}.png` corresponden a ese recorrido.
- `paneles-navegador.json`: nueve paneles, 18 aperturas incluyendo alejarse/regresar, Tab/Shift+Tab, pausa, Escape, restauración y WASD ignorado. La geometría de los puestos y los anchors permanece igual tras el batching.
- `offline-controles.json`: backend abortado solo en el navegador, panel honesto NO DISPONIBLE y control recuperado; WASD/ratón/rueda ignorados, inspección conserva el jugador; diagnóstico P0 disponible.
- `colisiones-recorrido.json`: observador del tramo final del recorrido, más de 3.300 muestras sin penetraciones y altura correcta. No cubre las nueve salas completas. La cámara inicial de Recepción puede extenderse sobre la entrada abierta; no hay un muro acristalado en ese hueco. El arranque espera a los colliders y la inspección vuelve a calcular el brazo posterior.
- `aceptacion-{recepcion,trading,comite,sistemas,performance}.png`: capturas posteriores a reubicar las mamparas laterales en el fondo y quitar sus franjas blancas interiores; reducen la oclusión junto a los NPC. `final-planta.png` es inspección arquitectónica. Todas son WebGL real, no imágenes generadas.
- `assets-final.json`, `movimiento-final.json`: hashes/licencias y FK de los keyframes de marcha y posturas sentadas; no sustituyen la revisión humana de la animación.
- `intentos/`: automatizaciones interrumpidas; no cuentan como aceptación. También se conservan baselines y ensayos de rendimiento negativos. Un fallo por codificación del nombre de un botón no es un fallo funcional del producto.

## Rendimiento final

Chrome real, Intel Graphics / ANGLE D3D11, 1920×1080, Equilibrado / DPR 1. Ventanas de 12 s con flechas reales, once rigs cargados y marcha previa. No se ejecutaron tests, compilaciones ni consultas WMI durante las ventanas. Los intervalos largos se conservan y cuentan en el promedio; se distinguen muestras de desplazamiento del total. `fps-seis-escenarios.json` contiene cinco escenarios y una repetición adicional de Trading, identificada como tal. `fps-recorrido-panel.json` añade un flujo real con apertura automática, cierre y marcha.

| Escenario | FPS en movimiento | p95 movimiento | Muestras móviles |
|---|---:|---:|---:|
| Trading | 22,40 | 108,8 ms | 173 |
| Recepción | 23,88 | 111,2 ms | 155 |
| Pasillo | 22,52 | 109,6 ms | 174 |
| Giro y marcha | 17,14 | 131,7 ms | 137 |
| Comité | 21,66 | 120,0 ms | 156 |
| Repetición Trading | 20,85 | 112,8 ms | 161 |
| Marcha + panel automático | 19,27 | 111,1 ms | 135 |

**NO alcanza el mínimo de 30 FPS. P1.F no está aceptada.** No se reutilizan los 32,8–59,9 FPS de la entrega anterior como si fueran resultados actuales. Esta sesión también comenzó con baseline inferior a 30. El batching reduce llamadas de dibujo sin sustituir materiales ni geometría; no ha resuelto los tirones.

Una muestra WMI real registró 750 MB libres, 91 % de memoria comprometida y paginación; CPU 1066 MHz. No demuestra causalidad exclusiva. Se ha solicitado reducir carga adicional antes de repetir, sin cerrar aplicaciones del usuario ni modificar su energía. La integración visual P2 permanece bloqueada por este gate, no por falta de autorización para avanzar.

## Reproducibilidad

Pruebas en `scripts/qa_p1_corrective/`, ejecutadas con Playwright CLI en Chrome y la aplicación local de producción en el puerto 5174. Los helpers solo leen la escena para planificar rutas; todas las acciones de movimiento/apertura son teclado y controles DOM reales. Para pasar JS mediante PowerShell se conservan los nombres con escapes Unicode; no reconstruirlos mediante una tubería Python que sustituya acentos por `?`.

Comandos: `python scripts/manage.py check`, `python scripts/manage.py audit`, `python scripts/check_p1_assets.py`, `python scripts/check_p1_motion.py`. La ausencia de un error en CLI no acredita éxito: comprobar que su salida es JSON de resultados y no un bloque `### Error`.
