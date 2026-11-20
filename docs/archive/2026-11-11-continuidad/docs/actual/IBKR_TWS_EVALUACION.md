> ARCHIVO INACTIVO · copia anterior a la auditoría del 11-11-2026. Sus próximos pasos y autorizaciones no gobiernan el trabajo actual. Enlaces relativos reubicados; contenido histórico conservado.

# Interactive Brokers / TWS API — evaluación para JAIME



Evaluación del 09-11-2026, Europe/Madrid. Actualización 11-11: el usuario ha creado la cuenta de simulación e instalado TWS; completado [piloto aislado de contratos solo lectura](../../../../../integrations/ibkr/README.md). Revisión posterior de contratos/divisa USD [conciliada con SEC/Alpaca y archivada](../../../../actual/ENTREGA_B2_3_CONTRATOS_IBKR.md). No hay proveedor continuo integrado, precios/históricos IBKR verificados ni órdenes. El resto de esta evaluación conserva su contexto inicial. Coste obligatorio 0 EUR y PAPER ONLY intactos.



## Conclusión



Recomiendo evaluar IBKR como adaptador adicional para identidad de instrumentos y cobertura de mercados, empezando en solo lectura. Mi propuesta es mantener Python como autoridad de investigación/riesgo, n8n como coordinador y SEC como fuente contable. IBKR puede aportar conectividad financiera; no sustituye la minería, la validación estadística ni garantiza rentabilidad. Tampoco sustituiría ahora la ruta Alpaca PAPER prevista en B6.



## Qué aporta y cómo encaja



TWS API conecta el cliente a una sesión de TWS o IB Gateway mediante socket. TWS sirve para inspección inicial; propongo Gateway para la operación habitual por su menor carga de interfaz. No es una clave REST que se pega en `.env`: la aplicación intermediaria requiere sesión autenticada. El modo Read-Only bloquea órdenes API. [Configuración oficial](https://interactivebrokers.github.io/tws-api/initial_setup.html).



| Necesidad de JAIME | Adaptación propuesta |

|---|---|

| Identidad y moneda del instrumento | Guardar ContractDetails, conId, secType, currency, exchange, primaryExchange, símbolo local y fecha de recepción; comparar con SEC/Alpaca y documentar diferencias. |

| Precios de distintas plazas | Suscripciones solo para una watchlist pequeña, según permisos reales; tipo de dato recibido y antigüedad explícitos. |

| Históricos para minería | Cola incremental con caché, intervalos y controles de huecos; no descarga indiscriminada del catálogo. |

| Autonomía | Un gestor de sesión en backend y una cuota central para todos los roles; n8n solicita trabajo, nunca habla directamente con el broker. |

| Simulación futura | Adaptador independiente detrás del motor de riesgo y OMS en B6, tras superar pruebas de reconciliación y los controles de ejecución. |



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



## Orden de incorporación



Actualización del 09-11: el usuario confirma que todavía no tiene cuenta. Diagnóstico local ejecutado; sin SDK ni aplicación en rutas estándar. [Preparación, discrepancia trial/Paper y continuidad](IBKR_PILOTO_PREPARACION.md). No dar por válida la prueba gratuita como fuente de históricos.



1. **Ahora:** evaluación documental cerrada; comprobar viabilidad de cuenta/paper, términos y datos a coste cero. Sin estos requisitos IBKR permanece candidato y B2 continúa con las fuentes existentes.

2. **B2, piloto opcional de lectura:** resolver los tres contratos actuales y una acción europea claramente identificada. Verificar divisa/plaza contra evidencia, sin fusionar automáticamente registros. Ninguna orden.

3. **B2, después de ese piloto:** histórico diario acotado, derechos, ajustes, cobertura, duplicados, pacing, reinicio y presupuesto de almacenamiento. Comparar contra otra fuente con semántica compatible.

4. **B3/B4:** experimentos solo si el dataset supera sus controles, manteniendo todas las carencias de supervivencia/temporalidad. El nuevo proveedor no da readiness por sí solo.

5. **B5/B6:** considerar ejecución IBKR PAPER como alternativa documentada a Alpaca, después de riesgo/OMS/reconciliación y pruebas de fallos; no activar por esta investigación.



Aceptación del piloto futuro: cero escrituras de órdenes, identidad inequívoca, permisos comprobados, etiquetas de retraso correctas, pérdida/reanudación de sesión sin duplicados, cuotas compartidas y almacenamiento controlado. Los secretos y autenticación permanecen en el equipo. No se ha añadido IBKR al catálogo como conexión operativa ni contado como proveedor verificado.

