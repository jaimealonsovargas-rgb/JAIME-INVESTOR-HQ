> ARCHIVO INACTIVO · copia anterior a la auditoría del 11-11-2026. Sus próximos pasos y autorizaciones no gobiernan el trabajo actual. Enlaces relativos reubicados; contenido histórico conservado.

# Suficiencia de proveedores — revisión del 27-10-2026



Actualización B2.3, 29-10-2026: implementados catálogo Alpaca, snapshot IEX, barras diarias paginadas, calendario, acciones corporativas y lectura PAPER con estados separados por endpoint. Sin claves, no hay conexión real validada ni datos Alpaca en la base habitual. IEX es parcial; SIP diferido es una posibilidad por comprobar, no fallback activo. No hay streaming aún ni vínculo SEC/instrumento certificado. [Entrega B2.3](../../../../actual/ENTREGA_B2_3.md). La insuficiencia para minería profesional sigue explícita. Las secciones fechadas B1/B2.1 debajo describen el punto de partida histórico.





Actualización B2.2, 28-10-2026: SEC multiemisor implementado y verificado para 100 emisores, 200 descargas; cuentas estándar, documentos recientes y revisiones. 353.528 cifras consultables y 12.961 registros documentales en el cotejo. 71/100 cuadros anuales con seis magnitudes básicas; 29 parciales. Cuota local SEC ahora compartida 1/s y 60/min, sustituyendo 2/min. Alpaca sigue sin claves ni conexión de universo. [Entrega/límites B2.2](../../../../actual/ENTREGA_B2_2.md).



Actualización 28-10: [B2.1](../../../../actual/ENTREGA_B2_1.md) configura el contacto SEC e incorpora el directorio real (8.023 emisores / 10.430 símbolos). El inventario de 99 instrumentos descrito debajo es el punto de partida B1; se conserva separado del catálogo. Alpaca sigue sin claves y la cobertura de cuentas, precios e históricos continúa pendiente.



**No son suficientes en su implementación actual.** Hay una base útil para construir un piloto de acciones/ETF estadounidenses y análisis macro, pero todavía no un universo profesional ni un dataset certificado para minería. No se han activado servicios de pago ni cuentas externas.



## Qué tiene realmente JAIME



Inspección de código y copia SQLite coherente que incluye WAL: 31 proveedores candidatos, 36 modalidades, 34 adaptadores. Registro: **99 instrumentos = 96 series macro, 2 cripto y 1 FX; cero acciones**. 4.297 observaciones guardadas y 23 casos. Estas cifras describen almacenamiento, no cobertura vigente ni aptitud financiera.



Alpaca y las modalidades B con clave están sin credenciales locales; SEC requiere configurar contacto identificativo, no comprar una API key. Ninguna comprobación leyó o publicó valores de secretos. `NOT_VERIFIED` en el inventario de configuración significa que se puede intentar la consulta, no que se haya probado ahora. Se conserva por separado el historial de conexiones.



Muchos adaptadores son **presets**: SEC fija un CIK; Alpaca cinco barras AAPL; Alpha Vantage cinco cierres IBM; FRED cinco observaciones DGS10; OpenFIGI un ISIN. Tiingo consulta metadatos, no descarga todavía su histórico. Un índice FIRDS no equivale a haber importado sus instrumentos. Añadir APIs sin cambiar esas rutas no resolvería la cobertura.



## Decisión por necesidad



| Necesidad | Fuente principal propuesta | Límite y decisión |

|---|---|---|

| Precios de acciones/ETF USA | Alpaca Market Data | Basic gratuito: IEX en tiempo real, 30 símbolos streaming, 200 llamadas históricas/min y datos desde 2016, con restricciones sobre los últimos 15 minutos. No etiquetar IEX como mercado consolidado. Autenticación y derechos efectivos pendientes de verificar en la cuenta. [Documentación](https://docs.alpaca.markets/us/docs/about-market-data-api) |

| Históricos de precios | Alpaca, contraste selectivo con Tiingo | Ingesta paginada, OHLCV completo, calendario, ajustes y reconciliación. El endpoint multiactivo puede agotar la primera página en un solo símbolo: recorrer `next_page_token`. No estimar cobertura por el primer resultado. [Barras](https://docs.alpaca.markets/us/reference/stockbars) |

| Empresas, filings y cuentas | SEC EDGAR | Submissions aporta identificación/tickers y archivos; companyfacts aporta XBRL; bulk nocturno para escala. No incluye necesariamente conceptos personalizados o segmentos. Registrar accession, periodo fiscal, unidad, aceptación/publicación y revisiones. El parser B1 sigue limitado a cuatro conceptos: es insuficiente para DCF. [SEC](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) |

| Macro, tipos y FX | BCE, Eurostat, BDE, INE, Treasury; FRED/ALFRED cuando esté configurado | Referencias, no precios ejecutables de bonos o divisas. FRED devuelve por defecto la información revisada actual; ALFRED permite consultar vintages. Una estrategia macro histórica exige disponibilidad de publicación. [FRED](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html) |

| Identificadores | SEC + OpenFIGI + catálogo Alpaca | Emisor, acción/clase, listing/venue y ticker temporal son entidades distintas. Resolver CIK/FIGI/ISIN sin unir por ticker solamente. Mapping no acredita divisa, acceso, liquidez o elegibilidad de ejecución. |

| Cuenta, posiciones y movimientos | Alpaca PAPER | API privada específica de cuenta PAPER; reconciliar cash, posiciones, órdenes, fills y actividades. No inferir posiciones a partir de precios ni mezclar con MASTER ficticio. [Entorno PAPER](https://docs.alpaca.markets/us/docs/paper-trading) |

| Noticias y eventos | Filings, relaciones con inversores y fuentes primarias autorizadas | GDELT actual solo devuelve pocos metadatos generales; RSS BCE no es noticias por empresa. Añadir vinculación de entidad, fechas y deduplicación; nunca instrucciones desde el contenido. Calendario de resultados/acciones corporativas no está resuelto. |

| Consenso y transcripts | No hay cobertura certificada | No prometer una base completa gratuita. Earnings Reviewer podrá comparar con periodo anterior y supuestos propios registrados; contra consenso solo si existe una fuente y licencia comprobadas. |

| Cripto | CoinPaprika personal | Free ofrece 20.000 llamadas/mes y un año de precios diarios; útil como contexto/piloto descriptivo. El preset BTC no es un universo ni OHLCV de una plaza. Se mantiene privado, separado de MASTER. [Plan](https://coinpaprika.com/api/pricing/) · [Términos](https://coinpaprika.com/terms-api) |

| Europa y renta fija individual | Cobertura insuficiente | Estadística europea, curvas del Tesoro o metadatos no sustituyen cotizaciones/históricos de cada valor. Estas familias permanecerán bloqueadas hasta disponer de datos apropiados. |



Tiingo Starter publica 500 símbolos/mes, 50 peticiones/hora, 1.000/día y 1 GB/mes: candidato para contraste acotado, no columna vertebral gratuita de miles de valores. Su lista de productos no demuestra entitlement para cada dataset. [Tiingo](https://www.tiingo.com/about/pricing).



Alpha Vantage anuncia 25 llamadas gratuitas/día: complemento selectivo, no feed masivo. Twelve Data Basic anuncia 800 créditos/día y uso interno sin display; su buscador de símbolos actual no acredita permisos de visualización de cotizaciones. No abrir las guardas actuales por disponer de una clave. [Alpha Vantage](https://www.alphavantage.co/support/) · [Twelve Data](https://twelvedata.com/pricing).



## Huecos que bloquean P5 y P6



- Historia suficientemente larga y homogénea por familia, con sesiones, zonas horarias, precios ajustados/raw identificados y calidad de volumen.

- Splits/dividendos/cambios de ticker, altas/bajas y universo conocido en cada fecha. Seleccionar hoy los supervivientes introduce sesgo.

- Publicación real o cota temporal conservadora. El `as_of` de B1 significa **conocido localmente**; no reconstruye el pasado del mercado. SEC solo proporciona fecha en companyfacts: B1 usa las 05:00 UTC del día siguiente para cubrir el cierre del día de la costa este estadounidense, no inventa hora de aceptación.

- Estado de mercado, frescura por sesión y feed, límites de spread/liquidez, costes y operaciones corporativas relevantes.

- Derechos independientes para acceso, almacenamiento, análisis IA, display y redistribución. Entitlement de endpoint, no permiso global del proveedor.

- Datos de cuenta PAPER, reconciliación y control de estados inciertos antes de poder ejecutar.



## Plan de captación B2



1. Preparar configuración local de Alpaca PAPER y contacto SEC; exponer solo el estado de preparación. Sin claves en frontend, prompts o logs. No crear cuentas ni suscripciones automáticamente.

2. Crear registro emisor–instrumento–listing y catálogo de capacidades por endpoint. Bootstrap SEC reanudable; cuotas agregadas por proveedor, backoff y caché. Cuota SEC local vigente: una consulta/segundo y hasta 60/min. Diseñar lotes, prioridades y presupuesto de disco antes de escalar; no confundir el límite técnico con cobertura efectiva.

3. Piloto de 100 emisores identificados y 20–30 símbolos de seguimiento, con barra diaria como primer horizonte. Tres emisores para normalización/modelos, incluidos ejercicios fiscales diferentes y una revisión. Captación masiva de metadatos no obliga a suscribir todos los símbolos en streaming.

4. Alcanzar 1.000 entidades identificadas y después miles; publicar distribución de cobertura, antigüedad, fallos y huecos. Un emisor identificado no cuenta como empresa analizada.

5. Congelar manifest por experimento. `RESEARCH_READY`, `BACKTEST_READY` y `EXECUTION_SIM_READY` se evalúan por universo/periodo/familia. Rechazar explícitamente datos insuficientes; no sustituirlos silenciosamente por otra plaza o feed.



**Criterio de suficiencia:** un ciclo completo reproducible sobre el piloto, con trazabilidad y tasas de cobertura medidas. Con coste obligatorio de servicios 0 EUR no se promete tiempo real consolidado global, consenso completo ni históricos institucionales de todos los activos. Esas limitaciones definirán el universo y las estrategias admisibles.

