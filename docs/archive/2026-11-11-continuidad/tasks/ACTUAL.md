> ARCHIVO INACTIVO · copia anterior a la auditoría del 11-11-2026. Sus próximos pasos y autorizaciones no gobiernan el trabajo actual. Enlaces relativos reubicados; contenido histórico conservado.

# B2 — continuidad exacta



11-11-2026. B1/B2.1/B2.2 completados; B2.5 entregado. **Terminada la revisión inicial B2.3: tres vínculos empresa–acción documentados y diagnóstico reproducible de históricos. Almacenamiento y conservación entregados. Divisa del contrato observado IBKR conciliada y archivada para las tres acciones. Siguiente: identidad histórica y después ampliación histórica acotada.** B2 completo sigue abierto. Esta entrega no inicia ni amplía autorización de P5/P6.



La sede visual está aceptada y el bootstrap SEC ya realizado. [Entrega visual y evidencia](../../../actual/ENTREGA_VISUAL_SEDE.md). Continuar desde el lote contable cerrado, sin repetir esos trabajos.



Último punto guardado: [contratos/divisa IBKR en B2.3](../../../actual/ENTREGA_B2_3_CONTRATOS_IBKR.md), schema 0013, 13 tablas/18 modelos preservados. 98 tests backend y 16 frontend afectados, build y navegador correctos. No repetir instalación, migración, piloto n8n ni diagnóstico sin cambios de evidencia. n8n conserva su flujo publicado; su arranque usa `scripts/n8n_shadow.py start`. [Operación](../../../../integrations/n8n/README.md).



## Estado que debe conservarse



- SEC: 8.023 emisores/10.430 símbolos y cuentas de 100 emisores; no repetir bootstrap.

- Claves Alpaca y Trading 212 configuradas por el usuario en `.env`. Nunca imprimir, enviar al navegador ni pedir por chat. Settings restringe PAPER/DEMO.

- Alpaca: ocho endpoints comprobados el 30-10, 14.407 activos, snapshot Apple y 21 barras diarias IEX (septiembre 2026). Última operación marcada STALE a la hora de comprobación. Trading 212 Demo HTTP 200, 500 registros normalizados por el adaptador acotado; no cartera ni órdenes.

- Base actual **0013_shadow_cycles**. Backup `output/b25-before-0013.db`; 38 tablas anteriores idénticas tras migración. Conservado también el respaldo anterior `output/b24-before-0012.db`. No fixtures en base personal.

- Modelos actuales al 07-11: **Apple v7 y Microsoft v5 PASSED; Walmart v6 PARTIAL**, ratio pasivos/activos pendiente. 18 modelos en total; los 16 anteriores a la prueba programada conservan sus huellas. Plantilla `company-accounting-v3.1`, originales XBRL y recibos locales. Las pruebas de conciliación/lote/web se conservan en [B2.4](../../../actual/ENTREGA_B2_4.md); la actualización programada en [B2.5](../../../actual/ENTREGA_B2_5.md).

- UI: Centro de activos → empresa → Análisis de empresa → Modelo / Resultados / Valoración y controles. Versiones, evidencia y entregas reales en ficha de especialista.

- Segundo tramo: 435 tests backend en suite completa; después 40 afectados correctos, incluidos dos nuevos controles de precisión/balance. Cinco tests frontend afectados y build correctos. Ver [entrega B2.4](../../../actual/ENTREGA_B2_4.md).

- Cierre actual SEC/P4/Nivel 2: `manage.py check` completo, 443 backend, 93 frontend y una omisión preexistente, TypeScript/build correctos; Alembic sin drift. Evidencia privada `output/b24-filing-update-real.json`. Apple v3 corresponde al filing nuevo del 03-11, no al cambio de parser.

- Verificación del cierre contable 06-11: `manage.py check` completo, 468 backend, 95 frontend y una omisión preexistente; TypeScript/build correctos. Navegador con las tres empresas, construcción repetida, documentos oficiales y móvil; órdenes 403. Evidencia privada `output/b24-statement-batch-20261105.json`, `output/b24-batch-browser.json`, `output/b24-final-check.log`.

- Verificación B2.5 del 06-11: repetir n8n y reiniciar backend no duplica. Ledger/cartera conservados. Check final **485 backend, 98 frontend, una omisión preexistente**, build correcto. Evidencia `output/b25-real-cycle.json`, `output/b25-readiness.json`, `output/b25-browser.json`. Cierre 07-11: segundo ciclo por disparo automático, ejecución n8n `trigger/success`; agenda original restaurada y catálogo MCP opcional desactivado. Evidencia `output/b25-schedule-check.json`, `output/b25-final-runtime.json`.



## B2.4 — cierre y límites



1. Entregado: inversión, financiación, FX compatible, variación de caja y total declarado del balance; parser `sec-financials-v2`, plantilla `company-accounting-v2`. Reprocesado local con SHA-256, sin sobrescribir snapshots/modelos ni redescargar. Actualización marcada `MAPPING_UPDATED`, nunca como nueva publicación.

2. Cierre del 06-11: relaciones de cálculo de los informes originales resuelven las diferencias de presentación de las tres empresas. La web muestra las partidas y los documentos. Walmart mantiene el ratio pendiente. Comando reutilizable `scripts/review_company_batch.py`; no repetir descargas/modelos ya disponibles.

3. Entregado: filing Apple 0000320193-26-000026, presentado 03-11-2026, ejercicio terminado 26-09-2026. Evento persistente del worker SEC genera v3/NEW_PERIOD, preserva v1/v2 y no duplica la petición. [Entrega actual](../../../actual/ENTREGA_B2_4_ACTUALIZACION_Y_P4.md).

4. DCF/comparables requieren hipótesis fechadas, fuentes/peers, puente deuda/caja/capital y precio identificado. No crear un precio objetivo con supuestos arbitrarios. Consenso y transcript permanecen ausentes hasta disponer de fuente autorizada.

5. Interpretación local solo si hay modelo usable y un contrato validado para estos artefactos. La entrega actual es Python y dice NOT_REQUESTED; no cambiar ese estado para fingir inferencia.



El núcleo usa company_model.py, company_review.py, company_service.py, company_api.py y company_schema.py. Constructor Decimal y revisor racional separados; API sin red/inferencia ni órdenes. Idempotencia, versiones y evidencia persistentes. Roles reutilizados: fundamental_equity, value_quality, valuation, data_quality. No instalar plantillas Anthropic ni servicios de pago.



Day Trader revisada en commit `3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd`: las nueve skills y sus 22 archivos ya estaban vendoreados y coinciden con upstream. Incorporado el control de informe anual pendiente, limitado al catálogo local conocido. Scanner, reglas de entrada/salida, simulación y riesgo se adaptarán por sus fases y controles de datos/costes. [Revisión y propuesta concreta](../../../actual/DAY_TRADER_ADAPTACION.md).



## B2.5 — entregado



Contrato CycleRequest y n8n local en sombra: autenticación independiente, ventana UTC, cuota y presupuesto, estado persistente, cancelación inmediata y recuperación sobre cola/eventos SEC existentes. Dos ejecuciones CLI del mismo workflow recuperan el mismo ciclo; el 07-11 se observó además un ciclo iniciado por el temporizador real con una hora de prueba acotada. Agenda normal restaurada 00/06/12/18 UTC, con ventanas perdidas omitidas y sin reloj SEC duplicado. Panel de control en Sistemas. Requiere procesos locales y ordenador encendidos; sin servicio de inicio automático de Windows. No activar órdenes ni extender esta agenda a otras fuentes por defecto.



## Revisión B2.3 entregada el 08-11 — identidad e históricos



Tres vínculos fijados por evidencia SEC/catálogo, clase/contexto XBRL y huellas; no son un maestro universal ni acreditan divisa nativa o identidad histórica. Apple 21/21 sesiones raw IEX, EXPLORATORY_ONLY; Microsoft/Walmart sin histórico. Los tres BACKTEST BLOCKED. Panel de calidad y CLI de solo lectura reproducible. 509 backend/102 frontend superados, una omisión, build y navegador correctos. Evidencia `output/b23-identity-history-20261108.json`, `output/b23-identity-preservation.json`, `output/b23-identity-browser.json`. No repetir el diagnóstico salvo cambio de entradas/política.



## Almacenamiento entregado — continuidad B2



Punto exacto del 11-11: [piloto IBKR de lectura verificado](../../../../integrations/ibkr/README.md). TWS en simulación y API local Read-Only; SDK oficial instalado en entorno aislado. Cuenta exacta, reloj y tres contratos AAPL/MSFT/WMT obtenidos a las 09:38 Madrid; evidencia privada `output/ibkr-contract-probe-20261111.json`. Revisión posterior SEC/Alpaca completada y archivada: USD para los contratos observados, sin unión genérica. Siguiente: continuidad de identidad del piloto durante el histórico; después ampliación de series y piloto europeo con derechos/coste cero. No repetir instalación, ni convertir la prueba en proveedor continuo. Sin precios ni órdenes; P4 PARTIAL.



Entregado: control compartido antes de captar, 4 GiB data/12 GiB output/16 GiB conjuntos, 5 GiB libres y reserva de 512 MiB. Sin limpieza de evidencias; panel, inventario, recuperación y preservación de 11 tablas/18 modelos verificados. 525 backend y 111 frontend superados, una omisión preexistente, build y navegador correctos. [Entrega](../../../actual/ENTREGA_B2_ALMACENAMIENTO.md). No repetir inventarios ni pruebas sin cambios.



Siguiente: resolver continuidad temporal del piloto (la divisa USD del contrato observado ya está documentada), después ampliar históricos con ajustes/acciones corporativas y cobertura suficiente, bajo presupuesto. Escala y B3 requieren controles propios. [TWS API evaluada](../docs/actual/IBKR_TWS_EVALUACION.md): comprobar elegibilidad, derechos y coste cero como candidato de identidad/lectura; con piloto de contratos completado, sin derechos de precios/históricos comprobados. Si no es viable, continuar B2 con fuentes existentes; no sustituir Alpaca ni activar órdenes.



## Pendientes paralelos de B2.3



- **Entregado el 04-11** el primer cierre europeo oficial. HT (HRHT00RA0005, XZAG, EUR) ya tiene una ficha, diez observaciones y una descarga. El actualizador P2 registró éxito y programó la siguiente comprobación para el 05-11 a las 05:43 de Madrid con el servicio local activo. Buscar por ISIN o usar «Cierres europeos». Los valores y el recibo quedan en la evidencia local `output/europe-ht-pilot.json`.

- **Próxima comprobación de este piloto**. Tras publicarse otra sesión, contrastar su fecha y precio con la bolsa y comprobar que las diez observaciones anteriores permanecen consultables. Antes de ampliar a otra plaza, identificar una segunda acción y documentar divisa, unidad, derechos de uso y presupuesto de almacenamiento.



- Nivel 2 C01 Yahoo/C02 Stooq: candidatos UNOFFICIAL_SOURCE/internal/sin redistribución, no conectados. Verificar términos, endpoint, listing/divisa y preferencia oficial antes del adaptador/piloto; no inventar derechos. D038/D039 locales corresponden a D027/D028 de PR #8. 39 skills importadas con pin/licencias; PR aún abierta.

- P4 reutiliza el ciclo y dossier para nota/tesis/calendario, con evidencia y abstención. Aún faltan tesis analíticas y fuente autorizada de fechas corporativas. No ejecutar scripts vendoreados ni repetir Bull/Bear/Chair. Mantener P4 PARTIAL.



- Vínculo actual SEC/acción contrastado solo para los tres registros fijados. USD documentado para los tres contratos observados mediante IBKR. Pendientes aliases y continuidad histórica de clase/mercado/divisa, nuevas clases y otros emisores. Fuera del piloto, ticker/mercado solo generan candidatos; UUID Alpaca no confirma CIK. No heredar precio en el emisor SEC.

- Streaming/backend único y watchlist limitada con recuperación. Captación actual por solicitud; no afirmar seguimiento continuo ni tiempo real consolidado. IEX explícito, sin fallback de pago.

- Retención y presupuesto agregado implementados (D042), sin borrado automático. Revisar capacidad antes de escalar históricos/modelos. Límites de mercado: 512 MiB de originales comprimidos (reserva conservadora) y 500.000 barras. Modelos: 10.000 versiones; sin limpieza automática.



## Después



B2.5 ya está entregado en el ámbito piloto. Tras cerrar los requisitos de datos, B3 minería/todos los trials; B4 OOS, costes, robustez y comité; B5 ampliación de autonomía/riesgo; B6 OMS y Alpaca PAPER con reconciliación. Hoja de ruta única: ROADMAP.



PIT actual es conocimiento local desde descarga. Sin LIVE, pagos ni órdenes en B2. P4 semántico sigue PARTIAL y no se repiten campañas largas sin hipótesis verificable. Abrir una ficha/refrescar UI no equivale a captar un dato nuevo.

