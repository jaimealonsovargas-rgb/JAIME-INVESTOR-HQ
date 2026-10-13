# Motor profesional de renta fija

## Datos contractuales
Emisor, identificador, moneda, nominal, tipo cupón fijo/flotante/cero, frecuencia, fecha emisión/vencimiento, calendario de pagos, convención ACT/ACT, ACT/360 o 30/360 según bono, seniority, callable/putable, amortización, rating, garantía y fuentes.

## Valoración
Precio sucio = valor presente de flujos futuros según curva y convención. Precio limpio = precio sucio − interés corrido. YTM como solución de flujos; diferenciar current yield, yield to worst, spread sobre curva y OAS cuando proceda. Duración Macaulay/modificada, DV01, convexidad y sensibilidad ±100 pb de tipos/spread. Bonos con opciones requieren tratamiento explícito, no fórmula estándar sin advertencia.

## Ledger
Compra entre cupones, accrued, cobro cupón, vencimiento, amortización, default/recovery, FX de cada flujo y mark-to-market etiquetado como precio de mercado o valoración teórica. Los precios OTC no se inventan.

## Tests mínimos
Cero cupón, cupón semestral, interés corrido, ACT/ACT vs 30/360, YTM conocido, precio al variar yield, spread, bono callable marcado, cupón parcial y flujos en divisa extranjera. Comparar con fixtures verificables y tolerancias documentadas.
