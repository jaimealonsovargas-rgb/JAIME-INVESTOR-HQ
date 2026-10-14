# P1 · Entrega y comprobación

P1.A–F implementadas en el repositorio local. B–F se cerraron secuencialmente conforme al issue #1 y PLAN_CIERRE_P1_BF; no se comenzó P2. Cambios locales previos preservados, sincronización documental por fast-forward a `abda9b6`, sin push ni despliegue.

## Qué funciona

- Oficina real Three.js/React Three Fiber, nueve departamentos conectados en una planta 34×28 m. Nogal/piedra/bronce/cristal, mobiliario suavizado, 23 sillas orientadas a sus mesas, placas integradas, fachadas y luces cálidas compartidas. Arquitectura fusionada conservada.
- Avatar humano skinned con traje profesional; inicio en Recepción, cámara elevada a 3,2 m y 3,8 m detrás, FOV 65°. WASD relativo, diagonal normalizada, giro suave, ratón derecho, zoom limitado, colisiones de cuerpo y cámara. Techo 4,5 m; luminarias/dinteles por encima del rango de cámara.
- Minimapa 3×3 y nueve teletransportes a posiciones verificadas. Cuatro cámaras auxiliares de inspección; «Recorrer» devuelve al jugador conservando su transform.
- Nueve monitores físicos: E/clic solo a distancia ≤2,25 m, delante de la pantalla y sin obstáculos. Nueve interfaces DOM distintas con diálogo modal, foco, Escape y restauración exacta de jugador/cámara.
- Salud y proveedores proceden del backend P0. El resto de paneles muestra honestamente las funciones pendientes P3–P6; sin datos financieros de ejemplo ni disponibilidad externa inventada.
- Diez NPC humanos de ambientación OFFLINE, rigs independientes, cuatro clips originales (idle/walk/observe/focus). Carga compartida y LOD con histéresis; animación/culling por distancia. No son agentes P4.

## Arquitectura añadida

| Área | Archivos en `frontend/src/world/` |
|---|---|
| Estado por refs y controles | `navigation.ts`, `Player.tsx`, `PlayerHud.tsx` |
| Colisiones semánticas y conectividad | `collisions.ts`, `pathfinding.ts`; colliders registrados por `model.ts` |
| Monitores y contenido | `terminals.ts`, `Monitors.tsx`, `MonitorOverlay.tsx`, `panels.ts`, `panels.css` |
| Humanos y optimización | `Avatar.tsx`, `Personnel.tsx`, `staffLayout.ts`, `humanLods.ts` |
| Métricas | `frameStats.ts`, `Office.tsx`; ventanas reales de 12 s y muestras móviles separadas |

No hay motor de física pesado, servicios cloud ni nuevas dependencias de pago. `api.ts` añade únicamente lectura tipada de `/api/providers/status`. Backend y diagnóstico P0 conservados.

## Comprobar en el equipo

Desde la raíz, abrir dos terminales si los servidores no están ya activos:

```powershell
python scripts/manage.py backend
```

```powershell
python scripts/manage.py frontend
```

Abrir **http://127.0.0.1:5173/**. La aceptación automatizada se realizó sobre el build de producción servido localmente en 5174, con el mismo código final. Chrome con aceleración gráfica y cargador conectado es la referencia.

1. Al cargar se ve el avatar desde detrás, entero y con cámara elevada; no aparece el diagnóstico.
2. Dar foco al mundo con un clic. WASD camina; Mayús acelera; arrastrar con botón derecho gira; rueda ajusta zoom; flechas izquierda/derecha giran también. Los muebles/cristales detienen al avatar y la cámara evita columnas/mamparas.
3. Caminar por los pasillos o utilizar los nueve botones del minimapa. Acercarse a un monitor, orientar el avatar y pulsar E o hacer clic en su pantalla. Cerrar con Escape o «Volver a la oficina»; la pose/cámara se conservan.
4. Sistemas muestra SQLite/salud/PAPER_ONLY reales y los proveedores NO DISPONIBLES. Detener el backend permite comprobar el estado offline sin impedir recorrer la oficina; volver a arrancarlo después.
5. «Medir FPS» recoge 12 s: caminar/girar durante la medición. `window.__HQ_METRICS__` separa `movingFps`, `movingFrameMsP95`, `movingSamples` del promedio total. No confundir reposo a 20 Hz o vistas auxiliares con FPS de desplazamiento.
6. **http://127.0.0.1:5173/?diagnostico=1** conserva la comprobación P0.

Validación reproducible sin servicios de pago:

```powershell
python scripts/manage.py check
python scripts/manage.py audit
python scripts/check_p1_assets.py
git diff --check
```

Las herramientas opcionales `fetch_p1_humans.py`, `build_p1_human.py` y `optimize_p1_human.mjs` documentan el pipeline de assets; no hace falta ejecutarlas para arrancar la aplicación.

## Resultados reales

**47 pytest + 25 Vitest aprobados**, TypeScript/build correctos. Auditoría: ninguna vulnerabilidad conocida Python, cero npm. Advertencias de Starlette/httpx y bundle 3D grande documentadas, no errores funcionales. [Logs](evidencias/P1F/tests-finales.txt) · [auditoría](evidencias/P1F/auditoria-dependencias.txt).

Chrome headless con GPU **Intel Graphics/D3D11 real**, 1920×1080, Equilibrado/DPR 1: **41,5 / 54,1 / 59,9 / 37,6 / 34,7 / 32,8 FPS móviles** en Recepción, Trading, giro, Comité, pasillo y flujo monitor. Tabla completa con p95, promedio total, contadores, datos originales y condiciones en [evidencias F](evidencias/P1F/README.md). No se certifica 60 FPS constante ni el perfil Detalle.

Nueve recorridos WASD reales, nueve teletransportes, nueve paneles por E/clic, congelación/restauración exacta, offline y diagnóstico P0 comprobados. Cámara corregida tras detectar cortes de esquina: **5.980 muestras finales sin penetraciones/cruces**, altura 3,2 m. Avatar contra mostrador, cristal, columna y pared: **2.159 muestras sin penetraciones**, deslizamiento lateral permitido. Tab/Mayús+Tab mantienen el foco dentro del diálogo tras añadir cierre explícito del ciclo; [prueba real](evidencias/P1F/accesibilidad.json). Conjunto real de once rigs (jugador + diez NPC) independientes.

`/health`: 200, PAPER_ONLY, órdenes deshabilitadas, SQLite correcto. POST local de orden LIVE: **403 P0_EXECUTION_DISABLED**. No se enviaron órdenes a brókeres. [Prueba HTTP](evidencias/P1F/p0-http.json). Consola final sin errores; [peticiones runtime](evidencias/P1F/red-local.txt) a recursos y backend locales, sin CDN.

Licencias: gráficos MakeHuman, traje de Margaret Toigo y mapas Poly Haven **CC0**; Three/R3F y meshoptimizer **MIT**. Se conserva la separación entre código AGPL de MakeHuman y sus assets gráficos CC0: no se copia el código AGPL. **33 fuentes, 6 mapas PBR y 5 mapas humanos verificados por hash**, glTF con 163 huesos y LOD 41.114/13.240/4.040 triángulos. [Licencias y atribuciones](../assets/LICENSES.md) · [verificación offline](evidencias/P1F/assets-verificados.json).

## Límites de esta entrega

Hay tirones: p95 móvil entre 18,4 y 62,9 ms. El total del flujo combinado de monitor es 28,9 FPS, aunque durante desplazamiento mide 32,8; pausas largas están incluidas. La prueba anterior con ahorro de batería activo dio 29,8 y se conserva. Con el cargador conectado el sistema confirmó AC activo y ahorro desactivado; la asociación con energía no demuestra que sea la única causa de variación. [Definición oficial de esos indicadores](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-system_power_status).

Primer callback de escena observado ~1,9–2,1 s; primer frame GPU ~6,1 s. No representa la carga fría completa de todos los personajes. Una base anatómica se reutiliza con variantes de vestuario/escala/animación; skyline conceptual, luz indirecta/reflejos aproximados para limitar carga de Intel integrada. No se promete fotogrametría ni GI en tiempo real.

Datos de mercado P2, ledger/NAV P3, agentes P4, riesgo/estrategias P5 y ejecución paper P6 siguen pendientes y NO DISPONIBLES. **Coste adicional 0 EUR. PAPER ONLY. STOP antes de P2.**
