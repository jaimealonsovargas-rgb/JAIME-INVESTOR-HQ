# Primer ciclo autónomo P4

Autorización: nuevo Goal del usuario tras revisar `c180800`. P4 conserva estado **PARTIAL** por el debate financiero pendiente; esta entrega implementa exclusivamente una revisión descriptiva autónoma. Ninguna inferencia Bull/Bear/Chair ni código P5/P6.

## Comportamiento

Con el backend encendido, el reloj reserva un `AutonomyEvent` y una `ResearchTask` sin abrir la oficina ni recibir una pregunta. La política `daily-descriptive-v1` solo permite `SCHEDULED_RESEARCH → DESCRIPTIVE_RESEARCH`. El router consulta A21 mediante P2, comprueba derechos/estado y selecciona el instrumento del registro usando alias verificados del feed. La configuración actual de A21 es el histórico diario agregado de BTC de CoinPaprika; no es selección multiactivo ni cotización ejecutable.

Un caso interno enlazado al evento reutiliza los jobs `data_quality`, `momentum_trend` y `volatility_regime`. Python/Decimal calcula trayectoria, rentabilidad del período, volatilidad muestral, drawdown observado y otras estadísticas descriptivas con sus evidence IDs. No se concluye una tesis de inversión. Los expedientes manuales e históricos se conservan. El texto descriptivo del caso lo genera el router; no es un disparador ni una instrucción externa.

El ciclo autónomo tiene **0 llamadas LLM**. La síntesis ordinaria manual existente sigue siendo opcional, acotada y separada; no se necesita para que la automatización funcione con `NO_LOCAL_MODEL`. Los 30 roles y límites globales 1 LLM / 2 quant / 4 fetch permanecen.

## Configuración y control

| Variable local | Predeterminado | Límite |
|---|---|---|
| `AUTONOMY_ENABLED` | `true` | `false` impide nuevas tareas y cancela las pendientes al arrancar |
| `AUTONOMY_INTERVAL_SECONDS` | `86400` | 3600–604800 |
| `AUTONOMY_STARTUP_DELAY_SECONDS` | `30` | 1–300; solo primera inicialización |
| `AUTONOMY_SOURCE` | `A21` | Única fuente autorizada en esta ruta |

La cadencia y siguiente vencimiento son persistentes. Tras varios días apagado se ejecuta como máximo una revisión pendiente, no una por cada día perdido. No hay ejecución local con el PC apagado. Se espera al reloj o a notificaciones de finalización, sin polling de trabajos. La UI consulta cada 10 segundos solo con el panel montado.

En **Sistemas** o **Research**, «Pausar automatización» persiste la pausa y cancela tareas autónomas activas; «Reanudar» conserva el siguiente vencimiento (si ya venció, podrá comenzar una única tarea). Cada tarea activa admite cancelación individual. El interruptor de entorno `false` prevalece: la UI no puede activarlo. Una petición HTTP ya en curso puede terminar, pero su respuesta tardía no crea un caso ni reactiva la tarea cancelada.

APIs locales con las protecciones Origin, `X-HQ-Research` e idempotencia existentes:

- `GET /api/research/autonomy` — estado, próxima fecha, últimas 50 tareas.
- `POST /api/research/autonomy/control` — `pause`/`resume`.
- `POST /api/research/autonomy/tasks/{task_id}/cancel` — cancelación idempotente de la tarea.

## Persistencia, límites y seguridad

`0006_autonomy` añade `autonomy_control`, `autonomy_events` y `research_tasks`. Reserva de evento/tarea/siguiente vencimiento en una transacción SQLite `BEGIN IMMEDIATE`, con claves únicas. Evento inmutable; cada transición se audita. La preparación de reinicio sucede después del bloqueo exclusivo del backend y antes de arrancar workers. En fase `PREPARED`, claves estables recuperan el mismo caso y jobs. Una consulta interrumpida en fase `FETCHING` queda `BLOCKED / RESTART_INTERRUPTED`, sin repetirla. Los trabajos agotados no se relanzan indefinidamente.

Presupuesto por tarea: una consulta P2, un intento, cero LLM, plazo lógico de 90 s; espera por el carril P2 limitada a 5 s. Se rechaza un resultado de jobs terminados después del plazo, aunque sea JSON válido. Se conserva el límite HTTP de P2. **El plazo no es una garantía de matar un hilo del sistema:** un bloqueo DNS del sistema operativo puede retrasar su liberación; no se crea otro hilo de reemplazo ni se aumenta la concurrencia. Pausa/cancelación persisten inmediatamente, con publicación tardía bloqueada.

La conexión SQLite de autonomía solo escribe sus tres tablas y auditoría. Los agentes mantienen su propia allowlist sin permiso para escribir las tablas de control. Ningún dominio P4 puede mutar ledger, cash, NAV, posiciones, órdenes o fills. MASTER permanece en 10.000 EUR ficticios; `orders_enabled=false`, `POST /api/orders=403`, coste 0 EUR.

A21 conserva los derechos P2 auditados para uso personal local, **sin redistribución ni valoración MASTER**. Una lectura de caché se identifica como tal, con la fecha de consulta original. La UI de tareas muestra un resultado histórico; el dossier revalida los derechos y vigencia actuales. Los datos privados, dossiers y capturas con precios se conservan en `output/`, nunca en Git.

## Evidencia y alcance pendiente

[Resultados reproducibles, recursos y capturas](evidencias/P4/autonomia-20261026/README.md). `scripts/qa_p4_autonomy.py` arranca un backend propio, observa por GET y comprueba reinicio/pausa/órdenes403; **no crea casos ni runs por HTTP**. Requiere puerto 8000 libre. No debe ejecutarse como un bucle de pruebas sobre la base operativa; hay que respetar la programación persistida. Los fixtures de tests se marcan `TEST_ONLY` y no se cuentan como conexiones reales.

Quedan fuera: otros feeds/rutas/universos, disparadores por filings o eventos de estrategia, ResourceGovernor general, calendarios de mercado, minería, backtests, riesgo/veto formal y ejecución PAPER. `Plan_JAIME_P5_P6.md` se conserva como diseño futuro; eventos/tareas separados de los expedientes permiten nuevas rutas autorizadas sin convertir las preguntas en la única entrada. El debate profundo no está validado y no se ha repetido en este Goal.
