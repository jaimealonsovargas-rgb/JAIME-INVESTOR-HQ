# Adaptación de Day Trader a JAIME

Revisión del 06-11-2026. Colección MIT de Jakeschincariol, commit `3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd`. Los 22 archivos de las nueve skills locales coinciden con los blobs originales tras normalizar finales de línea. La copia entró con las 39 skills el 04-11. Se revisaron instrucciones y código como referencia. [Versión examinada](https://github.com/Jakeschincariol/day-trader-skill/tree/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd).

## Revisión del 20-11-2026 · riesgo y minería

Se contrastó la cabeza de `main` con la revisión anterior. Ambas apuntan a `3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd`. El repositorio contiene once módulos y JAIME ya conserva nueve como referencias bajo la licencia MIT. La nueva oportunidad está en aplicar sus métodos a los bloques que JAIME ha desarrollado desde el 6 de noviembre. [Repositorio revisado](https://github.com/Jakeschincariol/day-trader-skill/tree/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd).

| Prioridad | Qué aprovecha JAIME | Condición de aceptación |
|---|---|---|
| Incorporado en B5 | El tamaño admisible de una compra depende de la distancia hasta una salida adversa. La política PAPER v2 exige que el comité identifique la invalidación, el precio de salida bajo estrés y la evidencia. Incluye costes de entrada y salida, tenencias y compras pendientes o ya aceptadas en el lote. Una propuesta excesiva recibe un veto y queda registrada la cantidad máxima según **este control**. | Pruebas de salto de precio, salida a cero, escenario ausente, tenencias previas y fraccionamiento entre dos candidatas. El umbral inicial del 0,5 % del patrimonio por instrumento es un parámetro de ingeniería. [Cálculo de tamaño original](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-budget/size.py) · [Controles originales](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-risk/check.py) · [Entrega JAIME](ENTREGA_B5.md) |
| Próxima ampliación de B3/B4 | Añadir dos familias diarias que el motor pueda ejecutar, ruptura del máximo de cierres previos y rebote tras sobreventa. El cribado inicial puede recorrer lotes y contar activos elegibles, descartados y sin datos. La señal solo usa barras cerradas y entra en la siguiente oportunidad negociable. | Prerregistrar ventanas, fórmula, tamaño de búsqueda, controles y costes. Comparar a igual presupuesto y validar sobre un periodo independiente. La ruptura intradía del rango de apertura requiere un dataset intradía admisible. [Scanner](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-scanner/scan.py) · [Entrada](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-entry/entry.py) |
| Posterior · B4 | Comparar el comportamiento en sesiones históricas con simulaciones por bloques de barras consecutivas. Guardar semilla, número de sesiones independientes y sensibilidad a huecos, liquidez y costes. | Mantener separados los episodios reales y los caminos simulados. El simulador original toma barras por franja horaria y contabiliza la salida al stop aun en un salto de precio. La prueba de selección de JAIME continúa usando su reserva independiente. [Time Machine](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-timemachine/timemachine.py) |

En una prueba ficticia con 10.000 USD de patrimonio, el presupuesto por instrumento fue de 50 USD. Con entrada a 10 USD, salida estresada a 8 USD y el margen de costes en ambos lados, 24 acciones pasaron el control. Proponer 25 elevó la pérdida estimada a 50,90 USD y produjo un veto. Otras pruebas repitieron el cálculo con acciones ya comprometidas.

El motor Python, los proveedores P2, la agenda n8n y el registro de ensayos cubren la infraestructura. Los nueve módulos se conservan como referencias estáticas. El siguiente hito de la cola sigue siendo el simulador local de B6. [Hoja de ruta](../../tasks/ROADMAP.md).

## Incorporado el 06-11-2026

El criterio de `trader-analyst.stale_note` se adapta al modelo anual de B2.4. CompanyService contrasta el ejercicio utilizado con el último informe anual del catálogo SEC conocido localmente hasta la fecha de corte. Un informe posterior o una enmienda pendiente bloquea la cobertura aunque las operaciones aritméticas cuadren. La comprobación se muestra junto a las conciliaciones y se conserva en cada versión. Los originales, recibos y cuotas son los de P2. La frescura del catálogo limita esta comprobación. [Criterio original](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-analyst/facts.py).

## Encaje en el orden de construcción

| Componente | Adaptación propuesta | Momento y condición |
|---|---|---|
| Analyst | Cobertura de informes incorporada. Después, comparativas interanuales y eventos 8-K con evidencia | B2.4 y P4. Periodos, conceptos y fechas de conocimiento compatibles |
| Scanner | Dos etapas de filtrado y confirmación, contadores de cobertura y causas de descarte | B3. Primera familia de tendencia diaria sobre un dataset admisible |
| News | Eventos nuevos deduplicados por fuente, emisor y documento. Vincularlos con la tesis y sus evidencias | P4 y agenda B2.5. Fuentes P2 autorizadas y contenido tratado como datos |
| Entry y Exit | Hipótesis con regla de entrada, invalidación, salida y vencimiento fijadas antes del ensayo | B3. Señal calculada al cierre y ejecución posterior con costes |
| Time Machine | Simulación reproducible, semilla registrada y comparación con episodios históricos | B4. Añadir dependencia temporal, regímenes, costes y evaluación fuera de muestra |
| Budget y Risk | Tamaño limitado por pérdida, exposición, liquidez y efectivo. Decisión vinculada al contenido concreto de la propuesta | B5. Estado real y vigente del ledger de simulación, reservas de riesgo y transacciones |
| Alerts | Eventos que se registran una vez por condición, vinculados a la agenda central | B2.5/B5. Calendario por mercado y recuperación tras interrupciones |
| Broker | Referencia del ciclo de una orden para el futuro OMS de JAIME | B6, con conciliación de ejecución PAPER y sus controles propios |

Los nueve módulos vendoreados tienen carácter de referencia. El ejecutor de brokers y el seguimiento de operaciones de congresistas quedan excluidos del inventario del proyecto. La adaptación respeta PAPER ONLY, coste 0 EUR y el bloqueo actual de órdenes.

## Límites observados en el código

- El scanner utiliza el directorio actual de símbolos y datos de Yahoo. Harán falta identidad por mercado, bajas históricas, ajustes y derechos de los datos para los ensayos. Las barras completas y el registro de símbolos fallidos son prácticas aprovechables. [Scanner](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-scanner/scan.py).
- Time Machine extrae barras de sesiones anteriores por franja horaria. Sus 10.000 trayectorias reutilizan una muestra de sesiones limitada. La rutina calcula el resultado al precio del stop y no incorpora comisiones, spread ni deslizamiento. En una barra que toca stop y objetivo elige el stop. Para JAIME, el coste, los gaps y la incertidumbre de ejecución deben entrar en el cálculo. El número de trayectorias no acredita rentabilidad futura. [Simulador](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-timemachine/timemachine.py).
- Los calendarios de alertas y riesgo están codificados para NYSE 2026/2027. Se requiere calendario por instrumento y cierre anticipado verificado. La política de dejar pasar reducciones de exposición merece revisión ante precios caducados, posiciones sin reconciliar y órdenes pendientes. [Riesgo](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-risk/check.py), [alertas](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-alerts/alerts.py).
- El analista selecciona versiones por publicación y deriva el cuarto trimestre. Para JAIME, cualquier derivación necesita fuentes compatibles y fecha de corte. El EPS derivado exige especial cuidado por las acciones medias. Se conserva la contabilidad Decimal y la revisión racional de B2.4. [Analista](https://github.com/Jakeschincariol/day-trader-skill/blob/3d0f4ef6986f4984b7c6bd46f7ff4f87744c3abd/trader-analyst/facts.py).

## Criterios para incorporar las siguientes piezas

Cada hipótesis deberá registrar instrumento, mercado, divisa, dataset y huellas, fecha de conocimiento, horizonte, fórmula de señal, regla de invalidación, parámetros y motivo del ensayo. Todos los intentos y descartes se guardarán. La selección exigirá resultados netos de costes, estabilidad, benchmark, control de múltiples pruebas y evaluación fuera de muestra. Estos requisitos pertenecen a B3/B4 de la hoja de ruta.

La entrega del 6 de noviembre incorporó la comprobación anual de cobertura. Los avances posteriores se fechan por separado arriba. El rendimiento se tendrá que demostrar con los datasets y controles de JAIME.
