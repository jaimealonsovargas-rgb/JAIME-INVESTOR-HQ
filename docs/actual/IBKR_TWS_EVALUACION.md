# Interactive Brokers / TWS API — evaluación para JAIME

Evaluación del 09-11-2026, Europe/Madrid. Actualización 11-11: el usuario ha creado la cuenta de simulación e instalado TWS; completado [piloto aislado de contratos solo lectura](../../integrations/ibkr/README.md). Revisión posterior de contratos/divisa USD [conciliada con SEC/Alpaca y archivada](ENTREGA_B2_3_CONTRATOS_IBKR.md). No hay feed continuo ni órdenes; D1 verificó acceso acotado según actualización inferior. El resto de esta evaluación conserva su contexto inicial. Coste obligatorio 0 EUR y PAPER ONLY intactos.

Actualización 16-11: [D1 completado](ENTREGA_D1_IBKR_DATOS.md), histórico diario y cotización diferida recibidos para AAPL. Sin archivo de precios; los derechos de archivo/minería y el resto de cobertura siguen pendientes. Las conclusiones iniciales inferiores conservan su fecha, no sustituyen esta prueba.

## Conclusión

IBKR está incorporado a la ruta de datos de B2: contratos y acceso acotado D1 probados; D2 de lotes entregado con fixtures y archivo real bloqueado. Python mantiene investigación/riesgo, n8n coordinación y SEC contabilidad. La ruta ejecutora de B6 sigue siendo Alpaca PAPER. Las capacidades de diseño siguientes no se consideran implementadas por el éxito del piloto de contratos.

## Qué aporta y cómo encaja

TWS API conecta el cliente a una sesión de TWS o IB Gateway mediante socket. TWS sirve para inspección inicial; propongo Gateway para la operación habitual por su menor carga de interfaz. No es una clave REST que se pega en `.env`: la aplicación intermediaria requiere sesión autenticada. El modo Read-Only bloquea órdenes API. [Configuración oficial](https://interactivebrokers.github.io/tws-api/initial_setup.html).

| Necesidad de JAIME | Adaptación propuesta |
|---|---|
| Identidad y moneda del instrumento | Guardar ContractDetails, conId, secType, currency, exchange, primaryExchange, símbolo local y fecha de recepción; comparar con SEC/Alpaca y documentar diferencias. |
| Precios de distintas plazas | Suscripciones solo para una watchlist pequeña, según permisos reales; tipo de dato recibido y antigüedad explícitos. |
| Históricos para minería | Cola incremental con caché, intervalos y controles de huecos; no descarga indiscriminada del catálogo. |
| Autonomía | Un gestor de sesión en backend y una cuota central para todos los roles; n8n solicita trabajo, nunca habla directamente con el broker. |
| Datos para simulación | Contratos y series verificadas para experimentos; el ejecutor vigente de B6 es Alpaca PAPER, con riesgo y OMS propios. |

`reqContractDetails` puede devolver varios contratos: solo aceptar una resolución inequívoca. IBKR recomienda conId y exchange para identificar contratos; currency y primaryExchange ayudan a desambiguar. **Inferencia de diseño:** esto puede resolver parte del bloqueo de divisa del piloto, pero conId no demuestra por sí solo CIK, continuidad temporal o universo histórico. SMART representa enrutamiento y no debe convertirse automáticamente en la plaza primaria o un MIC. [Contrato](https://www.interactivebrokers.com/docs/tws-api/doc/contracts/object), [ContractDetails](https://www.interactivebrokers.com/docs/tws-api/doc/contracts/details).

## Límites decisivos

**Datos y presupuesto.** La documentación indica que, salvo datos diferidos de watchlist, el acceso de mercado API normalmente requiere suscripciones. Poder ver un gráfico en TWS no prueba que el usuario tenga permiso para obtenerlo por API. No he verificado la cuenta, país, clasificación profesional, mercados ni suscripciones del usuario; no asigno un precio ni doy por disponible un feed gratuito. Con 0 EUR obligatorio, cualquier cobertura que exija pago se marca PLAN_REQUIRED y queda detenida. Un feed diferido es para exploración, no se etiqueta como tiempo real ni como apto para ejecución. [Datos de mercado](https://www.interactivebrokers.com/docs/tws-api/doc/md/introduction), [históricos oficiales](https://interactivebrokers.github.io/tws-api/historical_data.html).

**Miles de empresas no son miles de streams.** El valor por defecto documentado es 100 líneas simultáneas; las peticiones generales se limitan en función de esas líneas, normalmente 50 por segundo con esa asignación. No implica 50 descargas históricas grandes por segundo ni 100 empresas como límite del universo investigable. Propuesta: catálogo amplio, investigación por lotes y stream de candidatos seleccionados. La disponibilidad efectiva debe medirse en la cuenta. [Pacing oficial](https://www.interactivebrokers.com/docs/tws-api/doc/pacing-limitations).

**Históricos incompletos para investigación universal.** Hay restricciones por instrumento, antigüedad y tamaño de barra; faltan, entre otros, valores que ya no cotizan, y cambios de plaza pueden cortar historia. Esto deja riesgo de sesgo de supervivencia. Las reglas estrictas de barras pequeñas no se extrapolan indiscriminadamente a barras diarias, que conservan limitaciones y throttling propios. **Conclusión:** IBKR sería una fuente complementaria, no un dataset universal libre de sesgos para P5. [Limitaciones históricas](https://interactivebrokers.github.io/tws-api/historical_limitations.html).

**Autonomía de sesión.** Existen reinicios diarios y reautenticación periódica; el auto-restart no acredita operación permanente sin intervención. Guardar checkpoints, detectar datos viejos, cancelar suscripciones huérfanas y resuscribir tras reconectar. No automatizar MFA ni guardar la contraseña en scripts. [Auto-restart oficial](https://www.ibkrguides.com/traderworkstation/auto-restart-considerations.htm?Highlight=auto+restart).

**PAPER y licencias.** La documentación de paper vincula su disponibilidad a una cuenta regular aprobada y financiada y advierte diferencias de ejecución respecto a real. No se ha comprobado elegibilidad del usuario y no se solicita depósito. La licencia del código API y los derechos de datos son cuestiones distintas: no asumir que autorización para consultar concede almacenamiento ilimitado, redistribución o uso comercial. Revisar los términos aplicables antes de habilitar el adaptador. [Limitaciones y paper](https://www.interactivebrokers.com/docs/tws-api/doc/notes-limitations/tws-api-limitations), [licencia de API](https://interactivebrokers.github.io/index.html).

## Diseño técnico propuesto, todavía sin implementar

Un adaptador Python con SDK oficial revisado y versión fijada, compatible con nuestro Python/Windows antes de instalar. No añadir un wrapper externo por defecto. Un solo gestor de conexión alimenta cola de eventos, caché y consultas para los 30 roles; no 30 conexiones al broker. Mantener operaciones permitidas explícitas, transporte local, cliente identificado y reconexión limitada.

Persistir contratos y recibos versionados. Separar moneda/unidad del contrato de moneda base de la cuenta. Precios con proveedor, contrato, plaza/feed, tipo recibido —real, diferido o congelado—, timestamp observado y recibido. Históricos con intervalo, zona, sesión regular/extendida, ajustes y evidencia de derechos. Integrar cada lote en `StorageGovernor`; la instalación de Gateway, sus logs y caché externa necesitan inventario adicional porque no están en data/output.

Estados propuestos: NOT_CONFIGURED, AUTH_REQUIRED, CONNECTING, CONNECTED_READ_ONLY, NO_ENTITLEMENT, DELAYED, STALE, PACING_WAIT y DISCONNECTED. Estar conectado no acredita frescura ni cobertura. Tras reconexión, verificar contratos/suscripciones y evitar duplicados; preservar errores de acceso en lugar de cambiar de fuente silenciosamente. En una fase ejecutora futura, cuenta PAPER allowlisted y reconciliación explícita: el número de puerto por sí solo no acredita que una cuenta sea simulada.

## Orden vigente

La evaluación inicial queda conservada en el [archivo](../archive/2026-11-11-continuidad/docs/actual/IBKR_TWS_EVALUACION.md). Cuenta, SDK, contratos y acceso acotado D1 comprobados. [D2 entregado](ENTREGA_D2_LOTES.md) con fixtures/transporte offline; sin red real, archivo bloqueado por derechos no acreditados. Próximo D3 propuesto en [ACTUAL](../../tasks/ACTUAL.md). Retención y uso local/Alpaca PAPER no acreditados; no prohibición universal. No repetir pilotos.

El piloto europeo adicional no es obligatorio antes del laboratorio. Una denegación de datos se registra con límites concretos y una alternativa explícita solo si resulta adecuada y autorizada. No hay sustitución automática de Alpaca como ejecutor ni una entrega de ejecución IBKR en esta cola.
