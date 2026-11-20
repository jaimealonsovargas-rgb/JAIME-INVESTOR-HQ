> Ficha histórica inactiva, preservada al implementar D3 el 17-11-2026. La cola vigente está en [ACTUAL](../../../tasks/ACTUAL.md) y [ROADMAP](../../../tasks/ROADMAP.md).

# Próxima entrega única — D3 · admisión de datasets

17-11-2026, Europe/Madrid. **D2 entregado con fixtures:** cola durable, ventanas y transporte IBKR aislado; archivo real bloqueado por derechos no acreditados. 92 pruebas distintas y fixture 1.000 unidades, sin red real. [Entrega D2](../../actual/ENTREGA_D2_LOTES.md) · [Ficha anterior](../2026-11-17-d2/ACTUAL.md) · [Cola única](../../../tasks/ROADMAP.md).

## Resultado y punto de parada

Propuesta de siguiente entrega, todavía sin implementación D3: validadores verificables y manifiesto congelado para admitir o rechazar un dataset concreto de tendencia diaria con causas reales. Cero datasets admitidos es válido si faltan evidencias. Parar antes de B3.2; no incorporar nuevos proveedores para aparentar cobertura.

## Alcance cerrado propuesto

1. Identidad histórica: clase, símbolo, plaza, moneda, aliases y fechas efectivas con evidencia. El contrato fijado en D2 no prueba continuidad pasada ni universo PIT.
2. Calendario/gaps: sesiones esperadas/recibidas, huecos y causas por instrumento/periodo. Profundidad según protocolo; 252 sesiones no equivalen a aceptación estadística.
3. Precios/acciones corporativas: OHLCV, splits/dividendos, ajustes, moneda y semántica versionada. Ausencia no equivale a validación positiva; TRADES no cubre dividendos.
4. Cronología/universo: available-at, selección/bajas, sesgo de supervivencia y limitaciones reales del histórico conocido hoy.
5. Derechos de cuenta/feed/uso/archivo/retención y coste: mantener denegación sin evidencia. Los documentos públicos no acreditan el circuito local/Alpaca PAPER; no pagos, bypass ni fallback silencioso.
6. Reutilizar snapshots/cobertura D2; manifiesto inmutable con hashes, versiones, evidencia y razones por gate. Sustituir bloqueos fijos solo cuando haya validación real.

## Aceptación y límites

- Resultado por instrumento/universo/periodo/familia con causas; RESEARCH_READY, BACKTEST_READY y EXECUTION_SIM_READY solo cuando proceda. No promocionar por número de barras o éxito de fixtures.
- Pruebas positivas/negativas con fixtures; aceptación externa separada y solo con derechos/dataset disponibles. Preservar evidencia y StorageGovernor.
- Sin minería real, órdenes, obra visual, auditoría total ni migraciones por anticipado. PAPER ONLY, 0 EUR, órdenes 403, MASTER/modelos/ensayos intactos y P4 PARTIAL.
- Cerrar con evidencia y estado corto. Después B3.2 sobre datos admitidos; B4, B5 y B6 conservan sus gates.


