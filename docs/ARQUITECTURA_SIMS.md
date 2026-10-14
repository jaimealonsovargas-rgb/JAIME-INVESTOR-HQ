# Oficina Sims: decisión y adaptación incremental

La aprobación del issue #3 y el plan maestro sustituyen la cámara posterior. La huella 34 × 28 m, nueve IDs, builders de muebles, humanos locales y servicios P0/P2 se conservan. Se recolocan Trading al noreste, Quant al este y Ejecución al centro, conforme al SVG funcional.

La cámara de juego tiene azimut fijo atan2(12,16), desplazamiento (12,19,16), FOV 40°. Sigue al avatar con amortiguación; las flechas se proyectan en su base XZ y las diagonales se normalizan. El techo y el contexto urbano quedan ocultos y las divisiones son muros bajos cutaway; las colisiones del cuerpo permanecen físicas. No se barre la cámara elevada contra muebles bajos.

Paleta marfil, roble claro, azul noche y plantas; geometría y mapas CC0 existentes. Dieciséis asientos ocupados: 1/3/3/2/2/1/1/1/2 en Recepción/Trading/Research/Quant/Riesgos/Ejecución/Comité/Performance/Sistemas. Nueve principales conservan proximidad 2 m y rearme 2,8 m; siete secundarios no abren interfaces.

Videowall norte de 32 × 4,8 m con siete secciones. Su contenido no crea un ledger ni jobs. El resumen DOM accesible lee un endpoint local agregado sin hacer consultas externas por frame. Cartera, posiciones, operaciones, riesgo y agentes permanecen NO DISPONIBLES en P1/P2.

## S0 verificado

Preflight limpio en 71948e8; los commits locales previos permanecen intactos. Merge documental dc00029 desde origin/main ac3f68d; único conflicto de perspectiva resuelto con la decisión nueva y copia histórica. No reset, clean, force ni push.

Baseline real posterior a liberar carga adicional: Intel/D3D11, 1920 × 1080, Equilibrado DPR 1, Trading con 10 NPC: **31,29 FPS en movimiento**, p95 **92,7 ms**, 347 intervalos móviles. No representa aceptación del nuevo diseño. Captura y muestras completas en `evidencias/P1_SIMS/baseline-pre-sims.*`. El primer intento de automatización esperaba erróneamente una longitud de array en un objeto y se canceló; no produjo una medición ni se cuenta como prueba.
