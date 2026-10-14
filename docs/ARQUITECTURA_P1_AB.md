# P1.A–B · Arquitectura gráfica

Documento del alcance inicial P1.A–B: hardware, base gráfica y arquitectura de los nueve departamentos. El cierre posterior autorizado de P1.C–F está implementado y documentado en [ACEPTACION_P1](ACEPTACION_P1.md); las restricciones históricas de este documento no son el estado actual.

## Equipo y presupuesto inicial

Windows 11, Intel Core 5 120U (10 núcleos, 12 hilos), 16.847.925.248 bytes de memoria física instalada, Intel Graphics, driver 31.0.101.4953, pantalla 1920×1080. WMI declara 1 GiB de AdapterRAM; en esta iGPU no representa toda la memoria compartida disponible. WebGL comprobado por ANGLE Intel/D3D11 en Chrome. No se instala Blender ni se necesitan GPUs/servicios remotos.

Objetivo del ticket: 45–60 FPS; mínimo de degradación 30 FPS, sujeto al equipo y carga del sistema. Perfil Equilibrado: DPR 1 y sombras 1024; Detalle: DPR 1,35 y sombras 2048. Presupuesto de aceptación técnica: menos de 250 mallas fusionadas y 450.000 triángulos para toda la escena. Resultados reales y condiciones en STATUS.md; no se deducen FPS de estos presupuestos.

## Organización

- `world/layout.ts`: dimensiones en metros, nueve centros y presets de cámara para inspección arquitectónica. Plano 34×28 m: X oeste/este, Y vertical, Z negativo norte. Celdas amuebladas de 8,4×6,4 m; pasillos de 2,6 m.
- `world/model.ts`: geometría original con cantos redondeados, sillas con base de cinco radios, sofás con cojines, mesas, librerías, recepción acanalada, racks, plantas, vidrio y puertas estacionadas abiertas. Fusión de geometrías por material dentro de cada departamento; nodos department:id conservados para futuras interacciones.
- `world/materials.ts`: PBR con mapas CC0 locales, vidrio transparente de bajo coste, metal bronce y madera tintada/desaturada. Rótulos y monitores CanvasTexture, sin fuentes remotas ni gráficas financieras falsas.
- `world/Office.tsx`: iluminación, entorno procedural PMREM, sombras estáticas con recálculo al cambiar vista/calidad; métricas reales del renderer y tiempos de frame. No se usa una luz por monitor. Sombras de contacto aproximadas con gradiente local, no se afirman lightmaps horneados.
- `world/World.tsx`: Canvas con límites de error, controles de revisión y selector gráfico. La escena carga aunque /health falle. El diagnóstico P0 permanece en `?diagnostico=1`; la entrada normal abre directamente en 3D.

## Diseño y alcance visual

Norte: Research, Comité y Quant. Centro: Riesgos, Trading Floor y Ejecución. Sur: Performance, Recepción y Sistemas. Vidrio transparente, umbrales y pasos abiertos conectan todas las zonas en una sola planta. Techo visible en interiores y oculto únicamente en la vista de planta para inspeccionar la distribución; no es un piso adicional.

Recepción escultórica de piedra/madera/bronce; Trading Floor con seis puestos dobles; Comité con mesa de juntas y asientos en cuero; Research con biblioteca; Performance con sala de revisión; Sistemas con racks sin animación de trabajos; Riesgos/Quant/Ejecución con puestos y pantallas propias. Skyline de geometría original visible desde fachadas acristaladas. Las imágenes Runway no están en el repositorio: la dirección artística procede del SVG/paleta y requisitos escritos.

Las vistas Recepción/Trading/Comité/Planta son cámaras de revisión, no teletransporte del jugador. Arrastrar/rueda inspecciona el volumen; puede atravesar geometría por ser una cámara arquitectónica sin colisiones. No se declara navegación jugable de P1.C completada.

## Métricas y pruebas

Renderizado bajo demanda al observar una escena quieta, para no mantener la iGPU ocupada innecesariamente. «Medir FPS» activa 12 segundos de render continuo; el resultado se identifica después como última medición. No se presenta el reposo como 60 FPS.

Métricas locales expuestas en `window.__HQ_METRICS__`: FPS medio, p95 de frame, draw calls, triángulos, texturas, geometrías, resolución/DPR, renderer y nueve nodos de departamento. El cierre F conserva hasta 1.200 intervalos en `window.__HQ_FRAMES__`, suficientes para la ventana de 12 s; `window.__HQ_MOVING_FRAMES__` separa los intervalos con desplazamiento real. Se reinicia al cambiar cámara/calidad y al iniciar medición. Se excluyen pestañas ocultas y se cuentan las pausas largas: ya no se filtran intervalos superiores a 1 s. `loadMs` mide hasta el primer callback preparado y `firstFrameMs` hasta completar el primer frame WebGL sincronizado con GPU; no certifican la carga fría completa de todos los humanos. Los contadores son del último frame; activar «Medir FPS» para render continuo. Reposo jugable limitado a 20 Hz para animaciones ambientales.

Pruebas nuevas: correspondencia con el plano, paso entre celdas, una sola cota, presets dentro de la envolvente, geometría finita y presupuesto de mallas/triángulos. Pruebas P0 se conservan. Capturas reales de navegador y mediciones reproducidas por CLI; evidencias finales sanitizadas en docs/evidencias/P1B para revisión desde Git, además de output local ignorado.

## Seguridad y coste

Backend y guards de P0 intactos. Ninguna orden habilitada, ningún transporte hacia bróker. Monitores muestran NO DISPONIBLE con fase futura, sin NAV ni P&L ficticios. Recursos estáticos locales, sin CDN, HDRI remoto, telemetría remota, suscripciones o compras. Licencias y hashes en assets/LICENSES.md y P1_ASSET_MANIFEST.json.

## Revisión visual de P1.B · 2026-10-14

El usuario aprobó la distribución y la paleta general y pidió refinar el realismo. Se conservan centros, huella, pasillos, entrada 3D, controles de inspección y servicios P0. `details.ts` añade respaldos curvos con contorno ergonómico, asiento moldeado, hojas con nervadura y curvatura, macetas torneadas y UV de fachada. Las piezas se siguen fusionando por material/departamento; teclados y fachadas usan CanvasTexture original en lugar de una malla por tecla o ventana. Los monitores tienen biseles estrechos, soporte metálico, carcasa posterior y periféricos. Se añaden carpetas, tazas y esculturas abstractas propias.

Los carteles suspendidos desaparecen: placas de nogal/bronce a la altura de la vista sobre las mamparas y rótulo de suelo en Trading; la vista de planta conserva los nueve identificadores DOM. Exterior en tres franjas de profundidad, alturas, retranqueos y coronaciones diferentes, fachadas en todas las caras, cielo degradado original y niebla neutra desde 100 m, sin lavado azul próximo.

Luz ambiente reducida, luz diurna cálida, dos focos interiores compartidos orientados al suelo y materiales con rugosidad/relieve afinados. Se ensayaron luces de área y se retiraron al medir unos 26 FPS. La referencia antigua, medida después bajo la carga actual, también bajó hasta 29,72 FPS: no se atribuye toda la caída histórica al tipo de luz. Bevels pequeños con menor subdivisión y radios de silla modelados con tubos limitan el coste geométrico. No se usan SSR, ray tracing ni reflejos dinámicos de toda la escena: los reflejos siguen basados en el entorno procedural PMREM.

Techo a 4,5 m; luminarias por encima de 4,03 m y dinteles libres a 3,99 m. Presets de interiores a 3,25–3,35 m, dirigidos hacia abajo. El test del techo comprueba el mínimo de su geometría y lanza rayos horizontales por los umbrales centrales a 3,8 m. Esto revisa la envolvente arquitectónica para la cámara futura; no implementa avatar, seguimiento ni colisiones.

Capturas y JSON de medidas revisadas en `docs/evidencias/P1B/revision-visual/`. Benchmarks de 12 s con comprobación periódica de foco/visibilidad. Comparar con las cifras previas teniendo en cuenta las cámaras elevadas, geometría y carga del equipo; no son ensayos idénticos. La visual final debe ser aprobada antes de P1.C.
