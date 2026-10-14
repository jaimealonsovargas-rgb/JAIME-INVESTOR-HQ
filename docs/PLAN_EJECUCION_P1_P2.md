# Ejecución autorizada: corrección final P1 + desarrollo de P2

> **Decisión del usuario, 2026-10-14:** una misma ejecución de Codex debe **terminar las correcciones finales de P1 y empezar P2** siguiendo checkpoints verificables. Este documento **sustituye solo las instrucciones incompatibles anteriores** (STOP antes de P2, WASD/ratón, abrir panel exclusivamente en monitor, NPC de pie). Mantener PAPER ONLY, 0 EUR, seguridad y pruebas. **Encargo, no implementación ni resultados comprobados.**

## 1. Preflight y autoridad

- **El working tree LOCAL manda.** El main publicado todavía puede contener solo P1.B. Antes de editar: `git status --short`, `git log -5 --oneline`, `git branch --show-current`, `git diff --stat`; preservar cambios y commits no publicados. No reset, clean, force-push ni checkout destructivo. Incorporar la documentación nueva de main sin pisar código local.
- Leer AGENTS.md, STATUS.md y este encargo; para P1 solo el addendum nuevo de docs/PLAN_CIERRE_P1_BF.md y módulos locales afectados; para P2 tasks/P2_DATOS.md y docs/PLAN_P2_CHECKPOINTS.md. El issue #1 antiguo es histórico en lo que contradiga este encargo.
- **Dos workstreams con gates**, no ediciones simultáneas conflictivas: P1 corrige frontend 3D; P2.0/P2.1 pueden prepararse en backend sin interferir. **Integrar P2 en Sistemas solo después de estabilizar P1**. Avanzar automáticamente si gates verdes. Si hay bloqueo real de seguridad/licencia/datos, detener la parte afectada, preservar y reportar. Si se agota contexto, dejar STATUS y siguiente checkpoint exacto.
- **STOP antes de P3**: P2 no crea ledger, cartera, NAV, P&L, órdenes paper ni agentes operativos.

## 2. Correcciones P1 obligatorias (versión local, NO reconstruir)

| Gate | Criterio concreto |
|---|---|
| **P1.B** | **Quitar todos los sofás de Recepción**. Eliminar/reubicar mamparas/cristales que obstaculicen el paso o cámara, conservar estética de cristal útil. **Redistribuir interiores Performance y Sistemas** con puestos creíbles, accesos despejados y operador sentado; racks concentrados en Sistemas. Mantener 9 departamentos y planta 3×3. Elevar calidad de mobiliario, PBR, iluminación y skyline con rendimiento Intel. |
| **P1.C** | Movimiento normal **solo flechas**: ↑ avanzar, ↓ retroceder, ←/→ girar suavemente personaje. **No WASD ni ratón para girar cámara**. Cámara automática detrás y elevada (inicio ~3,2 m altura, ~3,8 m detrás, FOV ~65°); resolver oclusión acortando brazo, nunca volver cenital. Corregir animación idle/walk/giro, rig/retarget, foot sliding, velocidad y crossfade. Colisiones y puertas funcionales. Escape/Tab siguen siendo UI. |
| **P1.D** | Mantener **9 monitores físicos + 9 paneles DOM**, pero activar panel **automáticamente al acercarse al AGENTE PRINCIPAL de la sala**, no a la pantalla. No exigir E/clic. Radio inicial ~2,0 m entrada / ~2,8 m rearme; afinar en prueba. Comprobar sala, recorrido libre y no atravesar paredes; no activar sala vecina. Al cerrar, no reabrir hasta alejarse/reentrar. Modal accesible, pausa movimiento, Escape/cierre, conserva transform. |
| **P1.E** | **10 NPC humanos profesionales SENTADOS en puestos, trabajando VISUALMENTE**: 1 por departamento + 1 extra Trading. Seat anchors, poses correctas, typing/lectura/notas desincronizadas, sin clipping. **Ambientación, NO agentes IA P4 reales**: no inventar análisis, jobs, votos o trades. Optimizar rigs, sombras y LOD. |
| **P1.F** | Prueba navegador real de 9 salas, 9 paneles, 10 NPC, avatar, cristales/puertas, teclado, offline y P0. Capturas reales de cámara de juego; baseline LOCAL antes/después en 1920×1080 Equilibrado/DPR1, FPS/p95/draw calls/tris; objetivo 45–60 FPS, <30 sostenidos exige optimización. Tests, audit, licencias, STATUS y commits. |

**Interacción:** 1 NPC primario por sala; trigger únicamente dentro del departamento correcto y con aproximación físicamente válida; histéresis evita reapertura instantánea. El HUD puede decir «Acércate al agente» a distancia cómoda, pero **no «E · Abrir panel» junto al monitor**. Al cerrar, las flechas funcionan inmediatamente. No modificar centros de las nueve salas. No instalar assets con licencia dudosa ni herramientas grandes solo para arte.

## 3. P2: checkpoints obligatorios

Seguir [PLAN_P2_CHECKPOINTS.md](PLAN_P2_CHECKPOINTS.md) sin rediseñar P0: **P2.0** preflight/permisos → **P2.1** registry/capabilities → **P2.2** observaciones/cache/calidad/cuotas → **P2.3** SEC/ECB/Treasury → **P2.4** Alpaca Paper/T212 Demo/Twelve Data/FRED GET-only opcionales → **P2.5** selección/API/Sistemas → **P2.6** QA. Sin claves, implementar con mocks HTTP y estado NO DISPONIBLE; no inventar conectividad ni derechos de visualización. Cero órdenes.

## 4. Gates, salida y economía de tokens

Cada checkpoint: diff mínimo, tests, evidencia, STATUS y commit separado cuando sea viable. Verificar siempre /health PAPER_ONLY, orders_enabled=false y POST /api/orders 403. Ejecutar `python scripts/manage.py check`, `python scripts/manage.py audit`, `git diff --check`; probar navegador real y FPS cuando disponible. No declarar nada completado sin pruebas.

Al terminar: SHAs, P1 corregido/pendiente, P2 checkpoints hechos/pendientes, tests, FPS antes/después, capturas, proveedores realmente comprobados vs sin clave/derechos, limitaciones y próximo paso. **STOP antes de P3**. No pegar informes largos al usuario.

**Precedencia:** AGENTS.md para invariantes, este encargo para alcance/UX nueva, docs/PLAN_CIERRE_P1_BF.md para técnica P1 salvo apartados históricos, docs/PLAN_P2_CHECKPOINTS.md para P2 y STATUS.md LOCAL para hechos comprobados.