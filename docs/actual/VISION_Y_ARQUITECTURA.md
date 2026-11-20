# JAIME: mandato de producto y arquitectura vigente

Fecha: 27-10-2026. Estado: **dirección de producto; no certifica funciones implementadas**. Sustituye las prioridades contradictorias de documentos anteriores. Estado comprobado en [auditoría](AUDITORIA_2026_10_27.md); ejecución en [roadmap](../../tasks/ROADMAP.md).

## Objetivo

Construir una plataforma personal de investigación financiera y simulación cuantitativa que mantenga un universo amplio de empresas e instrumentos, detecte cambios relevantes, investigue por iniciativa propia, formule y contraste estrategias, descarte las frágiles y explique sus decisiones. La rentabilidad es un resultado que habrá que medir fuera de muestra y después en PAPER; nunca un criterio que se pueda garantizar ni obtener maquillando pruebas.

La oficina 3D sigue siendo la entrada y la representación del equipo. El trabajo efectivo pertenece al backend y continúa con la oficina cerrada mientras el proceso esté encendido. Las mesas, NPC y animaciones representan trabajos existentes; no crean una falsa sensación de actividad.

## Continuidad y autorización

Se recuperó el chat **Construye la base P0 de JAIME**, ID `01a13611-17ff-7b03-aefd-647474ba97b9`. En su último turno el usuario respondió expresamente: «Autorizo P5, pero antes haz lo que te he pedido. Se mas critico y mejora el producto».

**P5 y P6 Alpaca PAPER están autorizadas.** Después de la reorganización, el usuario ha confirmado en este chat el circuito de seis etapas descrito abajo y encargado su organización e implementación profesional. No repetir permisos de fases ni por cada trabajo autorizado. LIVE queda excluido. La autorización no sustituye pruebas ni abre el transporte de órdenes antes de tener datos, riesgo y reconciliación.

Persisten: coste obligatorio de servicios 0 EUR, entorno Windows local de ~16 GB RAM, MASTER separado de 10.000 EUR ficticios, secretos locales, API localhost y órdenes deshabilitadas. No contratar feeds ni servicios. Cualquier límite externo debe convertirse en una capacidad visible, no en datos inventados.

> Continuidad actualizada 17-11-2026: contratos IBKR, n8n piloto, núcleo sintético B3.1, acceso acotado D1 y captación D2 con fixtures entregados. Archivo real IBKR pendiente de derechos. Orden único en [ROADMAP](../../tasks/ROADMAP.md), próxima entrega D3 (sin implementar) en [ACTUAL](../../tasks/ACTUAL.md). Este diseño no crea otra cola.

## Circuito operativo acordado

Diseño objetivo, no capacidades completadas. Mantener una sola cola en ROADMAP; este apartado detalla los seis pasos pedidos por el usuario.

| Etapa | Responsabilidad y salida comprobable | Condición para avanzar |
|---|---|---|
| 1. n8n — automatización | Horario/calendario/evento → `CycleRequest` con ID, objetivo, ventana y presupuesto; consulta de progreso y errores | Entrega repetida del evento genera un único ciclo; reinicios y solapamientos no duplican trabajo |
| 2. SEC + Alpaca + IBKR | Datos versionados, universo, cuenta PAPER de solo lectura, manifests y estado de cobertura | Identidad, licencia, frescura, calendario y disponibilidad temporal compatibles con el siguiente análisis |
| 3. JAIME + IA | Router selecciona entre los 30 roles; dossiers, hipótesis, modelos y revisiones con evidencia | Contratos validados, lagunas explícitas, presupuestos cumplidos y resultados reproducibles/citados |
| 4. P5 — minería | Python ejecuta campañas acotadas; registra intentos, descendencia, descartes y supervivientes | Protocolo ex ante, OOS, costes, control de múltiples pruebas, estabilidad y revisión del comité |
| 5. Riesgo — decisión | `DecisionRecord`: COMPRAR/VENDER/MANTENER o ABSTENER/BLOQUEAR; razones, sizing y versión de política | Datos aptos y cuenta reconciliada; capital, concentración, liquidez y pérdida dentro de límites |
| 6. Alpaca PAPER | Intento validado → orden idempotente → eventos/fills → conciliación → atribución | Veto vigente inmediatamente antes del envío; estados desconocidos reconciliados; contabilidad consistente |

El bucle vuelve a investigación mediante eventos de nueva información, desvíos entre modelo y resultados, deterioro de estrategias o incidencias de datos/ejecución. Una caída de precio no obliga a generar una operación. MANTENER es una decisión con evidencia; ABSTENER/BLOQUEAR describe falta de base o veto, nunca una falsa recomendación de mantener.

### n8n y JAIME: responsabilidades separadas

n8n Community ya está instalado localmente para el piloto SEC, con persistencia y secretos protegidos; su editor y webhooks no se expondrán públicamente por defecto. [La edición Community sin licencia de pago admite self-hosting](https://docs.n8n.io/hosting/). Su implantación ocurrió en B2.5; el circuito completo continúa pendiente.

**Implementación B2.5, 06-11:** n8n Community 2.46.6 local instalado, flujo SEC de seis horas publicado y dos ejecuciones reales del mismo ciclo verificadas. Nueva agenda SEC con n8n como propietario; A21 conserva su agenda distinta. CycleRequest, presupuesto, cola, recuperación y revisión contable residen en JAIME; no se ha activado el circuito completo B5/B6. [Entrega y límites](ENTREGA_B2_5.md).

JAIME será dueño del estado del ciclo, colas internas, recursos, reintentos e idempotencia. n8n enviará una solicitud autenticada y pequeña y consultará el resultado; no ejecutará lógica de trading en nodos de código ni almacenará corpus financieros en su historial. El contrato incluirá versión, `event_id`, `cycle_id`, `correlation_id`, ventana UTC, objetivo allowlisted y hash del payload. Mismo ID con contenido distinto: rechazo. Duplicado: devolver resultado/estado previo. Eventos atrasados, replay, acumulación y cancelación tendrán políticas explícitas.

Horario de sesión bursátil validado contra el calendario del mercado, con timezone explícita y DST; no basta un cron en hora española. [Schedule Trigger usa la zona del workflow o instancia](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/). El scheduler actual de JAIME y n8n no podrán disparar simultáneamente la misma agenda. La integración migrará una agenda piloto, con modo sombra y elección explícita de propietario. No añadir Redis/workers distribuidos antes de medir la necesidad: [queue mode introduce broker y workers](https://docs.n8n.io/hosting/scaling/queue-mode/).

Operación local: funciona sin la oficina abierta mientras los servicios y PC estén encendidos. Reinicio: recuperar checkpoints y conciliar antes de continuar; nada equivale a disponibilidad con el equipo apagado. Notificaciones solo de incidentes/cambios accionables, no spam de cada agente.

### Datos e investigación

Separar tres universos: empresas conocidas, instrumentos con investigación suficiente e instrumentos aptos para estrategia/ejecución. No lanzar 30 inferencias por cada activo. Router por evento, especialidad, coste y evidencia; CPU/IO/LLM presupuestados, una inferencia local como máximo. Paralelismo entre tareas independientes y dependencias explícitas cuando un revisor necesita un resultado previo.

Adaptación Anthropic dentro de los roles existentes: constructor de modelo determinista con fuentes/celdas y escenarios; analista de resultados que compara actual/prior/supuestos y consenso únicamente cuando exista; revisor independiente que prueba conciliaciones, sensibilidad y comparables. Modelos y documentos conservan versión y fecha de conocimiento. Texto externo no puede cambiar herramientas, objetivos o límites.

[Revisión de proveedores](PROVEEDORES_Y_COBERTURA.md): el catálogo actual sí incluye acciones; la cobertura histórica admisible sigue pendiente. Alpaca, SEC e IBKR deben alimentar una ingesta por lotes con cobertura declarada. Una clave o una conexión HTTP no acredita todos los datasets, derechos o casos de uso.

### Minería y comité

Campañas de cientos o miles de variantes se ejecutan en lotes con presupuesto finito, checkpoints y cancelación. El número es un techo de búsqueda, no una medida de calidad. Registrar antes de ejecutar hipótesis, parámetros, parentesco, dataset y protocolo; no ocultar variantes descartadas o fallidas.

Separar train/validation/OOS cronológicamente; registrar exposición al holdout, incluso heredada. Walk-forward y purga/embargo cuando las etiquetas/posiciones lo requieran. Evaluar costes adversos, dependencia de unos pocos días/activos, estabilidad, regímenes y diversidad. Controles de múltiples pruebas con supuestos y muestras suficientes; una cifra Sharpe no es aceptación. Cero supervivientes es un resultado legítimo. Comité recibe tanto razones favorables como fallos y desacuerdos; nunca puede saltarse un veto de datos/riesgo.

### Riesgo y Alpaca PAPER

Política versionada: universo permitido, exposición bruta/neta, concentración por activo/sector/factor, turnover, drawdown/pérdida, liquidez, spread, reserva de caja, órdenes abiertas y antigüedad de precios. Valores concretos se calibrarán con benchmarks y pruebas, no se fijan como constantes supuestamente óptimas. Riesgo determinista, independiente del LLM y de n8n; evalúa exposición reservada por órdenes pendientes para impedir carreras entre propuestas.

Una decisión incluye motivo, estrategia/versión, datos y cuenta utilizados, expiración y límites. El gateway revalida frescura, cuenta y riesgo justo antes del envío. `DecisionRecord` no es permiso permanente. Solo host PAPER allowlisted, credenciales PAPER separadas y comprobación de cuenta. LIVE permanece rechazado por código.

OMS durable y outbox: `client_order_id` determinista vinculado a intención; confirmar por consulta y eventos. Timeout tras enviar → UNKNOWN, consultar antes de reintentar. Gestionar rechazo, fill parcial, cancelación concurrente, suspensión de mercado y desconexión. No duplicar fills por eventos repetidos. [Alpaca permite identificar y consultar órdenes por `client_order_id`](https://docs.alpaca.markets/us/docs/working-with-orders).

Reconciliar posiciones, efectivo, actividades y órdenes; divergencia bloquea nuevos envíos. Kill switch bloquea intenciones y aplica política de cancelación; no significa liquidar automáticamente. Ledger MASTER, experimentos y cuenta ALPACA_PAPER no se mezclan. El saldo de Alpaca no se fuerza a coincidir con los 10.000 EUR ficticios del MASTER.

Primero fixtures/fault injection y simulador interno como prueba del gateway; después prueba PAPER externa con mínimos límites, seguida de forward observado. [PAPER no modela todos los efectos de ejecución real](https://docs.alpaca.markets/us/docs/paper-trading): medir esas diferencias y no presentar su rentabilidad como garantía.

### Supervisión y aceptación transversal

Cada pantalla responde: qué sabe, de qué fecha, qué está haciendo, qué produjo y qué lo bloquea. Centro de activos con cobertura; ficha de especialista; laboratorio de campañas; decisiones con razones; órdenes y conciliación; operaciones del sistema. Logs técnicos en detalle, no como contenido principal.

Métricas: porcentaje del universo con identidad/cobertura útil, latencia de publicación→ingesta, tareas completadas/bloqueadas, errores de fuente, uso de recursos, reproducibilidad de trials, pérdida OOS y deriva, slippage simulado, rechazos y descuadres de conciliación. Cada métrica con definición y fuente. Ningún gate se aprueba contando tests o agentes solamente.

## Resultados de producto

1. **Conocer el universo:** buscar una empresa, ver sus instrumentos, documentos, cuentas, cotizaciones, cobertura, huecos y capacidad real para cada análisis.
2. **Saber qué ocurre:** mostrar cotización y momento de mercado, última recepción, retraso, calendario y fuente; alertas por cambios materiales y por pérdida de cobertura.
3. **Entender empresas:** estados financieros normalizados, periodos y revisiones; ratios y valoraciones reproducibles con escenarios y supuestos explícitos.
4. **Investigar sin preguntas:** agenda persistente que prioriza datos nuevos, anomalías, hipótesis y revisiones pendientes con presupuestos limitados.
5. **Descubrir y falsar estrategias:** registrar todos los intentos, validar temporalidad y costes, comparar fuera de muestra, conservar descartes y medir diversidad.
6. **Supervisar con claridad:** estado operativo, últimos resultados útiles y bloqueos; abrir la explicación de cada cifra o decisión sin leer JSON ni logs.

## Arquitectura de evolución

Mantener el monolito modular FastAPI/React existente. No reescribir la aplicación ni introducir una plataforma distribuida por adelantado. Migrar por dominios y contratos conservando APIs compatibles hasta completar cada consumidor.

| Dominio | Responsabilidad | Propietario de los hechos |
|---|---|---|
| Instrumentos y empresas | Entity, Instrument, Listing, identificadores y vigencia | Registro determinista |
| Datos | Adaptadores, ingesta incremental, calidad, derechos, revisiones, snapshots | Python + fuentes verificadas |
| Research | Expedientes, documentos, features, valoraciones y evidencias | Python; LLM opcional para interpretación |
| Autonomía | Eventos, tareas, prioridades, recursos, reintentos y trazabilidad | Scheduler persistente |
| Estrategias | Hipótesis, Genome, ensayos, validación y descartes | Motor quant determinista |
| Cartera y riesgo | Propuestas, exposición y veto de límites en P5 | Motor determinista independiente |
| Ejecución | OMS, fills y reconciliación en P6 futura | Gateway PAPER separado |
| Producto | Oficina, mercados, fichas, laboratorio y supervisión | React consulta capacidades reales |

Flujo de información: **fuente → dato versionado → snapshot utilizable → análisis/experimento → evaluación → propuesta**. El flujo hacia órdenes permanece cerrado hasta P6. Cada transición conserva IDs, versiones, fechas, motivos y evidencia.

Persistencia: SQLite WAL mantiene ledger, jobs, entidades y metadatos. Evaluar Parquet particionado y consultas DuckDB para históricos y matrices grandes cuando el benchmark de la entrega de datos lo justifique; sin mover el ledger. Primero medir carga, índices, tamaño y tiempos. DuckDB es una opción documentada, no una dependencia instalada ni una promesa de velocidad en este equipo.

## Agentes: organización y ejecución

Conservar 30 roles lógicos y sus identificadores. Una persona visual puede representar varios roles, pero cada rol debe tener su ficha, mandato, entradas, resultado y actividad real. Diferenciar `definido`, `implementado`, `habilitado`, `con datos` y `ejecutándose`.

La agenda selecciona roles según necesidad y capacidad: adquisición/calidad → screening → análisis especializado → crítica/validación → síntesis. Los especialistas fundamental, macro, técnico y crédito requieren evidencias distintas. No lanzar a todos ante cualquier noticia ni repetir comités sin datos suficientes.

Presupuesto inicial conservador: una inferencia local, hasta dos trabajos quant CPU y cuatro fetches ligeros, subordinados a memoria, cuotas y carga medida. Antes de ampliar, construir ResourceGovernor con prioridades, backpressure, cancelación, timeout, heartbeat, lease, reintento acotado y recuperación idempotente. Las tareas pesadas no deben bloquear el servidor ni la oficina.

Autonomía autorizada: consultar fuentes permitidas, refrescar, priorizar, calcular, registrar hipótesis, ejecutar experimentos autorizados al superar gates y descartar candidatos. Pedir intervención solo ante cambio de mandato/presupuesto, credenciales o acción fuera de autorización. Un proveedor caído produce espera y replanificación; no una pregunta repetitiva al usuario.

El LLM recibe contexto relevante y evidencia identificable, no miles de filas ni acceso libre a shell. Puede proponer un Genome admitido e interpretar resultados; Python calcula cifras y valida. La insuficiencia de Bull/Bear/Chair no bloquea la minería determinista. No invertir más ciclos en esa conversación profunda sin una hipótesis de mejora concreta y una prueba semántica pequeña.

## Medición del progreso

- Datos: entidades descubiertas, instrumentos resueltos, porcentaje actualizado, profundidad histórica, huecos, revisiones, cobertura por campo y readiness por uso. Mostrar numerador y denominador.
- Research: trabajos iniciados por evento, resultados útiles con evidencia, abstenciones justificadas, latencia y duplicados; no contar NPC como agentes productivos.
- Estrategias: intentos totales, fallidos, descartados, contaminación OOS, supervivientes por familia, costes y estabilidad; no maximizar el número de estrategias rentables en backtest.
- Producto: tiempo para encontrar un activo, interpretar estado y abrir evidencia; teclado, responsive, frescura visible y ausencia de etiquetas falsas.
- Operación: recuperación después de reiniciar, presupuesto de recursos, cola y errores accionables. Ninguna prueba unitaria sustituye la aceptación financiera y de producto.

## Qué no construir ahora

Microservicios, Kafka, Kubernetes, un grafo o base vectorial general, nuevos frameworks de agentes, 30 modelos residentes, feed mundial de ticks, generación libre de código y conectores adicionales sin necesidad. IBKR ya forma parte de los datos B2; el ejecutor de B6 sigue siendo Alpaca PAPER. Incorporar componentes solo si resuelven una necesidad medida. La amplitud se consigue por lotes y prioridades; la profundidad, con contratos de datos y validación.

El detalle de fuentes y minería está en [DATOS_Y_ESTRATEGIAS](DATOS_Y_ESTRATEGIAS.md) y el de producto en [EXPERIENCIA_PRODUCTO](EXPERIENCIA_PRODUCTO.md).

17-11-2026: [D2 entregado](ENTREGA_D2_LOTES.md): cola durable/transporte aislado, 92 pruebas distintas locales/offline, sin red real. `UNVERIFIED_ACCOUNT_AND_USE_SCOPE`: archivo IBKR denegado, retención y uso local/Alpaca PAPER no acreditados; no prohibición universal. D3 debe validar identidad temporal, calendario/gaps, acciones corporativas y readiness antes de B3.2.
