# P1.A–B · Arquitectura gráfica

P0 autorizada por el usuario y revisión estática de AUDITORIA_P0.md. Alcance: hardware, base gráfica y arquitectura de los nueve departamentos. No incluye P1.C–F: avatar, WASD, colisiones, teletransporte, monitores con paneles y diez NPC se implementarán después de aprobar el diseño.

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

Métricas locales expuestas en `window.__HQ_METRICS__` y muestra de hasta 600 intervalos visibles en `window.__HQ_FRAMES__`: FPS medio, p95 de frame, draw calls, triángulos, texturas, geometrías, resolución/DPR, renderer y nueve nodos de departamento. Se reinicia la muestra al cambiar cámara/calidad y al iniciar medición. No se registran frames con pestaña oculta ni pausas superiores a 1 s; una suspensión del sistema requiere reiniciar el benchmark. `loadMs` es el tiempo desde navegación hasta el primer callback de escena preparada; `firstFrameMs` mide hasta completar el primer frame WebGL mediante sincronización GPU. Son tiempos de esa navegación y equipo, no una certificación de descarga fría. Los contadores de draw calls y triángulos son los del último frame medido; para compararlos se debe activar «Medir FPS», pues en reposo se renderiza bajo demanda.

Pruebas nuevas: correspondencia con el plano, paso entre celdas, una sola cota, presets dentro de la envolvente, geometría finita y presupuesto de mallas/triángulos. Pruebas P0 se conservan. Capturas reales de navegador y mediciones reproducidas por CLI; evidencias finales sanitizadas en docs/evidencias/P1B para revisión desde Git, además de output local ignorado.

## Seguridad y coste

Backend y guards de P0 intactos. Ninguna orden habilitada, ningún transporte hacia bróker. Monitores muestran NO DISPONIBLE con fase futura, sin NAV ni P&L ficticios. Recursos estáticos locales, sin CDN, HDRI remoto, telemetría remota, suscripciones o compras. Licencias y hashes en assets/LICENSES.md y P1_ASSET_MANIFEST.json.
