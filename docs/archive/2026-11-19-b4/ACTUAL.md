# Próxima entrega única — B4 · validación y selección

19-11-2026, Europe/Madrid. [B3.2 completado](../../actual/ENTREGA_B3_2.md): un dataset BRK.B/IEX admitido para backtest retrospectivo exploratorio, diez ensayos y cero variantes promocionadas. No repetir captación, admisión o campaña por defecto. [Ficha B3.2 preservada](../2026-11-19-b3-2/ACTUAL.md) · [Cola única](../../../tasks/ROADMAP.md).

## Mandato y entrada

Construir la validación y selección deterministas sobre el registro quant existente, manteniendo la distinción entre resultado exploratorio, evidencia estadística y posibilidad de ejecución. Entrada real: campaña `b32-brkb-20261119-v1`, diez ensayos, dos escenarios de costes, protocolo y manifiesto congelados. Las tres SMA fallan el criterio predeclarado: no forzar un candidato ganador ni modificar la campaña terminada.

El intervalo 30-12-2024 a 31-12-2025 ya ha sido usado, incluidos calentamiento y evaluación; se registra como exposición exploratoria. No se puede etiquetar posteriormente una parte de ese intervalo como OOS nunca observado. Ningún dataset actual acredita reconstrucción PIT de mercado.

## Trabajo acotado

1. Definir contrato versionado de validación: hipótesis, universo, particiones temporales, costes, benchmarks, número total de ensayos, exposición previa y razones de rechazo. Consumir todos los trials, incluidos fallos y controles; no seleccionar solo resultados favorables.
2. Implementar checks de particiones sin solapamiento/look-ahead, muestras mínimas y exposición heredada. Aplicar métricas estadísticas únicamente cuando sus supuestos y datos sean suficientes; de lo contrario mostrar INSUFFICIENT_EVIDENCE. Fixtures para comprobar casos límite, sin simular evidencia financiera positiva.
3. Emitir el expediente de validación de la campaña existente: cero candidatos promocionables. Si se propone otra campaña o una muestra reservada, fijar su protocolo antes de observar precios/resultados y admitir sus datos por separado. No descargar más histórico por inercia ni reutilizar el periodo expuesto como OOS virgen.
4. Dejar el resultado consumible por el siguiente B5, con decisión/rechazos, hashes y trazabilidad. Un resultado NO_CANDIDATES mantiene el sistema en observación sin generar órdenes.

## Aceptación y punto de parada

- Contratos y checks de validación reproducibles, sin presentar retrospectivo como PIT/OOS.
- Informe trazable del conjunto completo de ensayos y sus rechazos; cero aceptados es válido.
- Pruebas relevantes e invariantes conservados: MASTER intacto, schema sin migración innecesaria, PAPER ONLY, 0 EUR, órdenes 403 y P4 PARTIAL.
- Parar al cerrar esta entrega B4; B5 riesgo/autonomía y B6 OMS son posteriores. Sin nuevos proveedores, cambios visuales o ejecución externa en este paso.

## Condiciones conservadas

Uso personal local Alpaca IEX del paquete revisado; respuesta de soporte aportada por el usuario, declarada con IA y sin autenticar cabeceras. Revisión interna vence el 18-12-2026 a las 15:45:30 Europe/Madrid; no es plazo de retención impuesto por Alpaca. B4 no amplía automáticamente la revisión a otros activos/periodos. Originales/artefactos privados en data/output, sin redistribución. IBKR sigue integrado para datos, con su archivo real todavía denegado; no se reemplaza como parte de esta entrega.
