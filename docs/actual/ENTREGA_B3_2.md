# B3.2 — Primera campaña retrospectiva real

19-11-2026, Europe/Madrid. **Entrega completada: un dataset real admitido para uso exploratorio, 10 ensayos registrados/completados y cero variantes promocionadas.** No es aceptación estadística ni minería a escala de todo el mercado. [Preparación conservada](B3_2_PRIMERA_CAMPANA.md) · [Ficha anterior](../archive/2026-11-19-b3-2/ACTUAL.md) · [Siguiente entrega única](../../tasks/ACTUAL.md).

## Datos y condiciones de uso

El usuario aportó una respuesta atribuida a soporte Alpaca que admite descarga, almacenamiento y backtesting personal/no comercial dentro de la suscripción y cuotas, sin redistribución. El propio mensaje declara generación con IA. Se conserva como **texto aportado por el usuario, sin autenticar cabeceras ni ticket**, junto con las condiciones públicas revisadas; no como permiso comercial ni excepción legal negociada.

No se exige otro correo para este uso ya respaldado. La respuesta no fija duración de retención ni una política específica de hashes/métricas. Se conserva esa ausencia explícita: los 30 días son un límite interno para revisar/reutilizar el paquete, no una concesión de Alpaca ni un borrado automático. Esta revisión vence el **18-12-2026 a las 15:45:30 Europe/Madrid**. El ejecutor rechaza nuevos cálculos fuera de su vigencia; los resultados anteriores siguen siendo evidencia histórica.

Captación con el transporte Alpaca existente, `feed=iex`, `adjustment=raw`, `asof=-`, cuotas compartidas y StorageGovernor. Una consulta auxiliar de calendario y un job de tres respuestas (calendario, barras, acciones corporativas), sin consultas de saldo ni órdenes. Job `b32-brkb-20261118-v1`: 252 barras del **30-12-2024 al 31-12-2025**, sin huecos/duplicados detectados y con originales revalidados frente a filas y recibos.

Identidad y moneda se incorporan solo al candidato revisado; el catálogo global no se modifica para fingir información nativa que no traía. Evidencias documentales:

- [Berkshire 10-K 2025](https://www.berkshirehathaway.com/2025ar/202510-k.pdf), portada, Item 5 y nota 22: clase B, NYSE, dividendos y continuidad accionaria. [Nota de acciones en SEC](https://www.sec.gov/Archives/edgar/data/1067983/000119312526083899/R32.htm). Las conversiones voluntarias A→B no dividen las acciones B ya mantenidas. Revisión retrospectiva junto al endpoint de acciones corporativas, que devuelve cero eventos; ese resultado vacío no se usa como prueba única de exhaustividad.
- [Términos publicados en el registro del Banco de Lituania](https://www.lb.lt/uploads/prospectuses/docs/56853_43fe0c345bc3ae9eac5c56568aae106a.pdf), 29-08-2025, sección 1.2, página 8: identifica la acción subyacente clase B en USD. Se usa esa referencia al **subyacente US0846707026**, no el token ni su ISIN CH1436219260.
- [Calendario NYSE 2025](https://www.nyse.com/publicdocs/ICE_NYSE_2025_Yearly_Trading_Calendar.pdf) y [cierre extraordinario Carter](https://ir.theice.com/press/news-details/2024/The-New-York-Stock-Exchange-Will-Close-Markets-on-January-9-to-Honor-the-Passing-of-Former-President-Jimmy-Carter-on-National-Day-of-Mourning/default.aspx). Se verifican el 09-01 sin sesión y los cierres anticipados del 03-07, 28-11 y 24-12.
- [Reglas de agregación Alpaca](https://docs.alpaca.markets/us/docs/market-data-faq): O/C diario de operaciones elegibles; no equiparar la barra IEX a una subasta NYSE o un precio ejecutable garantizado. Volumen puede incluir operaciones de horario extendido; no se usa como señal ni prueba de liquidez.

Los precios, respuesta de soporte y revisión específica permanecen en `data/` y `output/`, excluidos de Git. El código fija hashes de la revisión privada, del protocolo y de sus originales locales; cualquier cambio o ausencia retira la confianza. No se ha habilitado genéricamente cualquier instrumento/proveedor. El bloqueo de archivo IBKR permanece.

## Implementación y resultados

Admisión versionada `daily-trend-retrospective-v1`, invocada explícitamente con `--protocol retrospective`. Conserva la ruta estricta D3 y sus rechazos. El estado nuevo es `BACKTEST_READY_EXPLORATORY`: universo elegido después del periodo, histórico revisado disponible hoy, sin afirmar PIT/OOS. Se verifica integridad, calendario, OHLC, identidad, eventos, alcance personal y vigencia; no se cambian gates manualmente.

`b32_review.py` carga únicamente el paquete privado fijado en código. `quant_real.py` aporta contratos propios para mercado real; nunca convierte precios a `SYNTHETIC_TEST`. El motor `reference-daily-v2` reutiliza la aritmética Decimal existente e introduce calentamiento común: todas las variantes permanecen en efectivo durante 60 sesiones. La primera apertura evaluable es el 28-03-2025, con 192 sesiones hasta final de año.

`run_quant_campaign.py` registra y confirma los diez ensayos antes del primer cálculo. Se comparte un único snapshot quant entre los diez. Usa los parámetros y costes del [protocolo v1 congelado](B3_2_PROTOCOLO_v1.json), sin ajustarlos tras observar resultados. Sus campos de estado describen la preparación original; el estado actual está en el manifiesto y la campaña, no se reescribe ese documento histórico.

Campaña `b32-brkb-20261119-v1`: SMA20/40/60, efectivo y comprar/mantener, cada uno con costes base/adversos. **Ninguna SMA cumple el criterio predeclarado.** Cero candidatos aceptados o promovidos. Las métricas concretas se conservan en el informe privado `output/b32-20261118/RESULTADOS.md`; no se publican precios o resultados financieros en el repositorio.

Limitaciones: un único superviviente elegido a posteriori, IEX parcial, costes hipotéticos, apertura usada como proxy, sin liquidez/impacto/impuestos/FX/interés del efectivo, inventario final valorado al cierre sin venta ficticia. El intervalo usado está expuesto; B4 no puede llamarlo OOS virgen.

## Verificación y evidencias

- **111 tests aprobados** en siete archivos afectados: contratos, causalidad, calentamiento común, cuenta manual de control, idempotencia/leases, expiración, manipulación de inputs/evidencias/manifiestos y regresiones D3/B3.1. `output/b32-20261118/tests.log`. La pasada inicial de 50 está incluida y no se suma otra vez.
- CLI de admisión real ejecutado: manifiesto `7d80ac5f3ea55193859398c84394bb69e1649e7cb055369129a933aa73114715`. Archivo inmutable en `output/dataset-manifests/`.
- Diez ensayos, 30 eventos, una tentativa por ensayo. Los diez estaban registrados antes de calcular el primero. Reejecución del CLI idéntica, sin duplicar trials/eventos; reproducción determinista de los diez resultados con hashes iguales.
- Informe canónico: `output/quant-campaigns/b32-brkb-20261119-v1/53b1a415c056094a2299f8e730692a8561d4c44a9cf8b1251de451b0575ffcea.json`.
- SQLite conserva schema `0015_history_batches`, integridad `ok` y cero errores FK. `portfolios`, `ledger_events`, `ledger_entries` y `valuation_snapshots` conservan exactamente sus recuentos y hashes. MASTER separado y órdenes 403 comprobadas también por la suite. No nueva migración ni copia completa de la base.
- `output/b32-20261118/validation.json` y `validation-context.json`: hubo además un refresco concurrente A15/COINPAPRIKA, con recibo y alias fechados 18-11 a las 15:08:38 UTC. Por ello no se afirma que toda la base estuviera congelada; se distinguen captación/cuota, tablas quant y las cuatro tablas contables protegidas.

Operación local reproducible, mientras la revisión siga vigente:

```powershell
.\.venv\Scripts\python.exe scripts/admit_dataset.py market --listing 8a242788067bfd8a37e2ab0f2932c5b54fc534724557a3cf313e80bf20ccf5d3 --as-of 2026-11-19T10:22:02.109820+00:00 --protocol retrospective
.\.venv\Scripts\python.exe scripts/run_quant_campaign.py --manifest 7d80ac5f3ea55193859398c84394bb69e1649e7cb055369129a933aa73114715
```

El diagnóstico legacy de UI continúa separado: no se ha cambiado frontend ni añadido un laboratorio visual. Siguiente **B4 — validación y selección**, sin promociones artificiales ni activar PAPER. PAPER ONLY, coste obligatorio 0 EUR y P4 PARTIAL conservados.
