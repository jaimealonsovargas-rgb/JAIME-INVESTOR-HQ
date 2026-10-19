# Prompt maestro para Codex — P4 estabilización + watchlist estilo referencia + integraciones seguras

> Copiar desde aquí al agente Codex. Este encargo **continúa P4**, no inicia P5/P6. La captura de watchlist aportada por el usuario en el chat es una **referencia de diseño**, no una fuente de precios. Si Codex no puede verla, solicitarla o usar la descripción exacta del gate UI, sin inventar un PNG en el repo.

## Misión y reglas

Trabaja sobre **`jaimealonsovargas-rgb/JAIME-INVESTOR-HQ`**. Lee en este orden `AGENTS.md`, `STATUS.md` (entrada superior), `docs/evidencias/P4/README.md`, `docs/AUDITORIA_P4_CALIDAD_HUD_INTEGRACIONES_2026_10_19.md`, `docs/PLAN_P4_AGENTES_RESEARCH_LOCAL_AI.md`, `docs/INTEGRACIONES_TERCEROS_VERIFICACION.md` y solo los módulos/test relacionados.

**Objetivos simultáneos:** (1) arreglar la calidad real y la diferenciación Bull/Bear/Chair sin falsificar aceptación; (2) transformar watchlist y rail derecho al diseño negro minimalista de la captura; (3) activar de forma incremental solo las partes auditadas y seguras de Agent Reach/Vibe, mantener Liquid bloqueado si no existe permiso read-only; (4) conservar P1–P3 y todas las barreras de PAPER ONLY.

**No negociables:** coste adicional de servicios 0 EUR; `orders_enabled=false`, `POST /api/orders=403`; no órdenes reales ni paper P6, no broker scopes de trade; MASTER EUR 10.000 ficticios/0 posiciones y ledger inmutable; 30 roles lógicos, 1 inferencia local/2 quant/4 fetch; no APIs LLM de pago; no fabricar datos, cotizaciones, históricos, sparklines, rendimientos, desacuerdos ni pruebas; P5/P6 fuera de alcance; sin secretos en Git ni frontend.

## Q0. Preflight y sincronización GitHub — antes de tocar código

Ejecuta `git status --short`, `git branch --show-current`, `git log -10 --oneline`, `git remote -v`, `git fetch origin`, `git log origin/main -10 --oneline`. Compara `HEAD` con `origin/main`. Verifica que incluye commits P4 `64049f7`, `65d976d`, `eec3e6e`, `68a0672` y **los documentos de auditoría/prompt más recientes**. Si Cloud no contiene la versión publicada o el árbol local tiene cambios no subidos, **STOP**, explicar divergencia exacta y pedir sincronización; no reconstruir desde una versión vieja. Nunca `git reset --hard`, `git clean`, `git push --force`. Si la rama base es la correcta, trabaja con commits pequeños; integra a main por push normal/PR según política real del repo, y verifica SHA final remoto.

Realiza backup consistente de SQLite antes de cambios; valida 0004_research, MASTER hash/NAV, 30 roles, `/api/orders=403` y baseline de tests. Conserva los jobs/resultados históricos fallidos y sus hashes; no los edites para parecer exitosos.

## Q1. Diagnóstico reproducible del fallo P4

Antes de corregir, demuestra con tests/casos pequeños por qué se repiten los argumentos. Examina:
- `backend/app/research_roles.py`: `POLICY` única y restrictiva, una frase/elemento por campo, `claims` vacío.
- `backend/app/local_llm.py`: `grounded_schema` fuerza `INSUFFICIENT_EVIDENCE`, `maxItems=1` y `model_view` **borra IDs** de evidencia.
- `backend/app/research_service.py`: `brief` omite data_kind, feed, unidad, venue y razonamiento previo estructurado; reintentos; clasificación del caso.
- `backend/app/research_debate.py`: Bull/Bear/Chair solo intercambian tesis y listas, detector exacto no semántico.
- `docs/evidencias/P4/e2e-p45.json`, `e2e-p46.json`, `e2e-qwen25-p46.json`: salidas reales de ambos modelos.

No atribuyas todo a «modelo pequeño» sin aislar prompt, esquema, contexto y falta de evidencia. Usa fixtures TEST_ONLY para A/B reproducible sin contaminar P2. Registra matriz **observado / hipótesis / experimento / resultado**.

## Q2. Pipeline por objetivo y evidencia correctamente tipada

Introduce clasificación explícita `data_quality` / `macro_reference` / `investable_thesis` según pregunta, clase de activo y evidencia disponible. La referencia BCE `EXR.D.USD.EUR.SP00.A` **no es spread, plataforma, cotización ejecutable ni posición**. Para «alcance y limitaciones de la referencia BCE», generar dossier informativo con fuentes, fechas, definiciones y límites; **no forzar Bull/Bear/Chair direccionales**. Si el objetivo requiere tesis invertible y falta evidencia, abstenerse `ABSTAIN_INSUFFICIENT_EVIDENCE`, no producir contradicción artificial.

Construye `EvidencePack` estructurado por Python con IDs estables, `scope`, `data_kind`, `feed`, `venue`, `currency`, `unit`, `observed_at`, `rights`, `freshness`, `source`, observación/feature determinista y lagunas. Pasa IDs opacos al LLM, comprueba después contra manifest de evidencia inmutable; mantén contenido externo como UNTRUSTED_CONTENT. Los cálculos y cifras verificadas los produce Python Decimal, no el modelo.

## Q3. Debate de verdad o abstención explícita

Diseña contratos diferenciados, no un único `Opinion` relleno con el mismo texto:
- Bull: argumento condicional identificable, mecanismo, evidencia que lo apoya, supuesto clave, falsación.
- Bear: cita `bull_argument_id` real, contradice/limita ese mecanismo con evidencia contraria o **laguna específica**, explica qué cambiaría su juicio.
- Chair: confronta ambos con fuentes y limitaciones, clasifica calidad de evidencia y entrega síntesis de research o abstención; jamás orden.
- Para casos no invertibles: `NOT_APPLICABLE` o `ABSTAINED` documentado, no `FAILED` artificial.

Permite 2–3 argumentos cuando existan datos, sin repetición genérica ni wall of text. La vista de modelo conserva evidence IDs pero no permite seguir instrucciones externas. Valida JSON/schema, permisos, citas, cifras, datos obsoletos y roles. Añade detector determinista de duplicados/paráfrasis/solapamiento y referencias cruzadas a argumentos, con umbrales y casos negativos; **no afirmes que similitud léxica certifica razonamiento financiero**. Reintentos solo con corrección de contrato/inputs y límite estricto; códigos de error específicos sin filtrar secretos.

**Separar dos ejes de estado:** ejecución técnica `SUCCEEDED/FAILED` y calidad `ACCEPTED/REJECTED/ABSTAINED/NOT_APPLICABLE`. El Comité no puede presentar `SUCCEEDED` como conclusión válida. Dossier con límites y fuentes reales es útil aunque la IA se abstenga.

## Q4. Watchlist y rail derecho según imagen del usuario

**Estilo:** paneles negros planos y elegantes, borde gris muy fino, sans-serif clara, jerarquía «List» y «Watchlist» con chevron; cada fila amplia tiene ticker/nombre a izquierda, sparkline pequeño central y precio arriba + cambio % abajo alineados a derecha. Números tabulares, rojo/rosa para negativo, verde para positivo, estados legibles y accesibilidad sin depender solo del color. Interacción plegar/expandir y detalles de fuente al pulsar fila. **El rail derecho comparte el mismo lenguaje** en Cartera, Posiciones, Actividad y Mapa; preservar minimapa y retorno al juego. No copiar datos financieros de la imagen.

**Ancho:** revisar `FinancialHud.tsx` y `financialHud.css` (actualmente 280px). Probar una solución de aprox. 320–380px según viewport, sin tapar avatar/videowall ni robar media oficina; en pantallas menores colapsar/drawer con foco accesible. Preservar tipografía 16px de paneles, 9/9 clic NPC y 16 NPC, cámara isométrica y flechas. No reescribir P1.

**Datos:** conservar `/api/markets/watchlist` o ampliar contrato read-only con series **reales** comparables, de una sola identidad/feed/venue/moneda/unidad/frecuencia y derechos display. Un sparkline SVG ligero solo con histórico suficiente y legalmente visualizable; sin histórico → «— / Sin histórico», no dibujo decorativo. Precio/% diario únicamente si P2 los autoriza y la comparación temporal es válida; en otro caso `NO_DATA`, `STALE`, `RIGHTS_RESTRICTED` con fuente y hora. No convertir referencia BCE o IPC en cotización de NVDA. Si los símbolos de la captura se configuran como watchlist de preferencias, pueden aparecer como símbolos **sin precio** hasta obtener un proveedor autorizado; no afirmar conexión. Sin descargas de tipografías ni consultas masivas; proteger 55–60 FPS actuales, medir realmente en Windows.

Pruebas frontend: estados con datos, sin datos, stale, derechos, sin series, serie válida, teclas/foco, plegado, responsive 390/1280/1920, tabs/mapa, errores/offline. Capturas reales de ambos rails y oficina en movimiento. Si se ejecuta en Cloud, no inventar FPS Intel ni capturas locales.

## Q5. Herramientas externas «en la medida de lo posible»

Audita `docs/INTEGRACIONES_TERCEROS_VERIFICACION.md`, `assets/integrations/`, `scripts/audit_agent_reach.py`, `scripts/audit_vibe_metadata.py`, `backend/app/vibe_readonly.py`, `backend/app/data_catalog.py`.
- **Agent Reach:** ya auditado v1.5.0 para RSS BCE A20. Mantener y, si hay nuevos canales públicos legales y permitidos, implementar de uno en uno con allowlist host/ruta/verbo, límites, derechos, pruebas y estado real. Sin cookies, login, redes sociales privadas, DMs, shell o escritura. No contabilizar Agent Reach como nueva fuente si solo es el cliente de A20.
- **Vibe-Trading:** pin v0.1.16, 30 presets **METADATA_ONLY**. Solo portar factores/presets read-only deterministas auditados con tests, provenance y licencia; nunca instalar/activar runtime completo, generated-code runner, broker tools, órdenes ni auto-upgrade. Un YAML importado no cuenta como estrategia ejecutada ni como agente competente.
- **Liquid Co-Invest:** mantener `BLOCKED_TRADE_SCOPE` si OAuth mezcla read+trade; no conectar ni pedir credenciales. Investigar únicamente documentación pública oficial sobre un scope realmente read-only separado y gratuito; no inferir que existe. No abrir cuenta/contratar servicios.
- **Otros nombres:** si «las herramientas de ayer» se refiere a herramientas distintas, **NO ADIVINAR**; registrar `REQUIRES_USER_IDENTIFICATION` y solicitar nombres exactos en el reporte. No habilitar herramientas con costes, credenciales o permisos de escritura sin autorización específica.

Entrega una matriz `herramienta | versión/pin | capacidad | permisos | coste | pruebas reales | estado | bloqueo/siguiente paso`.

## Q6. Pruebas y aceptación

Reejecuta tests actuales, añade casos semánticos y de regresión; no basta con incrementar el contador. Demuestra:
1. Caso de referencia BCE → informe correcto, sin spread ficticio ni Bull/Bear obligatorio.
2. Fixture TEST_ONLY de tesis invertible → Bull y Bear argumentan mecanismos distintos, Bear referencia ID Bull, Chair sintetiza diferencias verificables; nada inventado se convierte en hecho real.
3. Caso sin evidencia → abstención visible, sin relleno.
4. Modelo sin servidor → NO_LOCAL_MODEL, sin fallback remoto.
5. Los dos modelos locales **ya probados** se evalúan tras corregir prompts/schema; no descargar tercero sin autorización. Si siguen fallando, P4 queda bloqueada por calidad, pero el modo determinista funciona.
6. No hay cambios en MASTER ni ledger; `POST /api/orders=403`; ninguna escritura broker.
7. UI sin sparklines/precios ficticios, provenance/freshness y diseño parecido a referencia, 9/9 NPC, responsive, accesibilidad, rendimiento local real cuando disponible.
8. Backup/reinicio, cancelación/timeout, concurrency 1/2/4, tests de prompt injection y restricciones de integraciones.

Publica evidencias **auténticas** (fixtures marcados TEST_ONLY, outputs reales con hashes, screenshots, logs, mediciones con entorno). Actualiza `STATUS.md` y task P4. Mantén P4 **pendiente** si la calidad no alcanza el gate. STOP antes de P5/P6.

## Entrega y sincronización final obligatoria

Haz commits normales y `git push origin main` si tienes permiso y el remoto no diverge. Verifica con `git fetch origin` que `git rev-parse HEAD` == `git rev-parse origin/main`. Si no puedes publicar, reporta el bloqueo y NO digas que está sincronizado. Nunca force push.

En el informe final proporciona: SHA local/remoto; resumen de causas confirmadas; cambios en prompts/esquemas/selección; caso BCE y caso invertible con calidad de aceptación; ambos modelos y benchmarks; rail izquierdo/derecho con capturas; número de series/precios realmente autorizados; matriz Agent Reach/Vibe/Liquid; tests, FPS y limitaciones; hash/NAV MASTER, /api/orders=403, coste 0, STOP antes de P5/P6. **No declares P4 terminada hasta pasar el gate semántico con evidencia.**
