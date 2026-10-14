# UI y flujos financieros de máxima claridad

## Posiciones
Tabla con instrumento, clase, qty, precio entrada, precio mercado, fecha y fuente, P&L EUR, P&L %, exposición, estrategia, riesgo y acceso a ficha. Ordenar, filtrar, buscar, abrir desde monitor del Trading Floor.

## Historial
Cada trade con BUY/SELL, fecha, cantidad, coste, fee, tipo de cambio, cuenta paper, fill, beneficio/pérdida absoluto y porcentual, estado, tesis, motivo de cierre y postmortem. Los cierres parciales se identifican por lote y orden.

## Investigación
Vista breve primero; paneles desplegables con tesis desarrollada, supporting arguments, contraargumentos, catalizadores, riesgos, invalidación, datos de fuente, opinión de agentes, comité, ejecución y revisión posterior. Sin muro de texto inicial.

## Navegación
HUD discreto dentro de mundo 3D **visto en tercera persona desde detrás del avatar**: mini mapa, departamentos, estado PAPER, NAV (solo cuando exista en P3), hora de datos, errores críticos. Cada departamento tiene identidad visual y propósito. El jugador se aproxima físicamente al **agente principal sentado de cada departamento** y el panel React/DOM correspondiente se abre automáticamente a una distancia cómoda; el monitor permanece como elemento físico. No se exige E/clic. Tras cerrar, no se reabre hasta salir y reentrar en el radio de proximidad; se vuelve **a la misma posición y orientación de la cámara de seguimiento**. El juego se maneja solo con flechas y cámara automática, sin giro manual con ratón. La vista aérea/planta es opcional como mapa o inspección, nunca la perspectiva principal.

## Estados
Sin datos, stale, offline, bloqueado, pendiente, error y completo con motivos claros. Nunca usar datos financieros ficticios sin etiqueta DEMO. Modo sin conexión permite explorar HQ, pero no ejecutar órdenes.
