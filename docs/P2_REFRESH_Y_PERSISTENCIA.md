# P2: continuidad de datos y control de frescura

Checkpoint de 20-10-2026. No cierra todavía el E2E semántico P4.

## Operación

`0005_data_history` añade `data_observations` y `data_refresh`; no altera tablas financieras. Cada observación conserva ID, hash original, proveedor/feed, unidad, moneda, periodo y fechas. La respuesta más reciente deja de borrar la historia. Revisiones distintas siguen separadas; el gráfico elige la última recibida por fecha observada. Los lectores revisan permisos actuales, identidad del preset y retiradas HTTP 403/404/410. Las respuestas mock nunca se archivan como conexiones reales.

`DATA_AUTO_REFRESH_ENABLED=true` por defecto. El backend arranca un trabajador local de concurrencia 1 después de 30 segundos. Comprueba vencimientos cada minuto y consulta como mínimo cada cinco minutos o según TTL más largo. Persisten lease, fallos, último intento/éxito y próximo plazo. Los errores tienen backoff limitado; cuotas compartidas con consultas manuales y P4. No se ejecuta con el backend apagado. `GET /api/data/refresh` expone solo metadatos; no secretos ni respuestas externas.

La actualización automática exige acceso, almacenamiento, display y redistribución autorizados, configuración válida y adaptador implementado. Excluye Alpaca y Trading 212, aunque haya credenciales. No activa canales nuevos de Agent Reach. Coinbase queda bloqueado incluso en consulta manual para este sistema de IA.

## Fechas y límites

OCDE/BIS consultan una ventana móvil, Treasury el mes actual; FMI, BEA y BLS v2 usan años relativos. ESMA consulta un índice acotado reciente; no descarga ZIP. Se mantienen host, path y método allowlisted. No se aceptan parámetros ni URL suministrados por el usuario/modelo.

Reconsultar una cotización spot no rejuvenece su timestamp observado. Una serie estadística conserva su periodo histórico: la fecha de recepción no es publicación ni precio en tiempo real. Los calendarios completos de cada organismo y festivos de mercado **todavía no están implementados**; el TTL es cadencia de revalidación, no certificación de última publicación. Datos antiguos de una tabla archivada necesitan cambiar de feed, no reducir TTL.

La [documentación oficial HICP](https://ec.europa.eu/eurostat/web/hicp/information-data) confirma el archivo de ECOICOP1 y el nuevo conjunto ECOICOP2. A04 cambia a `prc_hicp_minr`, `coicop18=TOTAL`, `unit=I25`, con identidad de feed nueva. La prueba real devuelve julio–septiembre de 2026. No se empalma el índice base 2015 con el índice base 2025.

Los [términos Coinbase](https://www.coinbase.com/legal/market_data), actualizados el 07-08-2026 y comprobados el 20-10, restringen expresamente la operación/evaluación de IA sin consentimiento escrito (§3.5). También limitan redistribución y valoración. El adaptador queda conservado para contratos/tests, pero sin acceso de HQ. No se interpreta un endpoint público como licencia de IA.

## Evidencia reproducible

`scripts/qa_p2_refresh.py` realiza una pasada acotada y prueba persistencia del planificador usando las cuotas existentes, sin mocks y sin brókeres. Salida local: `output/p4-data-refresh/sources-real.json`. Distingue conexiones nuevas, caché, estados y contadores históricos. La migración real está registrada en `migration-real.json`; el backup permanece local. La corrección Eurostat está en `eurostat-ecoicop2-real.json`.

En la primera pasada: 35 modalidades examinadas; 17 conexiones verificadas, 16 HTTP nuevas y una caché; 12 respuestas P2 utilizables, 11 sin credenciales, una configuración pendiente, 2 brókeres omitidos, 2 planes/endpoints pendientes, 5 restricciones, una fuente STALE y un timeout. Son estados de esa pasada, no disponibilidad futura. El contador histórico de 18 no se usa como conteo de conexiones nuevas.

Pendiente: revalidación legal específica para IA de más fuentes, calendarios de publicación, cobertura suficiente para una tesis financiera real y aceptación semántica Bull/Bear/Chair. Sin P5/P6, servicios pagados ni órdenes.
