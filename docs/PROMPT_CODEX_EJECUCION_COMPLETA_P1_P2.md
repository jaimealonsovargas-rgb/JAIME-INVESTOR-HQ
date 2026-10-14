# PROMPT COMPLETO PARA CODEX — JAIME INVESTOR HQ

Quiero que ejecutes **P1 correctivo + P2 completo** conforme a TODAS mis decisiones consolidadas. No reconstruyas el proyecto, no reabras decisiones ya aprobadas y no pierdas trabajo LOCAL.

## A. Preflight y documentos obligatorios

1. En VS Code/workspace ejecuta `git status --short`, `git log -5 --oneline`, `git diff --stat`, comprueba rama/remoto y si hay cambios no subidos. El **código LOCAL es la fuente de verdad** de la última ejecución. Prohibido reset/clean/force/pull destructivo. Sincroniza de forma segura los documentos nuevos de `origin/main`; si hay conflictos, conserva cambios y resuélvelos.
2. Lee **en orden**: `AGENTS.md`, `STATUS.md`, `docs/ESPECIFICACION_DEFINITIVA_2026_10_15.md`, `docs/PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md`, `docs/PLAN_EJECUCION_P1_P2.md`, `docs/PLAN_P2_CHECKPOINTS.md`. Para fuentes: `docs/P2_CATALOGO_MAXIMO_FUENTES.md`. Para terceros: `docs/INTEGRACIONES_TERCEROS_VERIFICACION.md`. Consulta el resto solo cuando sea necesario.
3. **IMAGEN ORIGINAL APROBADA:** hay un ZIP de handoff con dos PNG originales. Copia `JAIME_HQ_SIMS_VIDEOWALL_APROBADA.png` y `JAIME_HQ_SIMS_BASE.png` a `assets/reference_images/` y verifica SHA-256 contra `assets/REFERENCIA_APROBADA_MANIFIESTO.md`. **El SVG es solo un plano, NO la imagen aprobada.** Si no tienes el ZIP en el workspace, pide que se coloque; no inventes otra imagen y puedes avanzar en tareas no dependientes de la referencia. Versiona los PNG reales en commit cuando estén disponibles.

## B. Diseño definitivo aprobado

- **Oficina 3D minimalista tipo Los Sims**, vista isométrica/3/4 elevada, una planta luminosa con madera clara, marfil, plantas, mesas y monitores, comité central, recepción frontal, despachos laterales y una **PANTALLA PANORÁMICA ENORME ARRIBA**.
- Cámara isométrica de orientación fija con seguimiento suave; flechas ↑↓←→ para **moverse en direcciones de PANTALLA**, no para girar. El avatar gira automáticamente. No WASD, no mouse-look ni OrbitControls en juego; animación natural sin foot sliding.
- Mantén **9 departamentos y 9 paneles**, aunque Macro/Fundamental/ESG/Legal sean pods visuales adicionales. Recepción sin sofás, cristales sin bloquear pasillos, Performance y Sistemas bien diseñados.
- **16 NPC profesionales sentados**: Recepción 1, Trading 3, Research 3, Quant 2, Riesgos 2, Ejecución 1, Comité 1, Performance 1, Sistemas 2. Son ambientación, no 16 LLM. Los 9 principales activan los paneles automáticamente al acercarse ~2m, con histéresis/rearme ~2,8m, Escape, chequeo de sala y sin E/clic.
- Videowall superior con **SIMULACIÓN PAPER ONLY**, cartera/NAV/posiciones (solo P3), operaciones/fills (solo P6), mercados/noticias (P2), riesgo/comité (P5), agentes (P4), sistemas/proveedores (P2). Modo fullscreen DOM. **Nunca usar cifras ni titulares inventados de la imagen**: mostrar PENDIENTE/NO DISPONIBLE hasta que existan datos/ledger/jobs/fills reales.

## C. Ejecuta P1.S0–P1.S4

Reutiliza código local y corrige layout/cámara/controles/colisiones/NPC/animaciones/paneles/videowall; optimiza Intel Graphics 1920×1080, objetivo 45–60 FPS, mínimo sostenido 30 medido. Screenshots **reales** de navegador (vista Sims general y videowall, Recepción, Trading, Comité, Performance, Sistemas, interacción en 9 salas); no sustituir por render conceptual. Checkpoints con tests y commits separados.

## D. Ejecuta P2.0–P2.6: máximo de fuentes gratuitas utilizables

Construye registry de instrumentos/proveedores/capabilities; normalización Decimal/UTC/venue/fuente/timestamp/delay/derechos; cache, TTL, cuotas, fallback semántico, offline, backoff y Data Quality. **~31 proveedores / 34 modalidades CANDIDATAS**, no conectadas por el mero hecho de figurar en un listado. Prioriza BCE, Banco de España, INE, Eurostat, OCDE, Banco Mundial, BIS, Treasury, SEC, BLS, FMI viable; cripto market-data-only, GDELT, OpenFIGI, ESMA; después FRED, BEA, EIA, Alpha Vantage, Alpaca Basic IEX, T212 DEMO, Twelve Data y free tiers viables. No scraping no autorizado. Cada fuente debe mostrar CANDIDATE/IMPLEMENTED/CONNECTED/USABLE con evidencia HTTP real, fecha, derechos y motivo de bloqueo. Mocks no son conexiones. Integrar mercados/noticias en videowall **solo con datos verificados**.

**Agent Reach:** auditoría/instalación aislada cuando sea seguro; solo fuentes públicas legales, RSS/IR/reguladores/metadata; no cookies de mis cuentas, scraping de redes sin permiso, likes/posts/DMs. Noticias con fuente, URL, autor, fecha, deduplicación y protección prompt injection.

**HKUDS/Vibe-Trading:** auditar licencia MIT y terceros, dependencias, coste, seguridad y compatibilidad Windows; entorno aislado y solo read-only/viabilidad en P2. Planificar 30 roles IA lógicos P4 y hasta 30 presets upstream auditados, 6–10 activos inicialmente; NO ejecutar ahora swarms ni Python generado inseguro, no instalar brokers ni modelos de pago.

**Liquid Co-Invest:** investigar endpoints públicos read-only gratuitos y derechos. Su OAuth estándar concede read+trade, por tanto **NO conectar su MCP/OAuth/cuenta/wallet** ni siquiera en paper mode; registrar BLOCKED si no hay read-only demostrable.

Puedes preparar backend P2 aislado mientras corriges P1; no integrar P2 en UI hasta estabilizar P1. Si faltan claves, marcar NO_CREDENTIALS y continuar, sin registrar cuentas ni comprar servicios.

## E. Arquitectura futura que debes respetar, pero NO implementar ahora

- **P3:** ledger MASTER único de **10.000 EUR virtuales**, append-only, NAV/caja/FX/dividendos/comisiones, sin doble contar cuentas demo.
- **P4:** **30 roles IA especializados** bajo demanda, 1 inferencia LLM local gratuita como máximo por defecto, 2 trabajos quant CPU y 4 fetches ligeros; sin LLM local, roles NO DISPONIBLES y análisis deterministas. Presets Vibe auditados.
- **P5:** comité Bull/Bear/CIO, riesgo determinista con veto/kill switch, backtests point-in-time/walk-forward/costes, sin promesas de rentabilidad.
- **P6:** compras y ventas **PAPER con precios de mercado verificables**, spreads/slippage/fees/FX/sesiones, reconciliación y blotter. Acciones líquidas/ETFs/caja inicialmente; sin apalancamiento/cortos/derivados. Bróker paper/demo solo en fase autorizada y nunca live.
- **P7:** QA integral, seguridad, rendimiento, backups, documentación.
- Aunque 15 días paper sean positivos, **nunca activar trading real automáticamente**.

## F. Seguridad, pruebas y entrega

**Invariantes:** 0 EUR adicional; PAPER ONLY; no fondos reales; no secretos en repo/frontend/prompts/logs; no datos/beneficios/trades/jobs/FPS/tests inventados; `/api/orders` sigue 403 y `orders_enabled=false` en P1/P2. No abrir OAuth trade de Liquid ni endpoints de órdenes live. No perder cambios locales.

Trabaja por gates con commits separados. Ejecuta `python scripts/manage.py check`, `python scripts/manage.py audit`, `git diff --check`, builds/tests frontend/backend y E2E/Chrome/FPS cuando sea posible. Actualiza `STATUS.md` con hechos verificados, capturas reales, FPS, conectores probados, licencias, bloqueos, commits y próximo paso. Si no hay red o credenciales, registra NO VERIFICADO, no finge éxito.

**Tienes autorización para pasar de P1 a P2 cuando superen gates, sin detenerte para pedir permiso. STOP ABSOLUTO ANTES DE P3.**
