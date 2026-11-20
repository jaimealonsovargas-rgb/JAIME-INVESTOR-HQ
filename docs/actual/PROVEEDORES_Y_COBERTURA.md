# Proveedores y cobertura vigente

Revisión de implementación y evidencia local, 11-11-2026. No es una nueva verificación web de licencias/precios. Los permisos concretos deben comprobarse para cada dataset antes de habilitarlo. Orden único en [ROADMAP](../../tasks/ROADMAP.md).

| Fuente | Papel vigente | Comprobado | Próxima necesidad / límite |
|---|---|---|---|
| **IBKR/TWS** | Contratos y datos de mercado dentro de B2 | D1 16-11: cinco sesiones AAPL y snapshot diferido tipo 3; precios solo en memoria | D2 lotes/transporte offline entregados; archivo real denegado (`UNVERIFIED_ACCOUNT_AND_USE_SCOPE`). Retención/cuenta/uso local-Alpaca PAPER no acreditados; D3 pendiente |
| **SEC** | Cuentas/documentos y catálogo de emisores | 8.023 emisores/10.430 registros; cuentas/documentos de 100; modelos del piloto | Escalar por lotes cuando corresponda. No aporta por sí sola precios ni divisa del listing |
| **Alpaca Market Data** | Lectura estadounidense existente | Catálogo de 14.407, endpoints de lectura comprobados previamente, una serie de 21 barras Apple | Feed IEX parcial; histórico actual no admitido para backtest. Evaluar por semántica/permiso; no fallback de pago |
| **Alpaca PAPER** | Destino de ejecución B6 | Lectura externa separada de MASTER; órdenes JAIME bloqueadas | OMS/riesgo/reconciliación pendientes; habilitar solo al superar sus controles |
| ZSE / A22 | Piloto oficial europeo HT | Listing propio y cierres locales, refresco P2 existente | Conservar. Ampliar Europa no bloquea B3.1 ni obliga a otro piloto antes de la primera campaña |
| Trading 212 DEMO | Lectura conservada, fuera del siguiente entregable | Conexión/catálogo acotado de 500 registros comprobados previamente | No ampliar ni rediseñar el ejecutor mientras la ruta acordada sea Alpaca PAPER |
| Yahoo / Stooq | Candidatos Nivel 2, no habilitados | Catálogo con UNOFFICIAL_SOURCE/ámbito interno | Revisión de términos/dataset solo si hay una carencia concreta; accesibilidad no concede derechos |
| Otras fuentes / skills | Apoyo sujeto a permisos y contratos P2 | Inventario y auditorías previas conservados | Ningún número de skill se convierte automáticamente en dato del producto |

**No contamos una conexión como cobertura del mercado.** Por activo: identidad, campos disponibles, periodo, tipo de feed, observación/recepción, permisos y aptitud por análisis. El catálogo es amplio; los datos aceptados para estrategias siguen ausentes.

## Decisiones prácticas

- IBKR permanece en la ruta de datos y su prueba D1 tiene una salida concreta: acceso confirmado con límites o denegación documentada. Un contrato no prueba derechos de precios/históricos.
- SEC conserva contabilidad. Alpaca conserva lectura existente y el destino PAPER de B6. No crear un segundo proyecto de broker por esta auditoría.
- El objetivo de miles de activos exige cola/paginación/reanudación, cuotas, disco y cobertura medidos. Tres acciones son regresión de ingeniería, no universo de inversión definitivo.
- Coste obligatorio 0 EUR. Si un dataset no está disponible gratuitamente, no se promete cobertura ni se contrata; se explicita la limitación y se revisa una alternativa adecuada y autorizada.
- Persistir fuentes/versiones/tiempos; no mezclar dos series de distintos feeds, ajustes o moneda como si fueran iguales. Los permisos de redistribución y el uso para minería no se infieren del acceso a la API.

Evidencia: [datos IBKR D1](ENTREGA_D1_IBKR_DATOS.md), [contratos IBKR](ENTREGA_B2_3_CONTRATOS_IBKR.md), [Alpaca](ENTREGA_B2_3.md), [contabilidad](ENTREGA_B2_4.md), [n8n](ENTREGA_B2_5.md). [Evaluación inicial de proveedores preservada](../archive/2026-11-11-continuidad/docs/actual/PROVEEDORES_Y_COBERTURA.md).
