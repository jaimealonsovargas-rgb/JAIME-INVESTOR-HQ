> Ficha histórica D1, completada el 16-11-2026. No es la tarea activa.

# Próxima entrega única — D1 · datos IBKR

11-11-2026. **B3.1 terminado y verificado**: núcleo determinista, tres ensayos sintéticos, 104 tests y migración 0014 con 40 tablas anteriores intactas. No repetirlo. [Entrega](../../actual/ENTREGA_B3_1.md) · [Ficha anterior conservada](../2026-11-11-b31/ACTUAL.md) · [Cola única](../../../tasks/ROADMAP.md).

## Resultado y punto de parada

Comprobar si la sesión IBKR Paper/read-only existente permite obtener precios e histórico diario concretos sin gasto, documentando modalidad, fechas, permisos y derechos. Terminar D1 con una evidencia reproducible de acceso utilizable o con una limitación precisa y su consecuencia para D2. D1 no habilita campañas reales ni equivale a BACKTEST_READY.

## Alcance cerrado

1. Leer la [preparación existente](../../actual/IBKR_PILOTO_PREPARACION.md) y las partes de la [evaluación](../../actual/IBKR_TWS_EVALUACION.md) sobre datos/derechos. Verificar documentación oficial actual para las peticiones elegidas. SDK, TWS, cuenta y contratos ya están preparados; no reinstalar ni repetir el bootstrap.
2. Inspeccionar configuración privada sin mostrar cuentas/secretos. Reutilizar sesión Paper, API de solo lectura, localhost y aislamiento del SDK. Si la sesión está cerrada, completar el adaptador/pruebas independientes y pedir solo el inicio de sesión que realmente falte.
3. Ampliar la allowlist de lectura únicamente para una prueba acotada: contrato ya revisado, histórico diario pequeño y cotización puntual si es pertinente y accesible. Plazo, número de peticiones y máximo de bytes explícitos. Sin streaming masivo, órdenes, suscripciones de pago, nuevos proveedores ni prueba europea obligatoria.
4. Registrar feed real/delayed/frozen según evidencia, timestamps de mercado/recepción, moneda/unidad/calendario, tipo de precios/ajuste, permisos y restricciones. No inferir derechos históricos de los permisos de contratos ni vender datos retrasados como tiempo real.
5. Guardar respuesta/evidencia privada solo si los derechos lo permiten, bajo StorageGovernor, junto con hashes y errores seguros. Pruebas offline de allowlist, límites, timeouts y calidad; luego la petición real limitada. Confirmar MASTER intacto y órdenes bloqueadas.

## Aceptación

- Acceso y coste contrastados; datos recibidos identificados o denegación/limitación concreta conservada.
- Sin ampliación silenciosa de permisos, pagos, históricos inventados ni flags promovidos para aparentar aceptación.
- Si una limitación impide usar IBKR para ese dataset a coste cero, conservar su papel de identidad y dejar documentada la alternativa explícita que debe evaluarse. No repetir indefinidamente el mismo fallo ni cambiar de fuente sin verificar que sirve y está autorizada.
- Actualizar STATUS y esta ficha con la evidencia. Parar antes de D2; no empezar lotes masivos en la misma entrega.

## Después de D1

D2: captación por lotes recuperables y universo configurable, con deduplicación, cuotas y retención diferenciada de temporales/evidencia. Evitar copiar todos los datos a cada ensayo; no borrar originales existentes automáticamente. D3: validadores/manifiesto admitido. B3.2: campaña real acotada usando el motor B3.1. Después B4 → B5 → B6.

P4 PARTIAL, PAPER ONLY, 0 EUR, MASTER separado y POST /api/orders=403 permanecen. No tocar oficina ni integrar riesgo/OMS en D1.
