# B1 — integridad de datos y fichas de especialistas

Implementación 27-10-2026; cierre 28-10-2026 (Europe/Madrid). B1 completado con pruebas locales; no cierra P4 ni activa P5/P6.

## Cambios

- Observación, revisión y descarga separadas. Los IDs ya no dependen del hash completo de la respuesta. Revisiones SEC conservadas con accession, CIK, concepto y periodo; publicación diaria como cota conservadora.
- Histórico deduplicado por identidad semántica antes de limitar la ventana. Selección `as_of` por conocimiento local y publicación; redescarga no borra la primera recepción. Recibos con hash de respuesta y IDs de revisión preservan procedencia. Los registros antiguos siguen intactos y se deduplican al leer; no se reconstruyen versiones perdidas.
- Alias de un segundo proveedor añadidos al instrumento existente; capacidades por feed conservadas. Vínculo CIK con procedencia para conectar estados financieros al instrumento correcto. Fundamental Equity exige un bundle anual coherente; valoración sigue bloqueada sin modelo/inputs de B2.
- La entrada compacta de IA conserva emisor, concepto, periodo inicial, filing y precisión de publicación. Para SEC con solo fecha, la disponibilidad se acota a las 05:00 UTC del día siguiente y también exige recepción local.
- Ficha propia por persona, con asignación de los 30 roles a los 16 puestos, especialidad, mandato, tarea actual y última entrega. Metadatos de actividad desde la base, sin exponer contenido que deba pasar los controles del dossier. Acceso mediante clic real, selector Equipo y URL `?especialista=personal-research-1`.
- Departamento, casos/entregas y diagnóstico separados. El estado de conexión del servidor no acredita capacidad. Minería/riesgo/ejecución pendientes se identifican explícitamente. Fuente y fecha visibles sin desplegar la fila de mercado. Agentes en videowall etiquetados como investigación, no ledger.
- Corregida liberación prematura de recursos 3D durante la repetición de efectos de React StrictMode: las texturas de BatchedMesh no se destruyen mientras el modelo sigue montado. Sin cambio de geometría, cámara ni estética de la oficina.

## Pruebas realizadas

1. Tres regresiones nuevas antes del arreglo: fallaron SEC (2 filings → 1 ID), histórico (60 días → 30 fechas) y alias (dos proveedores → solo uno). Después pasan.
2. **326 pruebas backend pasan** (92,21 s), con red externa prohibida en fixtures. Incluyen consulta temporal, legacy sin rewrite, redescarga/reversión, coherencia fundamental, vínculo emisor y actividad. La suite conserva pruebas de órdenes bloqueadas y aislamiento del ledger.
3. **68 pruebas frontend pasan, una omitida preexistente**. TypeScript y build pasan. Avisos de Three Clock, chunk 3D grande y deprecación Starlette/httpx quedan registrados; no justifican actualizar dependencias en este bloque.
4. Navegador Chromium sobre copia local: 1920×1080, 1366×768, 800×600 y 390×844 sin overflow horizontal de fichas. Persona → última entrega → dossier, cambio de especialidad, backend desconectado, NO_LOCAL_MODEL, fechas visibles y dato caducado, foco, Escape, clic nativo sobre NPC y cámara liberada. Sin errores JavaScript en la pasada final. 800×600 comprueba reflow; no es una certificación de zoom nativo 200%.
5. Migración `0007_data_lineage` probada primero sobre snapshot SQLite con WAL y después aplicada a la base personal. **Todas las filas de las 20 tablas preexistentes permanecen idénticas**; solo se añade `data_downloads` y cambia versión Alembic. Backup privado: `output/b1-before-0007.db`.
6. Cierre del 28-10: **77 pruebas afectadas pasan** tras el último ajuste de fechas SEC y entrada de IA. Incluyen dos nuevas regresiones: límites de fecha en invierno/verano y conservación de la identidad financiera al compactar evidencia. Esta ejecución es posterior a la suite completa de 326; los recuentos se solapan y no deben sumarse como pruebas distintas. No se repitió navegador/build porque este ajuste solo afecta al backend.

Logs de pruebas, scripts de comprobación y snapshot de revisión están en el workspace de este chat, `work/`; capturas privadas en `output/playwright/b1/`. Evidencia portable sin precios en [cierre](evidencias/b1-closeout.json), [navegador](evidencias/b1-ui-verification.json), [migración de copia](evidencias/b1-migration-copy.json), [migración aplicada](evidencias/b1-migration-applied.json) e [inventario de proveedores](evidencias/b1-provider-inventory.json). No se publican datos ni capturas personales en Git.

## Límites y trabajo siguiente

- La consulta de historia todavía recorre el archivo de una fuente; es correcta para el volumen actual, no un benchmark de miles de emisores. B2 introducirá partición/índices y evaluación de volumen.
- `as_of` local no equivale a un dataset de mercado point-in-time completo. La migración no puede recuperar revisiones destruidas por el parser anterior. Es necesaria una nueva ingesta controlada.
- El enlace CIK está preparado y probado con fixtures. No se han fabricado acciones ni unido la base por nombres/tickers ambiguos. El registro personal sigue sin acciones.
- SEC continúa como preset y con cuatro conceptos. Modelos DCF, consensus, transcripts, cobertura masiva y minería no se presentan como implementados.
- n8n y Alpaca PAPER están autorizados por el usuario dentro del circuito objetivo, aún sin activar. Las claves Alpaca y contacto SEC siguen pendientes de configuración segura. Órdenes continúan bloqueadas; LIVE fuera de alcance.

Siguiente bloque único: [B2](../../tasks/ACTUAL.md). [Circuito acordado](VISION_Y_ARQUITECTURA.md) · [Suficiencia de proveedores](PROVEEDORES_Y_COBERTURA.md).
