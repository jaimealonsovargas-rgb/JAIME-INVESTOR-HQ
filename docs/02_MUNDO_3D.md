# Mundo 3D — diseño estilo Los Sims aprobado (2026-10-14)

**Fuente vinculante:** [plan maestro](PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md). Sustituye la antigua cámara detrás del avatar y la planta 3×3 rígida. Especificación, no implementación.

## Planta y distribución

Una planta minimalista premium, vista elevada 3/4, madera clara, marfil, plantas, pantallas azul noche y luz cálida. Mantener **9 departamentos canónicos y 9 paneles**: Recepción, Trading, Research, Quant, Riesgos, Ejecución, Comité, Performance y Sistemas. Reorganizar la geometría para asemejar la imagen aprobada, sin romper IDs/anchors ni reconstruir todo desde cero. Macro, Fundamental, ESG y Legal pueden ser pods visuales, no departamentos backend adicionales. Quitar sofás Recepción y cristales obstructivos. Pasillos amplios, paredes cutaway y Performance/Sistemas accesibles.

## Cámara y movimiento

**Cámara isométrica elevada estilo Sims** como vista inicial, azimut fijo, seguimiento suave, avatar visible y paredes recortables. Flechas ↑↓←→ trasladan en las **direcciones de pantalla** (arriba/abajo/izquierda/derecha); avatar gira automáticamente hacia el movimiento. Diagonales normalizadas, delta time, animaciones idle/walk/turn sin foot sliding, colisiones reales. No WASD, mouse-look ni OrbitControls en juego. Vista global opcional.

## NPC e interacción

**16 NPC sentados:** Recepción 1, Trading 3, Research 3, Quant 2, Riesgos 2, Ejecución 1, Comité 1, Performance 1, Sistemas 2. Nueve principales abren sus paneles automáticamente a ~2,0m, rearme ~2,8m, sin activar a través de paredes ni reabrir tras cierre hasta alejarse. Siete secundarios son ambientación; 30 roles IA P4 independientes.

## Videowall enorme superior

Pantalla panorámica en pared norte/superior visible desde vista global, con PAPER ONLY, cartera/NAV/posiciones **solo P3**, operaciones **solo P6**, mercados/noticias **P2 si verificados**, riesgo **P5**, agentes **P4**. Antes de cada fase mostrar «No disponible», no números ficticios de la imagen conceptual. Fullscreen DOM por botón «Ver centro de control», sin NPC obligatorio.

## Rendimiento y QA

Referencia Windows 11 Intel Core 5 120U, 16GB RAM, Intel Graphics 1920×1080. Objetivo 45–60 FPS, mínimo sostenido 30 medido en movimiento. LOD para 16 NPC, sombras limitadas, DPR adaptativo, DOM sin polling por frame. Capturas **reales** de cámara Sims, videowall, 9 salas/paneles, offline y P0 PAPER_ONLY; la imagen generada no es evidencia funcional.
