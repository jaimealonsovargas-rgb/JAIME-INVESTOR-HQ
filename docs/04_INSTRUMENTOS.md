# Instrumentos y matriz de capacidades

Cada combinación instrumento/proveedor declara RESEARCH, VALUATION, INTERNAL_PAPER y BROKER_PAPER de forma independiente, con licencia, moneda, país, mercado, fecha de comprobación y razón de restricción. Identificador compuesto de ticker, mercado, divisa e ISIN/CUSIP/FIGI cuando exista.

| Clase | Alcance inicial | Precaución |
|---|---|---|
| Acciones US | Investigación, valoración, paper si bróker admite | IEX/SIP, splits, dividendos |
| ETFs y REITs | Investigación y paper sujeto a API | tracking, concentración, deuda |
| Bonos soberanos individuales | Research, flujos, valoración, escenarios | cotización fiable no garantizada |
| Bonos corporativos individuales | Research, spreads, duración, riesgo de crédito | mercado OTC, precios no libres |
| ETFs de bonos | Research/paper si disponible | NO equivalen a bonos individuales |
| Efectivo/FX | Ledger y fuentes oficiales | fixing vs spot y spread |
| Monetarios/T-bills | Research y proxy cotizado si viable | vencimiento y liquidez |
| Materias primas mediante ETFs/ETCs | Research/paper según licencia | roll yield y estructura |
| Opciones/futuros | Research/escenarios inicialmente | vencimientos, greeks, margen |
| PE/VC/private credit/inmobiliario/infraestructura | Research y escenarios | valoración discrecional, iliquidez |
| CLO/estructurados/convertibles | Research | waterfall, opcionalidad, contraparte |

Prohibido afirmar ejecución demo universal. Un instrumento no negociable puede tener una ficha de investigación excelente sin inventar operaciones.
