# UI y flujos financieros de máxima claridad

## Posiciones
Tabla con instrumento, clase, qty, precio entrada, precio mercado, fecha y fuente, P&L EUR, P&L %, exposición, estrategia, riesgo y acceso a ficha. Ordenar, filtrar, buscar, abrir desde monitor del Trading Floor.

## Historial
Cada trade con BUY/SELL, fecha, cantidad, coste, fee, tipo de cambio, cuenta paper, fill, beneficio/pérdida absoluto y porcentual, estado, tesis, motivo de cierre y postmortem. Los cierres parciales se identifican por lote y orden. En P3 todavía no hay órdenes/fills de usuario: el historial activo es el ledger; blotter completo llega en P6.

## Investigación
Vista breve primero; paneles desplegables con tesis desarrollada, supporting arguments, contraargumentos, catalizadores, riesgos, invalidación, datos de fuente, opinión de agentes, comité, ejecución y revisión posterior. Sin muro de texto inicial.

## Navegación
HUD discreto dentro de mundo 3D **isométrico elevado estilo Los Sims**: mini mapa, departamentos, estado PAPER, NAV (desde P3), hora de datos, errores críticos. Cada departamento tiene identidad visual y propósito. El jugador se aproxima físicamente al **agente principal sentado de cada departamento** y el panel React/DOM correspondiente se abre automáticamente a una distancia cómoda; el monitor permanece como elemento físico. No se exige E/clic. Tras cerrar, no se reabre hasta salir y reentrar en el radio de proximidad; se vuelve **a la misma posición del avatar y cámara isométrica de orientación fija**. El juego se maneja solo con flechas **screen-relative** (↑ arriba, ↓ abajo, ← izquierda, → derecha), el avatar gira automáticamente y la cámara isométrica elevada sigue sin rotar. Vista general de planta opcional.

## HUD lateral profesional

Los paneles negros laterales deben convertirse gradualmente en un cockpit de monitorización, siguiendo patrones habituales de terminales de inversión profesionales (watchlist, portfolio, orders/trades, news/alerts), pero respetando las fases del proyecto.

### Lado izquierdo — Watchlist / Market Pulse

Desde P3 puede mostrar datos P2:
- watchlist compacta con símbolo/nombre, último, cambio diario %, frescura y fuente;
- 6–10 filas visibles como máximo;
- market pulse con 2–4 referencias relevantes;
- alerts informativas/read-only cuando P2 las soporte;
- click en símbolo solo cambia contexto/abre detalle, nunca envía una orden.

### Lado derecho — Portfolio / Activity / Map

Desde P3:
- **Cartera:** NAV, caja, invertido %, P&L y estado de valoración;
- **Posiciones:** top 5 por peso cuando existan; inicialmente “Sin posiciones · 10.000 EUR en caja”;
- **Actividad:** eventos de ledger; órdenes/fills quedan `P6 — NO DISPONIBLE`;
- **Mapa:** conservar el minimapa actual como tab o botón, no eliminarlo.

En P6, Activity podrá evolucionar a blotter de órdenes/trades con estados y fills, sin cambiar la estructura visual base.

## Centro de control — videowall gigante

Pantalla panorámica superior visible desde la oficina estilo Sims y expandible a DOM fullscreen. **P3 activa de verdad Cartera/NAV/Posiciones** usando la cartera MASTER; mercados/noticias P2 continúan si están verificados; operaciones/fills siguen P6, riesgo P5 y jobs P4. Sin cifras inventadas, con fuente, timestamp, derechos y estado por sección. Botón DOM propio, sin NPC obligatorio. Ver [plan P3](PLAN_P3_LEDGER_CARTERA_Y_HUD.md) y [plan maestro](PLAN_MAESTRO_SIMS_VIDEOWALL_AGENTES_INTEGRACIONES.md).

La nitidez del videowall debe tratarse como requisito funcional: usar texto DOM/SDF o textura suficientemente densa y filtros adecuados; no introducir re-render por frame ni degradar significativamente FPS solo por subir resolución.

## Estados
Sin datos, stale, offline, bloqueado, pendiente, error y completo con motivos claros. Nunca usar datos financieros ficticios sin etiqueta DEMO. Modo sin conexión permite explorar HQ, pero no ejecutar órdenes.
