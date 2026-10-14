# Oficina Sims: decisión y adaptación incremental

La aprobación del issue #3 y el plan maestro sustituyen la cámara posterior. La huella 34 × 28 m, nueve IDs, builders de muebles, humanos locales y servicios P0/P2 se conservan. Se recolocan Trading al noreste, Quant al este y Ejecución al centro, conforme al SVG funcional.

La cámara de juego tiene azimut fijo atan2(2,5;20), desplazamiento (2,5;19;20), objetivo a 0,7 m y FOV 40°. Sigue al avatar con amortiguación; las flechas se proyectan en su base XZ y las diagonales se normalizan. No hay WASD, mouse-look ni OrbitControls. La vista general opcional usa (5;66;64), objetivo (0;1,3;−0,5), FOV 19°; Esc devuelve al recorrido sin mover el avatar. El techo queda oculto; ventanas y skyline conceptual visibles. Muros bajos de 0,48 m conservan colisiones, y los paños superiores se ocultan cuando impiden ver al jugador.

Paleta marfil, roble claro, azul noche y plantas; geometría y mapas CC0 existentes. Recepción sin sofás, con operador sentado detrás del mostrador; Performance accesible y Sistemas con dos puestos y tres racks laterales. Dieciséis asientos ocupados: 1/3/3/2/2/1/1/1/2 en Recepción/Trading/Research/Quant/Riesgos/Ejecución/Comité/Performance/Sistemas. Avatar adicional: 17 rigs independientes. Nueve principales conservan proximidad 2 m (Recepción 2,15 m), con comprobación de sala y línea de visión, y rearme 2,8 m; siete secundarios no abren interfaces. Animaciones ambientales; no trabajos de agentes P4.

Videowall norte físico de 32 × 4,8 m, centro (0;4,8;−13,35), **nueve secciones**: cartera, posiciones, operaciones, mercados, noticias, riesgo, comité, agentes y sistemas. Texturas dinámicas del resumen local y diálogo DOM accesible GET `/api/hq/overview` cada 30 s, sin consultas externas. Mercados/noticias solo muestran cache real con derechos actuales de visualización, almacenamiento y redistribución; fecha, fuente y caducidad explícitas. Cartera/posiciones/operaciones/riesgo/comité/agentes NO DISPONIBLES; no hay ledger ni jobs P3/P4.

Geometrías/texturas compartidas, LOD y batching estático. Poses y matrices de NPC a 15/8/4 Hz según distancia; cachés idempotentes evitan uploads y recorridos redundantes sin congelar animaciones. Equilibrado: DPR 0,8 (1536 × 864 internos sobre viewport 1920 × 1080), MSAA, sombras estáticas 1024; Detalle no certificado para Intel. El ensayo DPR 0,85 tuvo una ventana móvil de cinco segundos a 28,79 FPS en Recepción y se conserva como negativo. Medidas móviles y tirones reales en `evidencias/P1_SIMS/`.

Sistemas monta Data Quality con 35 modalidades/31 proveedores, cuatro filtros y estados separados. La selección explícita consulta un único preset; pausa, cuotas, cache, credenciales ausentes y desconexión tienen estados honestos. RSS oficial BCE requiere `AGENT_REACH_PUBLIC_ENABLED=true`; no se ejecuta runtime de terceros al arrancar HQ. Las dos referencias PNG originales están verificadas en a3547bc: son conceptos, no capturas. STOP antes de P3.

## S0 verificado

Preflight limpio en 71948e8; los commits locales previos permanecen intactos. Merge documental dc00029 desde origin/main ac3f68d; único conflicto de perspectiva resuelto con la decisión nueva y copia histórica. No reset, clean, force ni push.

Baseline real posterior a liberar carga adicional: Intel/D3D11, 1920 × 1080, Equilibrado DPR 1, Trading con 10 NPC: **31,29 FPS en movimiento**, p95 **92,7 ms**, 347 intervalos móviles. No representa aceptación del nuevo diseño. Captura y muestras completas en `evidencias/P1_SIMS/baseline-pre-sims.*`. El primer intento de automatización esperaba erróneamente una longitud de array en un objeto y se canceló; no produjo una medición ni se cuenta como prueba.
