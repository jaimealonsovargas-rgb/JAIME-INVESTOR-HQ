# B2.3 — contratos observados y divisa IBKR

11-11-2026, Europe/Madrid. Entrega incremental sobre la identidad SEC/Alpaca existente. **Divisa USD documentada para los tres contratos observados**, sin inferir continuidad histórica. B2 sigue abierto, P4 PARTIAL, coste obligatorio 0 EUR y órdenes deshabilitadas.

## Resultado y revisión

Se revisaron los nombres de emisor, la acción ordinaria/contexto del 10-K SEC, el catálogo Alpaca fijado y las respuestas de contratos del piloto de las 09:38 Madrid. AAPL/Apple Inc., MSFT/Microsoft Corporation y WMT/Walmart Inc. resultan coherentes. La revisión se fijó a las 09:55 Madrid con huellas de los tres vínculos y sus instrumentos lógicos. No hay unión genérica por ticker, ni se atribuye un CIK al conId sin ese vínculo revisado.

| Acción | conId revisado | Divisa del contrato | Bolsa principal comunicada | Ruta |
|---|---:|---|---|---|
| AAPL | 265598 | USD | NASDAQ | SMART |
| MSFT | 272093 | USD | NASDAQ | SMART |
| WMT | 13824 | USD | NASDAQ | SMART |

IBKR distingue `exchange` (ruta), `primaryExchange` (bolsa principal) y `currency` (moneda del instrumento). No se transforma SMART en MIC ni se interpreta NMS como una acreditación independiente de la clase jurídica. [Definición oficial de Contract](https://www.interactivebrokers.com/docs/tws-api/doc/contracts/object), consultada el 11-11-2026.

La consulta estaba restringida a STK/SMART/USD. La respuesta documenta **ese contrato seleccionado**; no descubre todas las cotizaciones de la empresa, ni demuestra permanencia histórica de la divisa o del mercado. El enlace a documentación describe campos; la evidencia concreta es el informe privado preservado, no esa página web.

## Integración y conservación

- `pilot_identity.json` se conserva. `pilot_ibkr_review.json` añade metadatos de revisión, fecha, SHA del piloto, instrumentos lógicos, conIds y huellas de contratos. No contiene cuentas, claves ni la respuesta privada completa.
- `ibkr_contract_evidence.py` verifica el informe comprimido y acotado a 64 KiB, sus hashes, la revisión, tres candidatos únicos/completos, campos y vínculo de clase. Solo usa biblioteca estándar, sin importar SDK ni conectar a TWS.
- `archive_ibkr_contract_review.py` revalida SEC/Alpaca en una transacción de lectura, usa `PRAGMA query_only` y StorageGovernor antes de archivar. Dos ejecuciones conservan un único original idéntico. No modifica tablas ni catálogos del proveedor; no hay migración.
- El informe exacto se conserva en `data/ibkr/contracts/raw/402f5bb6c22eba424497a961ad4eabb2ae5855a1e50c9345f128ca8db2a566a2.json.gz`, **670 bytes comprimidos**. La copia de `output/ibkr-contract-probe-20261111.json` permanece intacta. No hubo nuevas peticiones a proveedores para esta conciliación.
- `identity_evidence` añade `current_contract` y `native_currency_state=DOCUMENTED_OBSERVATION` al diagnóstico existente. `known_from` de la empresa/clase sigue separado del conocimiento de la revisión IBKR. Las consultas anteriores a esta revisión no reciben la divisa posterior.
- Si falta o cambia el informe IBKR, se retira solo su confirmación de divisa; SEC/Alpaca conservan su evaluación independiente. Si cambian el catálogo o la clase SEC, se retiran también la asociación IBKR y la divisa. Datos no verificables nunca promocionan readiness.
- Política del diagnóstico `daily-trend-data-v2`: pasa la comprobación de divisa del contrato observado. Identidad histórica, ajustes, conocimiento en cada sesión, universo y derechos para minería conservan sus bloqueos. Apple sigue con 21 sesiones exploratorias; Microsoft/Walmart, sin histórico del piloto. Los tres BACKTEST BLOCKED y `execution_ready=false`.

## Interfaz

Centro de activos → ficha de la acción o emisor vinculado → Precios e históricos → Calidad para investigación → Ver comprobaciones y evidencia. El bloque «Contrato observado · IBKR» muestra símbolo/divisa/bolsa, conId/ruta, inicio de captación, fecha de revisión y huella del informe local. Los detalles empiezan plegados. Las fechas no son un refresco de cotizaciones. No se heredan precios en el registro del emisor SEC ni se alteran los campos originales del catálogo Alpaca.

## Verificación

- **98 tests backend** correctos: contratos IBKR, diagnóstico histórico, lectura de mercado y seguridad. Incluyen evidencia futura/corrupta/ausente, moneda/plaza/clase erróneas, ambigüedad, cambios de catálogo, idempotencia y órdenes 403. Log privado `output/b23-ibkr-tests-final.log`.
- **16 tests frontend** afectados correctos; TypeScript y build correctos. Contrato incompleto, URL insegura, moneda contradictoria y conocimiento futuro se rechazan antes de mostrarlo. No se ha repetido la suite completa. Avisos preexistentes: TestClient/httpx y tamaño del bundle 3D.
- Conciliación real repetida con el mismo corte, igualdad entre fichas SEC/Alpaca y consulta anterior a la revisión. **13 tablas protegidas y los 18 modelos preservados por hash**. Evidencia privada `output/b23-ibkr-reconciliation-20261111.json`.
- Navegador local comprobado con Apple: diagnóstico y detalle IBKR visibles, USD/NASDAQ/SMART y las fechas correctas, bloqueo de backtest conservado. Servicios locales disponibles en 8000/5173; arranque fuera del aislamiento necesario para acceso desde navegador. No se alteró la oficina ni se enviaron peticiones de captación desde la UI.
- API local comprobada con las tres acciones y `POST /api/orders=403`, evidencia `output/b23-ibkr-runtime-20261111.json`. Al arrancar los servicios, la agenda P2 existente A22 refrescó HT/ZSE: entre las 13 tablas protegidas solo cambió su `last_seen_at` (09-11 18:48 UTC → 11-11 15:38 UTC). Una reconstrucción **en memoria**, sin restaurar/borrar datos, reproduce exactamente el hash previo de `universe_listings` al sustituir solo ese timestamp. Las otras 12 tablas y los 18 modelos permanecen idénticos. Auditoría privada `output/b23-ibkr-runtime-audit-20261111.json`. Ese refresco es ajeno al archivo/lectura IBKR y no supone una agenda nueva.

## Continuidad propuesta al entregar — sustituida por D045

La auditoría posterior fija B3.1 como próxima construcción y D1–D3 como cierres para datos reales; ver [ROADMAP](../../tasks/ROADMAP.md). La propuesta original siguiente queda como historia: continuar **B2.3: identidad durante el histórico**. Elegir un intervalo acotado del piloto, contrastar clase, símbolo, mercado y cambios efectivos con fuentes fechadas; registrar aliases y huecos con conocimiento local explícito. Después conciliar ajustes/acciones corporativas y ampliar las series bajo presupuesto. El segundo piloto europeo IBKR requiere revisar acceso/derechos/coste cero antes de pedir precios o históricos.

IBKR queda como evidencia complementaria de identidad; SEC mantiene contabilidad y Alpaca la ruta PAPER prevista. B3 minería, B4 validación, B5 autonomía/riesgo y B6 OMS/Alpaca PAPER siguen detrás de sus gates. No se repite instalación del SDK, bootstrap, ciclo n8n ni sede visual.
