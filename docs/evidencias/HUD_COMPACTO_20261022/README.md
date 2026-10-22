# HUD compacto — aceptación del Goal acotado

22-10-2026. Cambio limitado a `FinancialHud.tsx` y `financialHud.css`; sin cambios backend, contratos financieros, runtime, scheduler ni escena 3D. **P4 sigue PARTIAL**. P5/P6 no iniciados.

## Antes / después reales

Mismo navegador local, viewport y seis filas disponibles de fuentes reales; detalles cerrados, scroll al principio. Se cuentan filas completas dentro del área desplazable, no filas parcialmente visibles. Incluyen feeds y referencias, no seis activos distintos.

| Resolución | Antes | Compacta | Incremento | Ancho anterior → nuevo |
|---|---:|---:|---:|---|
| 1920×1080 | 3 | 6 | +100 % | 340 → 306 px |
| 1366×768 | 2 | 3 | +50 % | 300 → 306 px |

Los seis píxeles adicionales a1366 mantienen lectura; la reducción de ancho se aplica a pantallas grandes. Normal conserva340/300px respectivamente. En escritorio desde1280px Compacta es predeterminada, en pantallas inferiores Normal; la preferencia explícita se conserva en localStorage. Sin almacenamiento disponible, el selector sigue funcionando durante la sesión.

| Elemento | Normal / antes | Compacta |
|---|---:|---:|
| Texto base / símbolo | 16 / 16 px | 13 / 13 px |
| Precio | 18 px | 14 px |
| Encabezado de rail | 20 px | 16 px |
| Patrimonio | 30 px | 24 px |
| Padding vertical por fila | 18 px | 9 px |
| Padding interior | 20×22 px | 12×14 px |
| Padding encabezado | 20×22 px | 10×12 px |
| Separación métricas | 13 px verticales | 8 px verticales |

Se anulan los márgenes heredados de los spans solo dentro del resumen compacto de cada fila. Las unidades pueden ocupar dos líneas; no se truncan con ellipsis. Sparklines56×30px conservan puntos reales. Se mantienen colores/contraste, estado, variación disponible y enlaces a procedencia. No se reduce la tipografía de los departamentos. Controles principales de al menos32px; resumen de activo de al menos44px. El selector de densidad afecta a ambos paneles y tiene nombre accesible.

## Evidencias y comprobaciones

- `before.json`, `after.json`, `comparison.json`: medidas del DOM y prueba real reproducible con `scripts/qa_hud_density.js`; sin fixtures financieros ni llamadas LLM.
- A1920 y1366: sin overflow horizontal; todas las pestañas y navegación con flechas del tablist correctas; los siete controles inferiores de la oficina no están cubiertos. Apertura de los seis detalles, URL de fuente y unidad contrastadas con `/api/markets/watchlist`, fechas observada/recibida y vigencia visibles.
- Alternancia Normal/Compacta y persistencia tras reload correctas. A390×844: Normal predeterminada, Compacta seleccionable, mercados sin overflow y pestaña Posiciones funcional.
- Inspección visual de capturas de ambos paneles, general y móvil. No se han detectado solapamientos ni texto recortado en el contenido visible; el resto se consulta por scroll. Un estado pasó naturalmente de vigente a desactualizado entre capturas; no se congeló ni falsificó el dato para la comparación.
- `check.txt`: **212 pytest +54 Vitest, 1 opt-in omitido**, TypeScript/build; exit0. Sin dependencias nuevas. Avisos conocidos de Starlette/httpx y tamaño del bundle3D sin cambio relevante.
- API real:30roles, cero jobs/cola, NO_LOCAL_MODEL, MASTER10000.00EUR, hash`fdf208a2870b7027d00bf2c9e7f8ee78cd27c044bbca5f8bab8fcc3dcd465836`, orders_enabled=false, POST/api/orders403. Ninguna inferencia ejecutada. No se midieron FPS nuevos ni se afirma resolver el rendimiento pendiente de P4.
- Incidencia de captura inicial: timeout esperando filas a30s. Se repitió con navegador en primer plano y margen45s; ambas resoluciones completas y la repetición final pasan sin errores JS. No se cambió la API para fabricar datos.

Capturas auténticas en `output/playwright/hud-density/`:

- `before-1920-left.png`, `before-1920-right.png`, `before-1920-office.png`.
- `compact-1920-left.png`, `compact-1920-right.png`, `compact-1920-office.png`.
- Mismos archivos con `1366`; adicional `compact-390-markets.png`.

`screenshots.json` registra hashes. Las imágenes permanecen locales porque contienen datos CoinPaprika con permiso personal y sin redistribución pública. Los logs publicados solo normalizan blancos finales; no se alteran resultados.

## Siguiente paso — solo propuesta

[P4_PROFUNDIDAD_Y_CIERRE](../../P4_PROFUNDIDAD_Y_CIERRE.md) concreta contratos/persistencia de profundidad, selección de roles, síntesis compacta opcional, presupuestos acotados, degradación honesta y aceptación del debate profundo. **No se implementa en este Goal.** `Plan_JAIME_P5_P6.md` se conserva como requisito futuro de laboratorio Python y registro de descartes, sin habilitar fases ni conexiones.

Goal visual satisfecho; no equivale a declarar P4 terminada. PAPER ONLY y coste adicional0EUR.
