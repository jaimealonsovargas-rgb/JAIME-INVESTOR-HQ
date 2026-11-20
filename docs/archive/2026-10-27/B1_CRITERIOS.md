# B1 — integridad de datos y claridad de producto

Archivo histórico del plan B1 preparado el 27-10-2026. Estado original conservado debajo; cierre y autorización vigente de P6 en [ENTREGA_B1](../../actual/ENTREGA_B1.md) y [STATUS](../../../STATUS.md).

27-10-2026. **PREPARADO, NO INICIADO.** La entrega actual reorganiza B0. Próxima implementación: este bloque. P5 ya autorizada después de mejoras previas; P6 pendiente.

## Resultado esperado

Abrir un activo/persona y entender capacidad, fecha, trabajo y evidencia; confiar en que revisiones e identidades no se pierden antes del análisis. No basta cambiar CSS.

## B1.1 Observaciones e históricos

Separar identidad de observación, revisión y descarga. SEC colisiona revisiones de mismo periodo; en otras series el hash completo de respuesta cambia todos los IDs al cambiar un dato. Conservar lineage y versiones sin duplicar toda la serie. Seleccionar revisión/as-of y deduplicar semánticamente antes del límite de ventana.

Regresiones: dos filings del mismo periodo conservados; revisión futura invisible en consulta pasada; dos descargas de 60 días con un dato revisado no se reducen a 30 fechas; redescarga idéntica idempotente. Backfill/migración no destructivos, lagunas irrecuperables explícitas. No inventar versiones perdidas.

## B1.2 Identidad multiproveedor y fundamentales

Instrumento ya existente debe incorporar alias de nuevo proveedor. Comprobar vínculo dato → emisor/instrumento. Alinear `fundamental_fact` con los contratos reales del especialista fundamental, comprobando conceptos/periodo/suficiencia; no aceptar cifras inconexas por cambiar un enum.

Regresiones: dos proveedores/tres descargas → una identidad y ambos aliases; colisión ticker/venue/currency legítima distinguida; fixture suficiente consumible y evidencia insuficiente rechazada.

## B1.3 Estados y fechas

Separar salud backend, capacidad implementada/habilitada, estado de trabajo y vigencia. Corregir disponibilidad basada en `/health` y `live=true`. Agentes en videowall no lleva etiqueta ledger. Rail cerrado muestra fecha del dato y feed; recepción/derechos en detalle. Ausente/caducado nunca se convierte en cero.

## B1.4 Persona y dossier

Propagar persona/rol desde clic a inspector, permitiendo varios roles por persona. Mandato, tarea actual, última entrega, fecha y evidencia antes de diagnóstico. Separar ficha de rol del formulario de nuevo caso y estado global de servidor. Conservar acceso por departamento, teclado, Escape y cámara.

## Salida y límites

Reproducir defectos con fixtures antes del arreglo; tests afectados, regresión necesaria, TypeScript/build y órdenes/ledger. Probar migraciones sobre copia aislada; fixtures nunca en base personal. Navegador: persona → trabajo → dossier, fecha visible, estados honestos, red caída, dato antiguo y LLM detenido; 1920×1080, 1366×768, ancho estrecho y zoom/teclado.

No rediseñar oficina, descargar modelos, lanzar comités largos, backtests masivos o brokers, ni mutar MASTER. Evidencia sin precios restringidos. Actualizar STATUS con comandos reales; no heredar PASS de otra fecha ni declarar P4 completa por este bloque. [Auditoría](../../actual/AUDITORIA_2026_10_27.md) · [Roadmap](../../../tasks/ROADMAP.md).
