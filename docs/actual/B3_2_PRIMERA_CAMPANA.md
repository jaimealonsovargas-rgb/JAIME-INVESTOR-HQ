# B3.2 — Preparación de la primera campaña real

**Documento histórico de preparación del 18-11. B3.2 se completó el 19-11:** [entrega, respuesta de soporte, admisión y resultados](ENTREGA_B3_2.md). Los pendientes descritos abajo reflejan aquel momento; la siguiente entrega actual es B4.

18-11-2026, Europe/Madrid. **Preparación documental terminada; dataset sin admitir y campaña sin ejecutar.** Esta ficha concreta [ACTUAL](../../tasks/ACTUAL.md), sin abrir otra fase ni cambiar el orden de [ROADMAP](../../tasks/ROADMAP.md).

## Experimento fijado antes de calcular resultados

[Protocolo v1](B3_2_PROTOCOLO_v1.json): Berkshire Hathaway clase B, candidata Alpaca `BRK.B`, feed IEX, barras diarias sin ajustar, últimas 252 sesiones oficiales que terminan el 31-12-2025. Las primeras 60 son calentamiento común y las 192 siguientes se evalúan. El inicio exacto se obtiene del calendario revisado, incluyendo medias sesiones y cierres extraordinarios; no se supone que un año civil contenga 252 sesiones.

Se escoge un caso sencillo para comprobar la tubería real, no por sus rendimientos. Esto no limita el universo futuro del producto ni constituye una recomendación sobre Berkshire. La ausencia documentada de dividendos en efectivo ayuda a acotar el caso, pero faltan la revisión completa de acciones corporativas y la identidad durante todo el intervalo.

Tres variantes SMA (20, 40 y 60 sesiones) y dos controles (efectivo y comprar/mantener), cada uno con costes base y adversos: **10 ensayos previstos**, incluidos los controles. Capital independiente de 10.000 USD simulados, acciones enteras, sin apalancamiento ni cortos. Ningún saldo procede de MASTER ni de una cuenta del broker.

Todos permanecen en efectivo durante el calentamiento. La primera operación posible es en la sesión 61; se usan únicamente cierres de sesiones anteriores. En igualdad con la media, la estrategia permanece o pasa a efectivo. El control comprar/mantener comienza también en la sesión 61. No basta con recortar después una curva que ya hubiera operado durante el calentamiento.

Costes por cada compra y venta: base, comisión 1 pb y deslizamiento 5 pb; adversos, 5 y 20 pb, respectivamente. Son supuestos de sensibilidad, no tarifas observadas de Alpaca. El deslizamiento incluye spread. Valoración final al último cierre, sin simular liquidación; no se atribuye coste de salida a una venta inexistente. Se conserva efectivo, posición residual y costes por separado.

Se mostrarán retorno neto, drawdown, costes, operaciones y comparación con ambos controles en idéntico intervalo. La hipótesis exploratoria solo queda apoyada en este caso si supera el retorno de ambos controles con los dos escenarios de coste y no aumenta el drawdown frente a comprar/mantener. Cualquier resultado sigue siendo exploratorio: no hay promoción automática, significación estadística, OOS ni activación PAPER. Todos los resultados, errores y descartes permanecen registrados; no se cambian activo, fechas o parámetros después de verlos.

## Corrección del alcance de D3

D3 exige hoy universo elegido antes del histórico y evidencia de publicación de cada barra. Estas condiciones sirven para su protocolo estricto, pero no describen un estudio retrospectivo elegido hoy sobre datos revisados hoy. El loader Alpaca ya reconoce que su universo procede del catálogo actual.

Para esta campaña se especifica **RETROSPECTIVE_EXPLORATORY**: selección posterior al periodo, sesgo de supervivencia reconocido y versiones actuales del histórico. No se inventarán fechas de publicación ni un universo point-in-time. El orden cierre previo → apertura siguiente evita usar el futuro dentro de la reproducción, pero no elimina revisiones históricas desconocidas ni demuestra disponibilidad contemporánea.

El protocolo está definido, **todavía no implementado ni habilitado en el CLI D3**. El registro confiable continúa vacío. Tras resolver el uso y capturar el dataset, se necesitará una adaptación mínima y versionada de admisión y del contrato quant real, conservando la ruta estricta y sus rechazos. B3.1 solo admite fixtures: no se introducirán barras reales bajo `SYNTHETIC_TEST`. También habrá que verificar el calentamiento común; el motor actual compra/mantiene desde la primera barra. Estos son requisitos concretos de B3.2, no un mandato de construir infraestructura ahora.

## Evidencia obtenida y pendientes

| Aspecto | Evidencia / límite |
|---|---|
| Candidato existente | Catálogo local: Alpaca `BRK.B`, NYSE, UUID `71bb19d0-6c5f-4881-9552-33224badd810`; listing `8a242788067bfd8a37e2ab0f2932c5b54fc534724557a3cf313e80bf20ccf5d3`. |
| Emisor y clase | Catálogo SEC: CIK `0001067983`, símbolo `BRK-B`; listado separado. El 10-K 2025 confirma clase B y NYSE. No se han fusionado registros ni acreditado toda la continuidad temporal. |
| Moneda | El catálogo local tiene `currency=null`. USD es la moneda objetivo; falta acreditar moneda nativa. Pedir USD a la API no la prueba. |
| Acciones corporativas | El 10-K informa de ausencia de dividendos en efectivo desde 1967. No basta para certificar ausencia de todos los eventos durante el intervalo; revisar splits y otros cambios. Un resultado vacío del endpoint por `process_date` no acredita exhaustividad. |
| Calendario | Faltan sesiones oficiales fijadas, medias sesiones, cierre extraordinario del 09-01-2025 y timestamps con zona. |
| Semántica de precios | IEX representa una plaza, no todo el mercado. Sus OHLC no se equiparan a subastas NYSE ni a precios garantizados de ejecución. Revisar cobertura horaria y usar la apertura solo como proxy de simulación. |
| Integridad | No se ha descargado el histórico candidato. Faltan paginación completa, hashes/recibos, 252 sesiones sin huecos/duplicados y comprobaciones OHLC. No rellenar ni sustituir sesiones silenciosamente. |
| Derechos | `RIGHTS_SCOPE_UNRESOLVED`: alcance contractual de copia persistente y reutilización local pendiente. No equivale a una prohibición universal del backtesting. |

## Revisión de condiciones de Alpaca

Fuentes oficiales consultadas el 18-11-2026:

- [Historical API](https://docs.alpaca.markets/us/docs/historical-api) presenta el backtesting como uno de sus usos.
- [Terms and Conditions](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf), apartados Personal and Non-Commercial Usage y Content: admite uso personal/no comercial y limita publicación, distribución y explotación comercial.
- [Customer Agreement](https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf), versión pública V26.2026.07, §30, página 16: incluye «I agree not to reproduce, distribute, sell or commercially exploit the market data in any manner without written consent from Alpaca».
- [Paper Trading](https://docs.alpaca.markets/us/docs/paper-trading) permite algoritmos Paper y describe acceso IEX para Paper Only. Esa descripción no resuelve por sí sola el contrato de una persona que también tiene cuenta real.
- [Berkshire 10-K 2025](https://www.berkshirehathaway.com/2025ar/202510-k.pdf), portada e Item 5 (K-33): clase/listado y dividendos; documento posterior al periodo, usado como evidencia retrospectiva, no como señal contemporánea.

El usuario ha confirmado que también tiene cuenta real. No se ha inspeccionado el contrato aceptado en su cuenta ni se afirma que el PDF público sea idéntico. El conflicto aparente se resuelve con una condición aplicable o una aclaración escrita de Alpaca sobre esta copia privada. No se deducen derechos del éxito de una petición HTTP ni se asigna una retención ficticia.

Se ha preparado [la consulta concreta](B3_2_CONSULTA_ALPACA.md), sin enviarla. Propone un máximo de 30 días de conservación de precios y copias privadas: **es un límite solicitado para el experimento, no un permiso del proveedor ni una limpieza ya implementada**. Debe aclarar también el tratamiento de métricas y artefactos al vencer el plazo. No se inicia descarga mientras este requisito siga abierto.

## Punto exacto de continuación

1. Resolver la consulta o aportar condiciones aplicables al uso personal descrito. Guardar la evidencia real y su alcance; no inventar una autorización ni reabrir una auditoría general.
2. Si permite el uso sin coste, completar identidad/calendario/eventos/semántica; captura acotada mediante la integración Alpaca existente y StorageGovernor. Acordar cómo cumplir la retención antes de archivar, sin borrar evidencias ajenas ni introducir limpieza global.
3. Adaptar el alcance retrospectivo de forma tipada, probar los límites relevantes y congelar el manifiesto del dataset. No cambiar el estado de un gate a mano ni admitir por mera ausencia de errores HTTP.
4. Con dataset admitido, conectar el contrato real al núcleo determinista, registrar los 10 ensayos antes del cálculo y entregar resultados con sus límites. Parar al terminar esa campaña; B4 continúa como siguiente entrega.

Si la respuesta impone pago o no cubre el uso, mantener el bloqueo y registrar la causa concreta. IBKR conserva su revisión pendiente y su bloqueo de archivo; no se sustituye la fuente silenciosamente. No se han ejecutado nuevos tests de runtime en esta preparación documental, ni cambiado código, base, órdenes o UI.
