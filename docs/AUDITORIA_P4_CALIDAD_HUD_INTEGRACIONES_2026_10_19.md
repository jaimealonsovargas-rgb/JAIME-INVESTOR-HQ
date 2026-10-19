# Auditoría técnica P4 — calidad semántica, HUD y terceros (2026-10-19)

**Base verificada:** GitHub `main` en `68a06721bc0574c1a73bdff33e167442673735ab` antes de esta documentación. Fuente: código de `backend/app/`, `frontend/src/world/`, `STATUS.md` y `docs/evidencias/P4/`. **No se han ejecutado pruebas ni medido FPS desde esta auditoría remota**. Las cifras son las declaradas y archivadas por Codex, no verificaciones independientes en este entorno.

**Decisión:** P4 **no aceptada semánticamente**. P1–P3 se preservan. El objetivo de esta iteración es **estabilizar P4, mejorar los dos rails usando la captura aportada por el usuario como referencia visual y evaluar integraciones seguras**. **STOP antes de P5/P6**. No cambiar cartera, dinero, broker ni orden.

## A. Hechos observables y fallos

1. **Infraestructura funcional, resultado semántico bloqueado.** `STATUS.md` y `docs/evidencias/P4/README.md` registran 182 pytest, 49 Vitest, build/TS y auditoría exitosa, clic 9/9, 30 roles, 98 instrumentos y MASTER 10.000 EUR/0 posiciones. No equivalen a 30 analistas competentes ni a un dossier aprobado. Qwen3-1.7B Q8_0 y Qwen2.5-1.5B Q4_K_M fallaron la distinción Bull/Bear; Chair quedó bloqueado en los runs p4.6. No usar `SUCCEEDED` mecánico como sello de calidad.
2. **El contrato empuja a la repetición.** `backend/app/research_roles.py` usa una `POLICY` compartida que fuerza frases muy cortas, **un solo elemento por lista**, `claims` vacío, prohíbe números/identificadores en tesis y obliga a `INSUFFICIENT_EVIDENCE`. `backend/app/local_llm.py:grounded_schema` refuerza `research_view=INSUFFICIENT_EVIDENCE`, `claims.maxItems=0` y arrays de un elemento. Roles distintos producen salidas formalmente válidas pero informativamente idénticas. **Hipótesis causal respaldada por código, no benchmark A/B.**
3. **El modelo pierde los IDs que necesitaría para citar.** `LocalLLM.chat().model_view` elimina recursivamente `id` y `evidence_ids` antes de crear el prompt. `research_service.py` selecciona evidencia para el `brief` pero el LLM recibe solo recortes `scope/freshness/excerpt`, no contrato semántico completo de feed/venue/unidad/tipo/serie. `attach_extracts` añade extractos verificados en Python; esto no verifica las interpretaciones narrativas ni da al Bear pruebas estructuradas para refutar.
4. **Bull/Bear/Chair reciben contexto insuficiente.** `research_debate.role_context` pasa solo `thesis`, `risks` y `key_disagreements`; no argumentos estructurados, premisas, evidencias citadas, contradicciones ni incertidumbre. El comentario de Chair sobre recibir ambos lados «en full» no coincide con esa proyección reducida. `validate_debate` solo detecta tesis exactamente iguales tras quitar caracteres no alfanuméricos; no garantiza contradicción semántica ni evita paráfrasis vacías. El rechazo evita falsos éxitos, pero no soluciona el razonamiento.
5. **Caso de prueba mal emparejado con el debate de inversión.** Los runs usan la serie de referencia FX BCE `EXR.D.USD.EUR.SP00.A` y preguntan por el alcance de una referencia, no por una tesis invertible sustentada en fundamentos. La salida registrada confunde `reference rate`, spread, plataforma y posición MASTER. **No forzar Bull/Bear sobre un caso de calidad de datos**. El motor debe seleccionar pipeline por tipo de instrumento, objetivo, evidencias suficientes y `data_kind`; permitir abstención informativa explícita.
6. **El tratamiento de errores no siempre explica la causa.** En p4.6 Qwen3 el Bear aparece `INVALID_RESULT_OR_RUNTIME`, que agrupa errores distintos. Hay reintentos sin corrección material de los inputs. Añadir diagnósticos seguros, versionados y no sensibles; diferenciar JSON/schema, semántica, evidencia, falta de datos y runtime. No exponer prompts completos, datos personales ni secretos.
7. **La watchlist actual no es la referencia visual solicitada.** `FinancialHud.tsx` muestra `Lista`, selector CORE/OPPORTUNITIES/PORTFOLIO, filas `details` con estado/fuente y Market Pulse. `financialHud.css` fija ancho de rail en 280 px (260 en breakpoints), cabeceras/filas más densas y **no implementa sparklines**. La captura del usuario usa negro puro, jerarquía limpia `List → Watchlist`, símbolo a izquierda, sparkline central y precio/% a derecha, filas amplias, línea fina y acento rosa/rojo. Se puede emular el lenguaje visual, **pero los precios de NVDA/MSFT/AAPL/BTC/ETH/SOL/XRP de esa imagen son SOLO REFERENCIA VISUAL, no datos del proyecto**.
8. **Faltan series de cotización aptas para minigráficos.** P3 registra que en la cache no había cotizaciones redistribuibles verificadas. `/api/markets/watchlist` sirve lo permitido por P2, no una watchlist de siete símbolos con series homogéneas. No dibujar zigzags ficticios, no mezclar índice, tipo BCE, precio de exchange o `market_quote`, no inventar variación diaria ni atribuir realtime sin prueba. `NO_DATA/STALE/RIGHTS_RESTRICTED` visibles, con fuente/fecha en detalle.
9. **Integraciones existentes no equivalen a conexión total.** `docs/INTEGRACIONES_TERCEROS_VERIFICACION.md`: Agent Reach 1.5.0 auditado para RSS público (A20 BCE vía cliente seguro HQ); Vibe-Trading 0.1.16 auditado **METADATA_ONLY**, 30 YAML/presets desactivados; Liquid Co-Invest bloqueado porque OAuth estándar incluye `read+trade` y no se confirmó API gratuita de solo lectura. No instalar Vibe completo ni enlazar broker, cookies o OAuth peligroso para aumentar contadores.

## B. Plan de corrección y aceptación

### Gate Q0 — sincronización, seguridad y baseline
- `git status --short`, `git fetch origin`, `git log -10 --oneline`, `git log origin/main -10 --oneline`, `git remote -v`; verificar que `HEAD` contiene **estos documentos** y los commits visuales/P4 previos. Preservar modificaciones locales. Nunca `reset --hard`, `clean` ni force push.
- Backup SQLite consistente, comprobar migración 0004, hash MASTER, API orders 403, 30 roles y regresión.
- Guardar fixture de las salidas reales p4.5/p4.6 para evitar regresión; no reescribir historial ni declararlo válido.

### Gate Q1 — adecuación de tareas y evidencia
- Clasificar casos por `research_goal` (data_quality, macro_reference, investable_thesis), asset class, data_kind, venue/feed, unidad, derechos, freshness y suficiencia.
- Crear un **paquete tipado de hechos** desde Python: facts y métricas deterministas, `evidence_id` opaco, `scope`, `observed_at`, `source`, `unit`, `feed`, `data_kind`, limitaciones y lagunas. No pasar como cotización una referencia BCE ni como spread un fixing.
- Si la pregunta es alcance de serie BCE, entregar un informe de datos/restricciones; debate direccional `NOT_APPLICABLE` o `ABSTAIN_INSUFFICIENT_EVIDENCE` sin simular desacuerdo ni convertirlo en error de ejecución. Un caso invertible sin evidencia suficiente también debe abstenerse honestamente.

### Gate Q2 — debate diferenciable y evaluable
- Sustituir el esquema uniforme por contratos de salida **por rol y objetivo**. Bull: premisa favorable **condicional**, mecanismo, `supporting_evidence_ids`, supuesto, refutación posible. Bear: `target_bull_argument_id`, objeción específica, `counter_evidence_ids` o `evidence_gap`, prueba de falsación. Chair: mapa de desacuerdos, calidad/suficiencia, decisión de research **o abstención**, no BUY/SELL.
- Conservar evidencia IDs en la vista del LLM de manera segura, sin dar autoridad a contenido externo; resolver contra manifest inmutable en Python. Separar hechos verificados de hipótesis y narrativas no verificadas.
- No forzar un solo ítem o la misma tesis por rol. Presupuesto de tokens/contexto acotado, sin que la respuesta se convierta en un muro de texto; permitir 2–3 argumentos distintos cuando haya evidencia.
- Validador semántico con reglas deterministas: Bear debe referirse a argumento concreto de Bull y ofrecer mecanismo de objeción/limitación distinto; Chair debe mencionar desacuerdo verificable; detectar igualdad y duplicación por solapamiento sin confiar en un LLM-juez como verdad. La aceptación humana sigue siendo obligatoria.
- Pruebas con: (a) fixture TEST_ONLY invertible de tesis y contra-tesis claramente diferenciadas, etiquetado TEST_ONLY; (b) referencia BCE real como caso `data_quality` sin Bull/Bear artificial; (c) caso sin datos; (d) prompt injection; (e) dos modelos locales existentes. No convertir fixture en precio real.
- Separar estado de **ejecución** (`SUCCEEDED/FAILED`) de **aceptación** (`ACCEPTED/REJECTED/ABSTAINED/NOT_APPLICABLE`) en API/UI/evidencias; un run completo no implica dossier aceptado.

### Gate Q3 — rails visuales de la referencia del usuario
- Usar captura como **inspiración de layout**: negro `#000` o `#050505`, contorno gris sutil, título `List` / `Watchlist`, filas con ticker negrita a la izquierda, sparkline pequeño en medio **solo con serie real** y precio + variación alineados a derecha. Verde/rojo con contraste accesible, no depender solo del color. Cabeceras plegables, buen espaciado y tipografía sans-serif local legible.
- Reconciliar anchura con oficina 3D 1920×1080: probar 320–380 px por rail según viewport y overlay, evitando tapar videowall, avatar y controles; responsive y colapso manual. El rail derecho debe compartir diseño (Cartera/Posiciones/Actividad/Mapa) sin fingir operaciones P6.
- Series de sparkline: mínimo suficiente de puntos reales comparables (misma identidad de instrumento, feed, venue, moneda, unidad, periodicidad), orden temporal, frescura y derechos. SVG ligero accesible; **sin serie → guion/«Sin histórico»**, no línea falsa. Precio y % diario solo si comparables y permitidos; si no, `NO DISPONIBLE`. Evitar consulta masiva/polling rápido.
- Símbolos de la imagen solo si se añaden como preferencias explícitas de watchlist; nunca crear datos ni cotizaciones. Etiquetas de fuente, horario, feed y estado disponibles por expansión/tooltip accesible; no saturar cada fila.
- Test visual en viewport real y captura de ambas barras, no solo test DOM. Preservar clic NPC 9/9, 16 NPC, cámara, controles, minimapa y 3D.

### Gate Q4 — terceros, solo conectividad real y segura
- Inventariar Agent Reach, Vibe-Trading y Liquid desde sus **pins y auditorías actuales**. Para cada herramienta: `INSTALLED / METADATA_ONLY / READ_ONLY_VERIFIED / BLOCKED / NOT_VERIFIED`, versión, permisos, licencia, coste, derechos, red, tests.
- Agent Reach: ampliar solo canales públicos, RSS y GET permitidos con allowlist y derechos; sin cookies/login/DM/shell/escritura. No duplicar A20 como proveedor nuevo.
- Vibe: considerar solo presets/factores deterministas **auditados y portados** a HQ con tests de equivalencia y licencia, sin ejecutar Python generado, tools de broker ni runtime completo. El YAML por sí solo no es agente operativo.
- Liquid: mantener `BLOCKED_TRADE_SCOPE` mientras no exista API/documentación oficial que pruebe acceso separado read-only y uso gratuito autorizado; nunca intentar OAuth read+trade.
- Para otras herramientas que el usuario haya mencionado y no figuren en los documentos: **solicitar nombres exactos antes de integrarlas**; no adivinar ni registrar cuentas. Secretos siempre en `.env` local.

### Gate Q5 — QA y entrega
- Tests focalizados de routing/abstención/semántica/grounding/errores + regresión 182 backend/49 frontend como **baseline**, no como cifras futuras garantizadas; TypeScript/build/audit.
- Repetir benchmark de los **dos modelos ya descargados** y comparar outputs, tiempo, tokens/s, memoria y tasa de aceptación, sin descargar un tercero salvo autorización. Si ambos fallan, `BLOCKED_SEMANTIC_QUALITY` y un modo determinista de research útil, no resultados fabricados.
- Capturas reales, trazas auditables sin secretos, pruebas 9/9 NPC, estados sin modelo, reinicio, derechos/stale, HTTP `/api/orders=403`, hash/NAV MASTER intacto. FPS Intel bajo carga local real; si no se ejecuta en Windows, `PENDIENTE VALIDACIÓN LOCAL`.
- Actualizar `STATUS.md`, task/issue y evidencia con **aceptado vs pendiente**; commit y push normal a `origin/main`, comprobar `HEAD == origin/main`. **STOP antes de P5/P6**.

## Referencias locales de esta auditoría
- `backend/app/local_llm.py`, `research_roles.py`, `research_debate.py`, `research_service.py`, `research_contracts.py`
- `frontend/src/world/FinancialHud.tsx`, `financialHud.css`, `frontend/src/portfolioApi.ts`
- `docs/evidencias/P4/README.md`, `e2e-p45.json`, `e2e-p46.json`, `e2e-qwen25-p46.json`
- `docs/INTEGRACIONES_TERCEROS_VERIFICACION.md`, `docs/P3_IMPLEMENTACION_Y_VALIDACION.md`, `AGENTS.md`

**Alcance de la auditoría:** lectura remota de fuentes versionadas; no se han ejecutado tests, probado APIs en vivo ni medido FPS en este análisis.
