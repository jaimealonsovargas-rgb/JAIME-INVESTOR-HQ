# P1 — Oficina 3D jugable premium (sin servicios de pago)

**Modelo recomendado en Codex: GPT-6.1 Sol · razonamiento Alto** (selección manual, si está disponible). Para componentes React simples o documentación: Sol Medio. Escalar a Astra Alto únicamente un problema difícil y acotado. **No usar modelos de pago por API, créditos, subagentes masivos ni modo acelerado facturable.**

## Lectura obligatoria (mínimo contexto)
1. `AGENTS.md` y `STATUS.md`.
2. Este ticket.
3. `docs/02_MUNDO_3D.md`, `docs/03_DEPARTAMENTOS.md`, `docs/20_UI_Y_FLUJOS.md`.
4. `assets/plano_9_departamentos.svg`, `assets/paleta_estetica.svg`, `assets/REFERENCIAS.md`, `assets/LICENSES.md`.
5. `docs/AUDITORIA_P0.md` y `docs/16_TESTS_ACEPTACION.md`.
Leer otros archivos solo cuando sean necesarios; **no copiar todos los documentos al contexto**.

## Resultado obligatorio
Al abrir `http://127.0.0.1:5173` aparece **directamente la oficina 3D jugable**, no el diagnóstico P0 ni un dashboard 2D. Una sola planta de aprox. 34×28 m, sin niveles apilados, pasillos abiertos y paredes acristaladas. Nueve departamentos físicamente presentes y distinguibles:

| Norte | Research | Comité de Inversión | Quant Lab |
|---|---|---|---|
| Centro | Riesgos | Trading Floor | Ejecución |
| Sur | Performance | Recepción / spawn | Sistemas y Data Quality |

Estética institucional de alto nivel, Manhattan/Londres: mármol/piedra negra, nogal, bronce cálido, cristal, luz indirecta, skyline, monitores financieros azul noche. Perspectiva de tercera persona elevada detrás de un **avatar humano de proporciones realistas**. Diez NPC humanos profesionales distribuidos de manera lógica. No Roblox, personajes geométricos, salas vacías ni una imagen estática fingiendo ser 3D.

### Interacción
- WASD, ratón para orientar cámara, zoom moderado, colisiones, Escape, accesibilidad de teclado, botón/contexto `E` y **clic directo en cada monitor**.
- Teletransporte desde mapa/menú a los nueve departamentos; controles en español.
- Cada zona tiene al menos un monitor físico que abre un **panel React/DOM legible y distinto**: Recepción (estado), Trading Floor (posiciones), Ejecución (órdenes), Performance (NAV), Riesgos (límites), Research (tesis), Comité (decisiones), Quant (estrategias), Sistemas (APIs/health).
- En P1 las funciones financieras posteriores deben indicar `NO DISPONIBLE — P2/P3/P4/P5/P6` según fase; **no mostrar precios, NAV, P&L, órdenes, rendimiento, trabajos de agentes ni saldos inventados**. Los 10.000 EUR son capital inicial **previsto para P3**, no NAV operativo.
- Los NPC pueden estar quietos, caminar o tener animaciones ambientales, pero su **estado de trabajo** debe indicar `OFFLINE/NO DISPONIBLE (P4)`; no simular jobs reales.
- La pérdida de backend no debe impedir explorar el mundo; solo marca servicios NO DISPONIBLES. Mantener `/health` y contratos P0 intactos salvo cambio necesario y probado.

### Dirección artística y assets gratuitos
- Emplear React Three Fiber, Three.js, Drei y assets glTF/GLB compatibles, licencia comercial/personal permitida; priorizar Blender original y CC0, HDRI/texturas de Poly Haven verificando licencia concreta.
- Registrar en `assets/LICENSES.md` cada asset externo: nombre, URL, autor, licencia, versión/fecha y atribución.
- Los IDs de Runway de `assets/REFERENCIAS.md` **no son PNG ni modelos 3D**. Si faltan imágenes, no fingir acceso: usar plano/paleta, y solicitar exportación de renders al usuario cuando sea imprescindible.
- Materiales PBR, geometría modular bien diseñada, texturas optimizadas, reflejos y luz indirecta con coste controlado; **calidad premium es criterio de cierre P1**, no una promesa para P7.
- El uso de primitivas técnicas durante desarrollo es aceptable, **pero nunca entregar un bloque de cubos como resultado final P1**.

## Implementación por subetapas para ahorrar tokens
**P1.A — Preparación (Sol Medio/Alto):** inspeccionar hardware Windows (GPU, memoria, resolución), probar compatibilidad R3F con React/Vite existentes, seleccionar licencias y presupuesto de rendimiento. Presentar plan y comenzar sin alterar backend.

**P1.B — Arquitectura premium (Sol Alto):** piso completo con 9 zonas, pasillos, vidrio, puertas, mobiliario, iluminación, skyline y materiales coherentes. Sin zonas ausentes. Captura real de navegador y FPS medidos. Ajustar antes de seguir.

**P1.C — Movimiento (Sol Alto):** avatar humano, cámara tercera persona, colisiones, WASD, zoom, teletransporte, accesibilidad y minimapa. Validar que se llega a las 9 zonas.

**P1.D — Monitores/UI (Sol Medio):** 9 monitores clicables con overlays React reales, estados NO DISPONIBLE veraces, botón volver al mundo, teclado/ratón y sin click-through. No integrar brókeres todavía.

**P1.E — NPC y optimización (Sol Alto):** diez humanos profesionales visualmente coherentes, animaciones de ambientación honestas, LOD/instancing/shadows y mejoras de rendimiento.

**P1.F — QA visual y aceptación (Sol Alto, Astra solo para bloqueo):** capturas de escritorio, E2E navegación y 9 pantallas, tests existentes P0 verdes, revisión de licencias y documentación de hardware/FPS. Pulir hasta el estándar visual requerido; no dar por terminada P1 con placeholders.

Trabajar **una subetapa por conversación/checkpoint** y actualizar `STATUS.md`. En P1.B y P1.E mostrar capturas reales para aprobación visual antes de continuar. No lanzar simultáneamente toda P1 en un prompt gigante.

## Pruebas y criterios de aceptación
1. `python scripts/manage.py check` sigue pasando (registrar resultado REAL, no asumir 56 tests).
2. La app abre directamente en 3D, sin pantalla de diagnóstico previa.
3. Los 9 departamentos están presentes, accesibles y reconocibles; mapa concuerda con plano.
4. Avatar humano y cámara tercera persona funcionan; no se atraviesan paredes ni se pierde el personaje.
5. Los 9 monitores abren paneles React diferentes, legibles y cerrables, sin necesidad de NPC.
6. Los 10 NPC tienen aspecto humano profesional y estados honestos, sin trabajos falsos.
7. Licencias/atribuciones registradas; **coste adicional 0 EUR**; no se descargan assets de pago.
8. FPS, tiempos de carga y GPU/CPU/RAM del equipo se miden y registran; degradación gráfica razonable cuando proceda.
9. Screenshots de **la app real** (no renders Runway), estado offline verificado, accesibilidad básica.
10. Prohibición live y guard de órdenes intactos. **No empezar P2** sin aprobación.

## Instrucción de arranque para Codex
«Lee los archivos indicados en este ticket. P0 está revisada estáticamente y autorizada para pasar a P1. Empieza por P1.A y P1.B; construye una escena arquitectónica premium de nueve departamentos en la aplicación real, con calidad visual verificable y coste 0 €. Mantén P0 verde, registra licencias, hardware, FPS y capturas, actualiza STATUS.md y **detente tras P1.B para que revise el aspecto**. No hagas P1.C–F todavía.»
