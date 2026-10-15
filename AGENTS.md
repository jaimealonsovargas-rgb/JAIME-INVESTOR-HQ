# Instrucciones permanentes para Codex

## Invariantes no negociables
1. Coste obligatorio de servicios igual a **0 EUR**. No crear infraestructura facturable ni compras de créditos.
2. **PAPER ONLY**: nunca enviar órdenes a endpoints live ni usar fondos reales. Defensa en profundidad en código y tests.
3. La pantalla inicial es la **oficina 3D estilo Los Sims con cámara isométrica elevada** (no cámara detrás del avatar), 9 departamentos/paneles, 16 NPC sentados, videowall enorme superior y solo flechas screen-relative; ver `docs/PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md`.
4. No inventar cotizaciones, trades, beneficios, trabajos de agentes, resultados de tests, disponibilidad de APIs o licencias.
5. Ledger maestro de **10.000 EUR ficticios** separado de cuentas paper de brókeres; sin doble conteo.
6. Cada fase exige tests, revisión de seguridad, evidencia visual cuando corresponda y actualización de STATUS.md.
7. Secretos solo en .env local; nunca en frontend, logs, capturas, repositorio o prompts.
8. Fuentes y modelos 3D gratuitos con licencia comprobada y atribución registrada.
9. Español para interfaz y comunicación; identificadores de código pueden ser ingleses.

## Fuente de verdad consolidada
- La visión visual/arquitectónica sigue en `docs/ESPECIFICACION_DEFINITIVA_2026_10_15.md` y `docs/PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md`.
- **Decisión posterior 2026-10-16:** P3 está autorizado según `docs/AUTORIZACION_P3_2026_10_16.md`; el plan ejecutable es `docs/PLAN_P3_LEDGER_CARTERA_Y_HUD.md` y la task `tasks/P3_CARTERA.md`. Esta decisión sustituye los antiguos `STOP antes de P3`. **STOP vigente antes de P4**.
- El usuario quiere **dinero virtual pero precios/datos reales**; los fills de P6 serán simulación documentada, no operaciones reales. Tras 15 días paper no se habilita live automáticamente.
- Las 30 funciones IA son **roles lógicos bajo demanda**; 16 NPC son ambientación. P4 NO está autorizado todavía.

## Requisito definitivo de perspectiva
- **Cámara isométrica elevada estilo Los Sims**, orientación fija y seguimiento suave; avatar completo visible, paredes cutaway, sin cámara detrás.
- **Flechas screen-relative:** ↑ arriba, ↓ abajo, ← izquierda, → derecha de pantalla; avatar gira automáticamente hacia la dirección del desplazamiento, **las flechas NO giran cámara ni avatar manualmente**. No WASD, mouse-look ni OrbitControls.
- **16 NPC sentados ambientales** (9 principales + 7 secundarios), 9 paneles por proximidad, videowall superior con cartera P3, operaciones P6, mercados/noticias P2, riesgo P5 y agentes P4; no cifras inventadas.
- **30 roles IA lógicos P4**, no 30 LLM simultáneos; hasta 30 presets Vibe auditados, 6–10 activos inicialmente, pero P4 sigue fuera de alcance.
- **Integraciones:** Agent Reach lectura pública P2; Vibe viabilidad P2 y quant/swarms P4–P5; Liquid OAuth read+trade prohibido en PAPER ONLY.

## Prioridad vigente: P3 ledger MASTER + HUD profesional (2026-10-16)
- P1/P2 se consideran base cerrada: no reabrir layout, providers o integraciones salvo regresión necesaria para P3.
- Crear **una sola** cartera MASTER de 10.000,00 EUR virtuales con seed idempotente, ledger append-only, Decimal, doble entrada, lotes FIFO, FX, NAV, P&L, snapshots y rentabilidad trazable.
- Consumir precios/FX P2 con proveedor, timestamp, quality/rights/frescura. Si falta o está stale: estado explícito, nunca valor cero inventado.
- UI P3: rail izquierdo **Watchlist/Market Pulse** con datos P2; rail derecho **Cartera / Posiciones / Actividad / Mapa**; videowall activa Cartera/NAV/Posiciones. Órdenes/fills siguen `P6 — NO DISPONIBLE`.
- Durante P3 `POST /api/orders = 403` y `orders_enabled=false`. No agentes P4, riesgo P5 ni ejecución P6.
- La nitidez del videowall puede mejorarse si no reabre el diseño 3D ni degrada de forma relevante el rendimiento.
- Gate final P3 exige tests financieros, regresión P1/P2, backup/restore, evidencia y actualización de STATUS. **STOP antes de P4**.

## P2 — conectividad base preservada
- Mantener el registry, normalización, caché/cuotas/derechos y estados verificados ya implementados. No inflar el recuento de fuentes ni reconsultar masivamente sin necesidad.
- Diferenciar **candidata / implementada / conectada real / utilizable**. No declarar conexión solo por mock.
- Los POST read-only estadísticos allowlisted de OpenFIGI/BLS v2 no alteran la prohibición de ejecución: **nunca POST a bróker, exchange, cuentas, órdenes ni trading** durante P3.

## Protocolo de ahorro de tokens
- Leer `docs/00_INDICE.md` y la task activa; abrir **solo los documentos relevantes**.
- Trabajar una fase o sub-tarea acotada por turno; no cargar todo el repositorio sin necesidad.
- Preferir diffs y cambios locales; no reescribir módulos estables ni pegar archivos completos en respuestas.
- Guardar decisiones, tests, bloqueos y siguiente paso en STATUS.md.
- Selección manual de modelo por el usuario: Sol para rutina/implementación; Astra para arquitectura, finanzas críticas y auditorías. Ver `docs/18_MODELOS_Y_TOKENS.md`.
- Evitar agentes paralelos masivos y consumo innecesario.

## Protocolo de ejecución
Inspeccionar → plan breve → implementar → pruebas → revisión visual/financiera → actualizar STATUS → resumen. Si algo no funciona o no está autorizado, mostrar motivo y marcar NO DISPONIBLE. Nunca fingir una integración o una operación.

## Seguridad operativa
La IA nunca controla directamente órdenes ni excepciones al riesgo. El motor determinista de riesgo y el kill switch mandan siempre cuando existan en P5. UNKNOWN en una orden futura significa reconciliar antes de cualquier reintento. En P3 no existen órdenes de usuario: cualquier BUY/SELL/FILL se limita a fixtures aislados de tests.
