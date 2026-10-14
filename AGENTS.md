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

## Fuente de verdad consolidada (2026-10-15)
- Leer **`docs/ESPECIFICACION_DEFINITIVA_2026_10_15.md`** como documento rector y **`docs/PROMPT_CODEX_EJECUCION_COMPLETA_P1_P2.md`** como instrucción ejecutable. Referencia visual **PNG original** (NO SVG) en `assets/REFERENCIA_APROBADA_MANIFIESTO.md`; copiar desde ZIP de handoff y verificar hash antes de afirmar que está en GitHub.
- El usuario quiere **dinero virtual pero precios/datos reales**; los fills de P6 son simulación documentada, no operaciones reales. Tras 15 días paper no se habilita live automáticamente.
- Las 30 funciones IA son **roles lógicos bajo demanda**; 16 NPC son ambientación. P2 fuentes máximas útiles, Agent Reach público, Vibe auditado y Liquid bloqueado si scope trade. Mantener P1+P2 autorizados y STOP antes de P3.

## Requisito definitivo de perspectiva (aprobado 2026-10-14)
- **Cámara isométrica elevada estilo Los Sims**, orientación fija y seguimiento suave; avatar completo visible, paredes cutaway, sin cámara detrás.
- **Flechas screen-relative:** ↑ arriba, ↓ abajo, ← izquierda, → derecha de pantalla; avatar gira automáticamente hacia la dirección de movimiento, **las flechas NO giran cámara ni avatar manualmente**. No WASD, mouse-look ni OrbitControls.
- **16 NPC sentados ambientales** (9 principales + 7 secundarios), 9 paneles por proximidad, videowall superior con cartera P3, operaciones P6, mercados/noticias P2, riesgo P5 y agentes P4; no cifras inventadas.
- **30 roles IA lógicos P4**, no 30 LLM simultáneos; hasta 30 presets Vibe auditados, 6–10 activos inicialmente.
- **Integraciones:** Agent Reach lectura pública P2; Vibe viabilidad P2 y quant/swarms P4–P5; Liquid OAuth read+trade prohibido en PAPER ONLY, investigar solo API pública read-only sin credenciales.
- Fuente vinculante: `docs/PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md`. Trabajo autorizado ahora P1 correctivo + P2; STOP antes de P3.

## Prioridad vigente: revisión P1 + P2 (2026-10-14)
- Juego normal **solo flechas** para navegar; no WASD ni ratón para orientar la cámara. Cámara isométrica elevada, orientación fija y seguimiento automático; ratón reservado a interfaces DOM.
- **9 monitores físicos + 9 paneles**, abiertos automáticamente por proximidad al agente principal de la sala; no E/clic obligatorios. Histéresis para evitar reapertura tras cerrar. **16 NPC profesionales sentados** con animaciones de trabajo puramente ambientales: agentes IA reales P4 aún NO DISPONIBLES.
- Recepción sin sofás; cristales sin bloqueo de paso; Performance y Sistemas redistribuidos; mejor caminar/iluminación/calidad sin degradación grave Intel.
- Excepción de alcance expresamente autorizada: **corrección final P1 + inicio P2 en una ejecución con gates separados**, siguiendo `docs/PLAN_EJECUCION_P1_P2.md` y `docs/PLAN_P2_CHECKPOINTS.md`. STOP antes de P3. Preservar el código LOCAL.

## P2 — conectividad máxima viable (petición posterior del usuario)

- **No limitar P2 a siete fuentes.** Seguir el catálogo [docs/P2_CATALOGO_MAXIMO_FUENTES.md](docs/P2_CATALOGO_MAXIMO_FUENTES.md): **34 modalidades de acceso de ~31 proveedores distintos** (19 públicas, 15 con registro o gratuitas condicionadas; BLS, CoinGecko y OpenFIGI tienen dos modalidades), más fuentes oficiales especializadas.
- Priorizar integraciones públicas sin clave, **activación bajo demanda** con cache/cuotas y derechos verificados. Preparar conectores opcionales con clave, sin registrarse ni comprar por el usuario. Diferenciar **candidata / implementada / conectada real / utilizable**. No declarar conexión solo por mock.
- Si un proveedor falla, registrar motivo y continuar con otros. No crear decenas de stubs. Reutilizar parser/HTTP/SDMX compartidos.
- Excepción muy limitada de **POST estadístico de solo lectura** para OpenFIGI mapping y BLS v2, únicamente host+ruta+verbo allowlisted y testeados; **nunca POST a bróker, exchange, cuentas, órdenes ni trading**. Mantener POST /api/orders = 403.

## Protocolo de ahorro de tokens
- Leer docs/00_INDICE.md y el ticket activo; abrir **solo los documentos relevantes**.
- Trabajar una fase o sub-tarea acotada por turno, salvo el encargo P1 final + P2 expresamente autorizado con checkpoints; no cargar todo el repositorio sin necesidad.
- Preferir diffs y cambios locales; no reescribir módulos estables ni pegar archivos completos en respuestas.
- Guardar decisiones, tests, bloqueos y siguiente paso en STATUS.md.
- Selección **manual** de modelo por el usuario: Sol Medio para rutina; Sol Alto para 3D; Astra Alto para arquitectura, finanzas críticas y auditorías. Ver docs/18_MODELOS_Y_TOKENS.md.
- Escalar solo el problema difícil y regresar a Sol después; evitar agentes paralelos masivos y modo de consumo acelerado.

## Protocolo de ejecución
Inspeccionar → plan breve → implementar → pruebas → revisión visual/financiera → actualizar STATUS → resumen. Si algo no funciona o no está autorizado, mostrar motivo y marcar NO DISPONIBLE. Nunca fingir una integración o una operación.

## Seguridad operativa
La IA nunca controla directamente órdenes ni excepciones al riesgo. El motor determinista de riesgo y el kill switch mandan siempre. UNKNOWN en una orden de bróker significa reconciliar antes de cualquier reintento.
