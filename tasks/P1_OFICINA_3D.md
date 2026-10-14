# P1 — Oficina 3D jugable premium (sin servicios de pago)

**Modelo recomendado en Codex: GPT-6.1 Sol · razonamiento Alto** (selección manual, si está disponible). Para componentes React simples o documentación: Sol Medio. Escalar a Astra Alto únicamente un problema difícil y acotado. **No usar modelos de pago por API, créditos, subagentes masivos ni modo acelerado facturable.**

## Autorización expresa de cierre integral P1 · 2026-10-14

El usuario ha autorizado **una única ejecución secuencial de los checkpoints restantes P1.B → P1.C → P1.D → P1.E → P1.F**. P1.A ya está completada. Codex **no debe pedir aprobación intermedia** si las pruebas y verificaciones de cada checkpoint son satisfactorias; sí debe corregir fallos antes de avanzar y **detenerse ante un bloqueo real** de licencia/asset humano, conflicto Git con riesgo de pérdida de cambios, seguridad/PAPER ONLY o plataforma. Registrar avances y resultados verificables en `STATUS.md`.

Esta autorización **sustituye las instrucciones históricas** de trabajar una subetapa por conversación, pedir aprobación visual tras B/E y detenerse tras B o C; no sustituye las pruebas, el requisito de calidad visual ni los invariantes de `AGENTS.md`. **Tras corregir P1.F, iniciar P2 según el plan actualizado; STOP antes de P3.** La versión local y sus cambios sin publicar deben preservarse; sincronizar Git sin sobrescribir ni forzar.

La especificación detallada B/C está en [issue #1](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/issues/1); D/E/F y aceptación final en [docs/PLAN_CIERRE_P1_BF.md](../docs/PLAN_CIERRE_P1_BF.md). Leer por etapa, sin duplicar investigación ni documentación.

**ÚLTIMA APROBACIÓN VISUAL (PREVALECE):** [plan maestro Sims + videowall + 16 NPC + 30 roles IA](../docs/PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md). Cámara principal **isométrica elevada**, flechas screen-relative (no girar con flechas), 16 NPC sentados y pantalla enorme superior. Instrucciones históricas de cámara detrás, **10 NPC** y mármol oscuro NO prevalecen. Ejecución P1+P2; STOP antes de P3.

## Revisión final + ampliación a P2 (autorización posterior, prevalente)

**No reconstruir P1**: partir del trabajo LOCAL reciente. Retirar sofás Recepción; cristales que bloqueen; redistribuir Performance y Sistemas; mejorar calidad y caminar. **Solo flechas** ↑↓←→ y cámara automática sin ratón; **9 paneles por proximidad al agente principal** y no al monitor; **16 NPC sentados trabajando visualmente** (ambientación, no agentes P4). Validar P1 con capturas/FPS y comenzar P2.0→P2.6 con gates; **STOP antes de P3**. Especificación única: [PLAN_EJECUCION_P1_P2.md](../docs/PLAN_EJECUCION_P1_P2.md) y [PLAN_P2_CHECKPOINTS.md](../docs/PLAN_P2_CHECKPOINTS.md). Instrucciones anteriores incompatibles quedan supersedidas.

## Lectura obligatoria (mínimo contexto)
1. `AGENTS.md` y `STATUS.md`.
2. Este ticket.
3. `docs/02_MUNDO_3D.md`, `docs/03_DEPARTAMENTOS.md`, `docs/20_UI_Y_FLUJOS.md`.
4. `assets/plano_9_departamentos.svg`, `assets/paleta_estetica.svg`, `assets/REFERENCIAS.md`, `assets/LICENSES.md`.
5. `docs/AUDITORIA_P0.md` y `docs/16_TESTS_ACEPTACION.md`.
Leer otros archivos solo cuando sean necesarios; **no copiar todos los documentos al contexto**.

## Investigación técnica y especificación ejecutable
La guía [PLAN_CIERRE_P1_BF.md](../docs/PLAN_CIERRE_P1_BF.md) contiene decisiones y criterios para B–F, **ahora autorizados**. El [issue #1](https://github.com/jaimealonsovargas-rgb/JAIME-INVESTOR-HQ/issues/1) conserva el mapa de archivos y la especificación pormenorizada de B/C. Seguir los checkpoints en orden y documentar resultados reales.

## Resultado obligatorio
Al abrir `http://127.0.0.1:5173` aparece **directamente la oficina 3D jugable**, no el diagnóstico P0 ni un dashboard 2D. Una sola planta de aprox. 34×28 m, sin niveles apilados, pasillos abiertos y paredes acristaladas. Nueve departamentos físicamente presentes y distinguibles:

| Norte | Research | Comité de Inversión | Quant Lab |
|---|---|---|---|
| Centro | Riesgos | Trading Floor | Ejecución |
| Sur | Performance | Recepción / spawn | Sistemas y Data Quality |

Estética premium minimalista estilo Los Sims, madera clara/marfil/plantas y pantallas azul noche. **Perspectiva jugable isométrica elevada** con avatar visible, cámara de orientación fija y seguimiento suave, videowall gigante superior, 16 NPC sentados. Los materiales oscuros y la cámara detrás anteriores quedan sustituidos.

### Interacción
- Solo flechas ↑↓←→ para desplazamiento relativo a pantalla (avatar gira automáticamente); cámara automática sin ratón en juego; colisiones, Escape y accesibilidad. **Los paneles se abren por proximidad al agente principal sentado**, no por E/clic en monitor.
- Teletransporte desde mapa/menú a los nueve departamentos; controles en español.
- Cada zona tiene al menos un monitor físico y un agente principal sentado cuya proximidad abre un **panel React/DOM legible y distinto**: Recepción (estado), Trading Floor (posiciones), Ejecución (órdenes), Performance (NAV), Riesgos (límites), Research (tesis), Comité (decisiones), Quant (estrategias), Sistemas (APIs/health).
- En P1 las funciones financieras posteriores deben indicar `NO DISPONIBLE — P2/P3/P4/P5/P6` según fase; **no mostrar precios, NAV, P&L, órdenes, rendimiento, trabajos de agentes ni saldos inventados**. Los 10.000 EUR son capital inicial **previsto para P3**, no NAV operativo.
- Exactamente 16 NPC profesionales **sentados en sus puestos** con microanimaciones ambientales de trabajo; los agentes IA reales siguen `NO DISPONIBLE (P4)` y no se simulan jobs.
- La pérdida de backend no debe impedir explorar el mundo; solo marca servicios NO DISPONIBLES. Mantener `/health` y contratos P0 intactos salvo cambio necesario y probado.

### Dirección artística y assets gratuitos
- Emplear React Three Fiber, Three.js, Drei y assets glTF/GLB compatibles, licencia comercial/personal permitida; priorizar Blender original y CC0, HDRI/texturas de Poly Haven verificando licencia concreta.
- Registrar en `assets/LICENSES.md` cada asset externo: nombre, URL, autor, licencia, versión/fecha y atribución.
- Los IDs de Runway de `assets/REFERENCIAS.md` **no son PNG ni modelos 3D**. Si faltan imágenes, no fingir acceso: usar plano/paleta, y solicitar exportación de renders al usuario cuando sea imprescindible.
- Materiales PBR, geometría modular bien diseñada, texturas optimizadas, reflejos y luz indirecta con coste controlado; **calidad premium es criterio de cierre P1**, no una promesa para P7.
- El uso de primitivas técnicas durante desarrollo es aceptable, **pero nunca entregar un bloque de cubos como resultado final P1**.

## Implementación por subetapas para ahorrar tokens
**P1.A — Preparación (Sol Medio/Alto):** inspeccionar hardware Windows (GPU, memoria, resolución), probar compatibilidad R3F con React/Vite existentes, seleccionar licencias y presupuesto de rendimiento. Presentar plan y comenzar sin alterar backend.

**P1.B — Arquitectura premium (Sol Alto):** piso completo con 9 zonas, pasillos, vidrio, puertas, mobiliario, iluminación, skyline y materiales coherentes. Sin zonas ausentes. Captura real de navegador y FPS medidos. Ajustar antes de seguir. **Las vistas de inspección de P1.B no son la cámara de juego**; el pulido debe preparar una perspectiva isométrica Sims y videowall superior.

**P1.C — Movimiento (Sol Alto):** cámara isométrica elevada estilo Sims, orientación fija, seguimiento suave y avatar visible; flechas ↑↓←→ desplazan **en direcciones de pantalla**, avatar gira automáticamente. No WASD, mouse-look ni OrbitControls. Colisiones, paredes cutaway, animación sin foot sliding, accesibilidad, minimapa y teletransporte opcional. La ruta inicial abre en esta vista Sims.

**P1.D — Monitores/UI (Sol Medio):** 9 monitores físicos con **paneles activados por proximidad al agente principal** desde vista isométrica Sims, con overlays React reales, estados NO DISPONIBLE veraces, botón volver al mundo, teclado/ratón y sin click-through. Comprobar proximidad, departamento e histéresis y regreso a la misma posición del personaje. No integrar brókeres todavía.

**P1.E — NPC y optimización (Sol Alto):** dieciséis humanos profesionales visualmente coherentes **a la escala del avatar y vistos desde la cámara de juego**, animaciones de ambientación honestas, LOD/instancing/shadows y mejoras de rendimiento **durante el movimiento real del jugador**.

**P1.F — QA visual y aceptación (Sol Alto, Astra solo para bloqueo):** capturas **de la perspectiva isométrica Sims real con videowall superior**, E2E caminando por las nueve zonas y abriendo nueve pantallas, pruebas de cámara/colisiones/oclusión, tests existentes P0 verdes, revisión de licencias y documentación de hardware/FPS en movimiento. La vista global de planta es parte del diseño aprobado. Pulir hasta el estándar visual requerido; no dar por terminada P1 con placeholders.

**Excepción autorizada de cierre:** ejecutar B → C → D → E → F en una sola sesión/encargo con **checkpoints internos obligatorios**. Registrar capturas reales en B y E y autoevaluar contra los criterios; **no pedir aprobación intermedia** si pasan. Si el contexto se agota, dejar checkpoint/estado verificable en `STATUS.md` para reanudar sin reanalizar. Nunca saltar una prueba fallida. Tras validar F, iniciar P2 por checkpoints y detenerse antes de P3.

## Pruebas y criterios de aceptación
1. `python scripts/manage.py check` sigue pasando (registrar resultado REAL, no asumir 56 tests).
2. La app abre directamente en 3D, sin pantalla de diagnóstico previa.
3. Los 9 departamentos están presentes, accesibles y reconocibles; mapa concuerda con plano.
4. La **vista inicial es cámara isométrica elevada estilo Los Sims**, avatar visible, seguimiento suave y orientación fija; solo flechas screen-relative funcionan y el avatar se orienta automáticamente, la cámara evita obstáculos y no se atraviesan paredes, techos o muebles ni se pierde el personaje. Capturas de inspección estáticas sin recorrido jugable NO cumplen este criterio.
5. Los 9 paneles React se abren al acercarse al NPC principal de cada sala; monitores físicos presentes, sin E/clic obligatorio y sin reapertura inmediata tras cerrar.
6. Los 16 NPC tienen aspecto humano profesional y estados honestos, sin trabajos falsos.
7. Licencias/atribuciones registradas; **coste adicional 0 EUR**; no se descargan assets de pago.
8. FPS, tiempos de carga y GPU/CPU/RAM del equipo se miden y registran; degradación gráfica razonable cuando proceda.
9. Screenshots de **la app real desde la cámara Sims isométrica y videowall superior durante el recorrido** (no solo vistas de inspección ni renders Runway), estado offline verificado, accesibilidad básica.
10. Prohibición live y guard de órdenes intactos. **P2 autorizado expresamente**; STOP antes de P3.

## Instrucción de arranque para Codex (actualizada)

«Inspecciona y preserva el working tree LOCAL. Ejecuta las ocho correcciones finales P1 conforme a docs/PLAN_EJECUCION_P1_P2.md, prueba y documenta P1.F; a continuación empieza P2.0→P2.6 conforme a docs/PLAN_P2_CHECKPOINTS.md, con gates y commits. Sin datos inventados, sin live ni órdenes, sin costes; no empieces P3. Si hay bloqueo real, deja STATUS y checkpoint exacto.»
