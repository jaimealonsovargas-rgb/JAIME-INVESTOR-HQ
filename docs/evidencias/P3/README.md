# P3 — evidencia real, 16 de octubre de 2026

Entorno Windows local, Chrome con ventana, Intel Graphics / ANGLE D3D11, 1920×1080. No ejecución Cloud. Datos de prueba financieros separados de la base MASTER real (capital ficticio).

## Pruebas

- `python scripts/manage.py check`: exit 0; **144 pytest, 45 Vitest**, TypeScript y build. [Log](check.txt).
- `python scripts/manage.py audit`: exit 0; cero vulnerabilidades conocidas Python/npm. [Log](audit.txt). PowerShell etiqueta stderr como NativeCommandError incluso para avisos; no es el código de salida del proceso.
- Migración 0003_portfolio aplicada; MASTER **10000.00 EUR**, efectivo 10000.00, cero posiciones, un depósito. Dos inicializaciones y dos arranques del backup restaurado conservan cantidades y hash. SQLite integrity_check y claves foráneas correctos; 98 instrumentos P2. [HTTP y restauración](aceptacion-http-backup.json).
- POST local /api/orders **403**; lectura de APIs 200. Tests financieros cubren Decimal, FIFO, comisiones, FX/devengo, acciones corporativas, idempotencia concurrente, inmutabilidad, corrupción, aislamiento, derechos/feeds y métricas sin historia inventada.
- [UI](ui.json): cuatro tabs, teclado, mapa, offline con movimiento, diagnóstico y 390 px sin desbordamiento horizontal.
- [Recorrido](recorrido.json): nueve departamentos/paneles por flechas nativas, histéresis, cristales interiores atravesables, 16 NPC sentados. Fue anterior a la última corrección de textos financieros; [repetición final de los tres paneles afectados](paneles-financieros.json) confirma Recepción, Trading y Performance.

## FPS con movimiento real

| Zona | FPS | p95 ms | DPR |
|---|---:|---:|---:|
| Recepción | 60,00 | 17,7 | 0,81 |
| Trading | 59,99 | 17,8 | 0,82 |
| Comité | 59,99 | 17,8 | 0,83 |
| Sistemas | 59,97 | 17,8 | 0,84 |

[Datos completos](fps.json): perfil Equilibrado adaptativo, flechas nativas, ventanas de 12 s y más de 9 s móviles, 16 NPC y HUD/videowall activos. Peor ventana móvil de cinco segundos: 59,79 FPS. Sin builds, tests ni auditorías simultáneas. CDP focus emulation activado para evitar throttling por oclusión; el intento inicial ocluido (~1 FPS) no se cuenta como muestra válida. No es un A/B controlado frente a P1 ni una garantía bajo cualquier carga. Los intentos fallidos permanecen en output/playwright/p3; un intento adicional de captura encontró el target cerrado/about:blank y se repitió abriendo la aplicación.

## Capturas auténticas

- [HUD / cartera](hud-cartera.png), [posiciones](posiciones.png), [actividad](actividad.png), [mapa](mapa.png).
- [Videowall final](videowall-final.png), [planta final](planta-final.png), [centro de control](final-centro-control.png).
- [Recepción final](final-panel-01.png), [Trading final](final-panel-02.png), [Performance final](final-panel-03.png).
- [Comité](recorrido-committee.png), [Sistemas](recorrido-systems.png).
- [Offline simulado por bloqueo de peticiones del navegador](offline.png), [diagnóstico](diagnostico.png), [390 px](hud-390.png).

## Límites y seguridad

No hay cotizaciones con derechos de redistribución utilizables en la watchlist actual: no se fabrican filas ni variaciones. Market Pulse usa referencias reales de P2 con procedencia/fecha/estado. La frescura de P2 cambia con el tiempo; 18 conexiones históricamente verificadas no significan 18 fuentes utilizables ahora. No se han hecho consultas externas nuevas ni promovido instrumentos research-only a valoración. Las ratios que requieren historia muestran NO DISPONIBLE. No se añaden activos/licencias ni servicios de pago.

Persisten avisos de TestClient/httpx, THREE.Clock, redondeo Intel/ANGLE y chunk 3D >500 kB. Texto DOM independiente de DPR, pero la vista general limita su tamaño proyectado. Pendiente revisión visual del usuario y sesión prolongada con su carga habitual. No hay operaciones reales ni agentes P4 activos. PAPER ONLY; orders_enabled=false; coste adicional 0 EUR. STOP antes de P4.
