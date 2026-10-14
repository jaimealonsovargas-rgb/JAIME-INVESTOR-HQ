# P1.B–P1.F — guía técnica de cierre para Codex (investigación consolidada)

> **Alcance actualizado por el usuario (2026-10-14):** revisión final correctiva de P1 sobre la versión LOCAL, y comienzo de P2 en el mismo encargo con gates. **STOP antes de P3**. Leer primero [PLAN_EJECUCION_P1_P2.md](PLAN_EJECUCION_P1_P2.md). Los apartados históricos de WASD, ratón, E/clic y NPC dispersos quedan sustituidos por el addendum siguiente. Esta guía NO acredita implementación.
>
> **Fuente B/C detallada:** [issue #1](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/issues/1). Este documento concentra sobre todo las decisiones de D/E/F para evitar una nueva investigación.

## Addendum obligatorio: correcciones del usuario (prevalece sobre el texto histórico)

1. **P1.B:** retirar sofás de Recepción; quitar/reubicar cristales obstructivos; redistribuir interiores Performance (análisis real) y Sistemas (racks agrupados, operador accesible); elevar PBR, iluminación, skyline y muebles conservando 9 salas.
2. **P1.C:** **solo flechas** ↑/↓ avanzar-retroceder, ←/→ girar personaje; cámara automática detrás y elevada ~3,2 m / 3,8 m, sin ratón/OrbitControls en juego. Resolver oclusión acortando brazo, mejorar rig, idle/walk/turn, velocidad y foot sliding.
3. **P1.D:** nueve monitores físicos y paneles React, pero apertura **automática al acercarse al agente principal sentado de cada sala**, no por E/clic; radio orientativo entrada 1,6 m, rearme 2,3 m; comprobar departamento/acceso, histéresis, modal y Escape.
4. **P1.E:** **10 NPC humanos sentados**: uno por departamento y un segundo en Trading, con microanimaciones de trabajo **solo ambientales**, sin fingir agentes P4.
5. **P1.F:** baseline de FPS de la versión LOCAL antes de tocarla, repetir pruebas visuales, navegación, paneles, NPC, licencias, P0, tests y FPS después. Avanzar después a P2.0→P2.6 según [PLAN_P2_CHECKPOINTS.md](PLAN_P2_CHECKPOINTS.md). STOP antes de P3.

## Protocolo de inicio y presupuesto

1. `git status --short`, `git log -1 --oneline`, revisar diffs y cambios sin publicar. **El working tree local es la autoridad**; las capturas recientes pueden ser posteriores al código de GitHub. No sobrescribir trabajo existente.
2. Leer `AGENTS.md`, `STATUS.md`, `tasks/P1_OFICINA_3D.md`, este documento y las secciones necesarias de `docs/02_MUNDO_3D.md`, `docs/03_DEPARTAMENTOS.md`, `docs/20_UI_Y_FLUJOS.md`. Consultar el issue #1 para B/C. No cargar P2–P7 ni el backend entero.
3. Plan breve y checkpoints secuenciales B → C → D → E → F, **autorizados expresamente**. Cada checkpoint: implementación, tests, prueba visual real, registro de incidencias y corrección. Si falla, no fingir verde ni contaminar la siguiente etapa. Continuar automáticamente si pasa; si hay bloqueo real, detenerse y explicar.
4. Hardware: Windows 11, Intel Core 5 120U, 16 GB, Intel Graphics integrada, 1920×1080. Equilibrado/DPR 1 como referencia. Objetivo 45–60 FPS en movimiento cuando sea viable; menos de 30 FPS sostenidos requiere optimización. FPS de P1.B en `STATUS.md` son históricos, **no resultados del cierre**.
5. Coste adicional 0 EUR, sin CDN ni recursos de pago, sin secretos, **PAPER ONLY**. No inventar cotizaciones, NAV, P&L, operaciones, votos, jobs ni proveedores disponibles. Los 10.000 EUR ficticios son de P3, no NAV de P1.

## Checkpoint B — acabado arquitectónico (detalle en issue #1)

- Techo orientativo **4,2–4,5 m**, ajustando proporcionalmente mamparas, marcos, dinteles, columnas, soffits, luminarias, rótulos y cámara; no cambiar únicamente `FLOOR.ceiling`.
- Revisar **todas** las sillas respecto a su mesa/monitor. En el modelo publicado `chair()` tiene respaldo hacia `-Z`; verificar orientación real y evitar solapes.
- Interior premium: piedra/mármol negro, nogal, bronce cálido, vidrio, PBR/roughness y escala de texturas coherentes, sillas y plantas más naturales, señalética integrada y discreta.
- Skyline con familias y distancias distintas, fachadas de bajo coste, capas de profundidad, niebla moderada; evitar bloques idénticos junto a ventanas. Mantener geometría fusionada por material y departamentos.
- Validar las cuatro cámaras auxiliares, capturas reales y FPS. No sustituir calidad de producto por una panorámica atractiva.

## Checkpoint C — tercera persona definitiva (detalle en issue #1)

- Inicio en Recepción con **avatar humano profesional de cuerpo entero** y cámara de seguimiento detrás y claramente por encima de la cabeza; no aérea, isométrica, primera persona ni panorámica. Punto inicial ajustable: cámara **3,2 m sobre suelo**, **3,8 m detrás**, **FOV 65°** (rangos documentados: 2,8–3,8 m / 3–4,5 m / 60–75°).
- Flechas ↑↓←→, cámara automática sin ratón en modo normal, Escape, minimapa 3×3 y teletransportes opcionales a **safe spawns verificados**. Normalizar diagonal, suavizar giro y usar `useFrame`/refs con delta; evitar `setState` React a 60 Hz.
- **Colliders semánticos XZ** para paredes, cristal, columnas, mesas y mobiliario; puertas visualmente abiertas deben ser transitables. No usar la malla fusionada entera como física ni instalar motor pesado sin necesidad.
- Cámara con spring arm/raycast, prevención de oclusión, pitch limitado, transiciones suaves y comprobación bajo techo. Vistas OrbitControls solo en modo inspección, nunca simultáneas al follow camera.
- Pruebas reales de navegación por las nueve zonas y cámara/avatar en las capturas.

## Checkpoint D — nueve monitores físicos y nueve paneles React

### D1. Arquitectura y comportamiento

- `model.ts` fusiona meshes por material; **no intentar convertir una etiqueta/pantalla ya fusionada en interactable identificable**. Crear `MONITOR_DEFINITIONS` con **exactamente nueve IDs únicos**, uno por departamento: `reception`, `trading`, `execution`, `performance`, `risk`, `research`, `committee`, `quant`, `systems`.
- Cada definición: `id`, `departmentId`, etiqueta, posición/rotación 3D, ancla de interacción, fase propietaria, tipo de panel. Verificar coordenadas con la **versión local**. Añadir nueve hitboxes/superficies de pantalla independientes sin deshacer el merge arquitectónico; raycast selectivo y `stopPropagation` para evitar click-through.
- Abrir **automáticamente al aproximarse al NPC principal sentado del departamento**, sin E/clic obligatorio. Distancias orientativas enter=1,6 m / rearm=2,3 m, con departamento correcto y acceso libre; no a través de paredes, ni reapertura inmediata al cerrar. El monitor sigue existiendo físicamente.
- El dashboard es **React/DOM**, no una textura ni un dashboard completo dentro de Canvas. Modal con `role=dialog`, `aria-modal`, foco inicial, trampa Tab/Shift+Tab, Escape, cierre visible y devolución del foco. Bloquear movimiento/cámara mientras esté abierto y restaurar exactamente posición, yaw, pitch y zoom al cerrar. El mundo debe continuar siendo explorable sin backend.
- Componentes compartidos, no nueve CSS duplicados: `MonitorOverlay`, `PanelHeader`, `StatusBadge`, `UnavailableState`, `DataTableShell`, `SectionCard`, marcas de fuente/hora. Estética institucional azul noche/piedra/bronce, legible a 1920×1080.

### D2. Contenido honesto por terminal

| ID | Interfaz P1.D | Datos/funciones bloqueados |
|---|---|---|
| `reception` | Estado de sede, mapa, PAPER ONLY y salud **real** del backend | NAV/caja P3, agentes P4; 10.000 EUR **no** es NAV actual |
| `trading` | Shell de Posiciones: instrumento, clase, qty, coste, precio, fuente/hora, P&L, exposición, estrategia y riesgo; tabla vacía | `SIN DATOS — CARTERA DISPONIBLE EN P3`; no filas ni precios demo |
| `execution` | Blotter con columnas orden/fill/rechazo/UNKNOWN/cuenta paper/reconciliación | `NO DISPONIBLE — P6 · SOLO PAPER`; sin envío de órdenes |
| `performance` | Shell NAV, series, rentabilidad, atribución, benchmark, FX | `NO DISPONIBLE — P3`; sin curvas ni retornos inventados |
| `risk` | Shell límites, exposición, concentración, liquidez, veto, kill switch | `NO DISPONIBLE — P5`; bloqueo P0 solo si verificado |
| `research` | Dossiers, tesis, valoración, fundamentales, macro, técnico, crédito, fuentes | `NO DISPONIBLE — P4`; sin informes ficticios |
| `committee` | Bull/bear, críticas, votación, actas, condiciones | `NO DISPONIBLE — P4`; sin votos ficticios |
| `quant` | Estrategias, señales, backtests, parámetros, costes, escenarios | `NO DISPONIBLE — P5`; sin Sharpe/backtests falsos |
| `systems` | Health, base de datos, PAPER_ONLY, órdenes deshabilitadas, schema, timestamps, estado real de proveedores | Ningún proveedor `DISPONIBLE` sin respuesta verificable |

- Para Sistemas reutilizar `GET /health` y `GET /api/providers/status`; `GET /api/instruments` solo si aporta valor veraz. El frontend publicado tiene `fetchHealth()`; añadir un cliente tipado/validado para proveedores si procede, **sin crear endpoints backend solo para decorar**.
- Estados compartidos: `available`, `no-data`, `stale`, `offline`, `blocked`, `pending`, `error`, `phase-locked`. Ausencia = «Sin datos»/«NO DISPONIBLE», **nunca cero financiero inventado**.
- Tests D: nueve IDs únicos y cobertura completa, fase correcta, rango/LOS, click-through, modal/foco/Escape, movimiento bloqueado, transform restaurado, backend offline, salud/proveedores reales y ausencia de números financieros inventados.

## Checkpoint E — diez NPC humanos profesionales y rendimiento

- **Diez humanos creíbles**, no cápsulas, cubos, robots, siluetas planas ni maniquíes geométricos como entrega final. Ropa profesional y escala coherente. Preferir 1–3 bases humanas buenas reutilizables antes que diez GLB pesados.
- **Pipeline de licencias:** inspeccionar primero assets y herramientas locales. Reutilizar modelos existentes solo con licencia verificada. MakeHuman/MPFB con assets CC0 y ropa formal CC0 es una posible vía **si ya hay herramientas compatibles**; Mixamo solo si hay assets válidos/acceso no bloqueante. No instalar Blender/MakeHuman pesados sin permiso ni usar assets por parecer gratuitos. Registrar autor, URL, licencia concreta, archivo y hash en `assets/LICENSES.md` y manifiesto.
- Para skinned glTF compartidos: cargar una vez, clonar esqueletos correctamente (`SkeletonUtils.clone` o equivalente), compartir geometría/texturas cuando sea seguro; animaciones idle/walk de avatar y 2–4 microanimaciones ambientales si disponibles. `AnimationMixer.update(delta)`; reducir actividad fuera de cámara.
- Distribución sugerida: Recepción 1, Trading 3, Research 1, Quant 1, Riesgos 1, Ejecución 1, Comité 1, Sistemas 1, Performance 0 = **10**. Ajustar a mobiliario/colliders locales.
- **No son agentes P4**: solo ambiente/idle. Etiqueta opcional `PERSONAL · OFFLINE` / `TRABAJO DE AGENTE: NO DISPONIBLE — P4`. Nunca fingir jobs, votos, análisis u órdenes.
- LOD/animación por distancia con histéresis: cerca ~0–8 m, medio ~8–16 m, lejos >16–20 m; medidas orientativas, afinar visualmente. Presupuestos iniciales (no estándares): avatar 30–60k tri, NPC cercano 20–35k, medio 8–15k, lejano 2–5k; texturas NPC preferentemente ~1K.
- Sombras dinámicas limitadas, sin luces por NPC. Medir antes de instancing/reescribir geometría fusionada. `PerformanceMonitor`/`AdaptiveDpr` solo si mejora de forma estable; no desactivar raycasts de monitores mediante optimización indiscriminada. Optimizar glTF **después** de inspeccionar y medir, conservando skin/animaciones. Precarga razonable sin gran bloqueo de arranque.
- Tests E: exactamente diez NPC, escala/posiciones seguras, licencias verificadas, no jobs P4 falsos, ausencia de dependencias externas runtime y rendimiento medido.

## Checkpoint F — aceptación integral de P1

- Ejecutar `python scripts/manage.py check`, `python scripts/manage.py audit`, `git diff --check` y nuevos tests; **registrar resultados reales**, nunca asumir cantidades. Verificar `/?diagnostico=1`, `PAPER_ONLY`, `orders_enabled=false` y rechazo de `POST /api/orders`.
- **Navegador real:** carga directa avatar/Recepción; solo flechas/cámara automática; colisiones con pared, cristal, mesa, columna y puerta abierta; cámara bajo techo/puertas; caminar a nueve departamentos; probar nueve teletransportes; abrir/cerrar nueve monitores; restaurar transform; foco/Escape; offline; diez NPC y cero actividad P4 fingida.
- **Benchmark en movimiento** a 1920×1080 Equilibrado: Recepción, Trading con NPC, giro de cámara, Comité, pasillo acristalado y abrir/cerrar monitor. Por escenario registrar FPS medio, p95 frame, draw calls, triángulos, texturas, geometrías, DPR, resolución y GPU. Reutilizar `window.__HQ_METRICS__` si existe; no reutilizar FPS estáticos como si fueran de P1.F. Si <30 FPS sostenidos, perfilar y optimizar DPR, sombras, NPC/LOD, skyline, texturas y draw calls, en ese orden aproximado.
- **Evidencias auténticas** desde app real en `docs/evidencias/P1F/`: Recepción con avatar, Trading con avatar/NPC, Comité, pasillo/techo/cámara, skyline, minimapa, Trading overlay, Sistemas overlay con salud real, escena con NPC y offline cuando se pruebe. Panorámicas solo complementarias.
- Verificar licencias/hashes, recursos locales sin CDN, 0 EUR, secretos ausentes. Actualizar `STATUS.md` por checkpoint con implementación **real**, tests, FPS, evidencias y limitaciones. Tras completar P1.F, comenzar P2 por checkpoints conforme al encargo actualizado; STOP antes de P3.

## Criterios de bloqueo y reporte

- No reemplazar humanos por muñecos para declarar E «completada». Si un asset válido requiere acción humana, **declarar bloqueo concreto**, no descargar material de licencia dudosa.
- Detener ante conflicto Git que pueda perder trabajo, vulneración PAPER ONLY/seguridad o impedimento técnico material. Si un checkpoint falla, reportarlo como pendiente.
- Respuesta final breve: checkpoints realmente completados, tests y FPS medidos, assets/licencias, evidencias, límites, confirmación PAPER ONLY/0 EUR, estado real de P1 y preparación para P2.
