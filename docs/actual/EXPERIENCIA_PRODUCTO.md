# Experiencia de producto: oficina y análisis

27-10-2026. **Especificación; no interfaz ya implementada.** Revisión de código y capturas históricas del 23-10, sin nueva sesión de QA de la aplicación.

## Estructura

La oficina 3D isométrica, flechas, nueve departamentos, 16 NPC y videowall se conservan. Desde ella se abren espacios DOM amplios, con regreso a la misma posición y cámara. El usuario debe entender qué ve, de cuándo es y qué puede concluir. El backend trabaja independientemente de la oficina.

| Espacio | Contenido principal | Objeto enlazable |
|---|---|---|
| Mercados | Búsqueda, filtros, precios, cobertura y frescura | Empresa/instrumento |
| Investigación | Tesis, documentos, resultados y modelos | Dossier/modelo financiero |
| Laboratorio | Hipótesis, campañas, ensayos y descartes | Estrategia/experimento |
| Cartera y riesgo | MASTER, posiciones, propuestas y límites implementados | Posición/propuesta |
| Operaciones | Roles, tareas, datos, cuotas y recursos | Agente/tarea/fuente |

Rutas estables propuestas: `/markets`, `/instruments/:id`, `/companies/:id`, `/research/:caseId`, `/agents/:roleId`, `/strategies/:id`, `/experiments/:id`. `/` conserva oficina. Preservar filtros/selección y atrás/adelante. No habilitar enlaces que aparenten capacidades inexistentes.

## Laterales

Izquierda: watchlist corta con símbolo/nombre, divisa, precio, variación de periodo explícito, sparkline comparable y **fecha/hora del dato visible en la fila cerrada**. Separar macro de cotizaciones. “Abrir mercados” lleva al universo completo con paginación; no apilar miles de filas en el rail.

Derecha: capital virtual separado, últimas entregas útiles, trabajo actual y bloqueos accionables. Cada evento abre su expediente, tarea o activo. Mostrar un límite principal y detalle extensible; no repetir todas las carencias del sistema en cada panel.

`DataStamp` distingue observación, recepción, feed directo/retrasado/EOD/indicativo y antigüedad. Persistencia UTC; UI Europe/Madrid con zona explícita. Refrescar navegador no rejuvenece el precio. Salud backend, conexión proveedor, vigencia del dato y aptitud analítica son estados separados.

## Al pulsar una persona

Propagar `person_id`, departamento y relación con `role_id`. Una persona puede representar varios roles; cada uno conserva mandato y capacidad real. No abrir el mismo formulario genérico al pulsar cualquier persona.

1. Nombre, rol, disponibilidad y última actividad.
2. Trabajo actual, activo/universo, motivo, inicio, dependencia y próximo paso. En reposo: última entrega y próxima agenda, si existe.
3. Última conclusión válida, alcance, fecha del análisis, periodo de evidencia y límite principal.
4. Actividad, Resultados y Fuentes; diagnóstico técnico secundario.
5. Abrir trabajo/activo, evidencia, pausa/cancelación permitidas. “Nueva investigación” tiene flujo propio.

Estados en español: En espera, Analizando, Esperando datos, No implementado, No pudo completar, Sin modelo local. `/health` no acredita que Riesgos o Ejecución estén disponibles. Las animaciones no acreditan trabajo IA.

## Ficha de empresa y modelos

Búsqueda/filtros por entidad, clase, mercado, moneda y cobertura; orden/paginación de servidor y total filtrado. Identidad estable, gráfico con fuente/periodo/ajustes, cuentas por periodo/filing, documentos, eventos, valoración e investigaciones relacionadas. Bonos y macro usan métricas/convenciones propias; un dato desconocido no es cero.

Integrar tres vistas inspiradas en los flujos financieros investigados: **Modelo** (históricos, supuestos, proyecciones, controles y versiones), **Resultados** (real vs anterior/guidance/estimación propia y consenso solo si existe), **Valoración** (DCF/comparables, sensibilidad, puente EV-equity y observaciones del revisor). Cada cambio enlaza a evidencia y al valor previo. Ver [adaptación de Anthropic](AGENTES_FINANCIEROS_ANTHROPIC.md).

## Laboratorio

Campañas e hipótesis, embudo de ensayos, comparación y descartes. Rentabilidad neta, benchmark, drawdown, turnover, costes, muestras y pruebas aplicables solo cuando haya resultados reales. Experimento → hipótesis original, snapshot, universo, parámetros, ventanas, búsqueda total, exposición OOS y motivo de aceptación/rechazo. “Todos los intentos” incluye errores. Ninguna etiqueta de backtest promete rendimiento futuro.

## Componentes y aceptación

Estética sobria compatible con oficina, cifras tabulares, espaciado consistente y acento dorado moderado. Orden: resultado/fecha → evidencia/límite → diagnóstico. Tablas para comparar e inspector para profundizar. Extraer `DataStamp`, `CapabilityStatus`, `TaskStatus`, `EvidenceLink`, `EmptyState`, `InstrumentTable`, `AgentInspector`, `DossierSummary` al tocar cada dominio; evitar reescritura global.

Primera entrega: capacidades honestas, fecha visible, etiqueta correcta del videowall y persona con identidad/contexto. Después: activo → dossier/modelo → experimento con selección persistente. QA 1920×1080, 1366×768, ancho estrecho, zoom 200%, teclado/Escape, red caída, datos antiguos y LLM apagado. Fixture de 5.000 registros solo prueba rendimiento, nunca cobertura real. Capturas con precios restringidos quedan privadas.
