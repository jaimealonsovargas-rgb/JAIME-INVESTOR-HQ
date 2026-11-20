# Estado real de JAIME

Actualizado 20-11-2026, Europe/Madrid. **B5 completado.** El ciclo de n8n verificó el expediente B4 y registró la observación de BRK.B. Cero candidatas y cero órdenes. La decisión identifica el expediente, la política aplicada, la ventana y su vencimiento. [Entrega B5](docs/actual/ENTREGA_B5.md).

| Área | Implementado / comprobado | Falta |
|---|---|---|
| Producto | Oficina 3D aceptada; Centro de activos, modelos, calidad y operación | Laboratorio y seguimiento de estrategias junto a sus contratos reales |
| Catálogo | 8.023 emisores; 10.430 registros SEC, 14.407 Alpaca y 1 ZSE | Cobertura de datos por activo y ampliación de identidad revisada por lotes |
| Contabilidad | Cuentas/documentos de 100 emisores; Apple v8, Microsoft v6 y Walmart v7, 21 versiones | Ampliar modelos; ratio Walmart pendiente; DCF/consenso/transcript sin inputs suficientes |
| Precios e históricos | 21 barras Apple y 252 BRK.B/IEX; este último admitido para un ensayo retrospectivo personal local | Cobertura ampliada y admisión por instrumento/periodo/uso; no acreditada a escala de miles |
| IBKR | D1 acceso acotado conservado; D2 cola durable/transporte aislado probado offline | Archivo real denegado; derechos de cuenta/uso/retención pendientes |
| Research | 30 roles definidos; ciclo descriptivo y artefactos parciales | P4 PARTIAL; debate/tesis analíticas no aceptados; no bloquean el núcleo B3 |
| n8n | Agenda piloto 00/06/12/18 UTC. Riesgo B5 y revisión contable SEC comparten ventana con recuperación por identificador. | Mantener el ordenador y los servicios disponibles para las próximas ventanas |
| Minería / validación | B3.1, B3.2 y B4 entregados. Diez ensayos reales inventariados, tres variantes descartadas y expediente verificable para riesgo | Ampliar los activos y las hipótesis con muestras independientes admitidas por alcance |
| Riesgo / ejecución | B5 registra decisiones PAPER y vetos por ventana. Capital y exposición se reservan dentro de cada lote. MASTER separado. | B6, simulador de órdenes, persistencia de envíos, fills y reconciliación |

Base: `0015_history_batches`, ensayada en copia y aplicada; 43 tablas anteriores intactas, integridad correcta y cero fallos FK. Evidencias `output/d2-20261117/{before,rehearsal,applied}.json`. Presupuesto: 4 GiB data, 12 GiB output, 16 GiB conjuntos, 5 GiB libres y reserva por unidad. No limpieza automática de evidencia.

## Siguiente entrega

**B6 · Gestión de órdenes y reconciliación PAPER.** La primera entrega trabaja con un broker simulado local y escenarios de fallo. [Ficha única](tasks/ACTUAL.md) · [Orden](tasks/ROADMAP.md).

## Evidencia y límites

- [20-11 · Riesgo B5](docs/actual/ENTREGA_B5.md). Ciclo real repetido con el mismo recibo. Política PAPER v2 con presupuesto de pérdida bajo estrés por instrumento. [Evaluación de Day Trader](docs/actual/DAY_TRADER_ADAPTACION.md).

- [20-11 · Minería y B4](docs/actual/MINERIA_REPOS_2026_11_20.md). Vista de diseño para el proponente y piloto Optuna 4.9.0 aislado, con validación del entorno. Sobre un fixture se registraron 192 sugerencias, 61 configuraciones únicas y tres podas. La búsqueda evitó seis de 244 cálculos de estrategia. La auditoría posterior los completó. Reproducción exacta de la traza y del expediente real B4. Pasaron 186 pruebas de integración y regresión del ámbito afectado.

- [B4, 19-11](docs/actual/ENTREGA_B4.md). Revisión local de los diez ensayos y sus 30 eventos, con cero sesiones reservadas. Dos validaciones produjeron el mismo expediente. Las cuatro tablas contables de MASTER y las tres quant conservaron sus hashes. La suite también verificó el HTTP 403 de órdenes.

- [B3.2, 19-11](docs/actual/ENTREGA_B3_2.md): 111 tests; 10 ensayos, 30 eventos y un snapshot compartido. Registro completo antes del cálculo, CLI idempotente y diez reproducciones deterministas con hashes iguales. `output/b32-20261118/{tests.log,validation.json,RESULTADOS.md}`. Protocolo original congelado; no reajuste de parámetros tras pérdidas.
- Schema 0015 conservado, integridad ok/FK 0. Cuatro tablas contables conservan recuentos/hashes exactos. Refresco concurrente A15 documentado en `validation-context.json`; no se afirma inmutabilidad de todas las tablas de datos. Revisión privada Alpaca personal local válida hasta 18-12-2026 15:45:30 Europe/Madrid; plazo interno, no obligación de retención del proveedor. Soporte aportado por usuario y generado con IA, sin autenticar correo. Ninguna orden ni nueva migración.

- Preparación B3.2 del 18-11, conservada como antecedente: protocolo previo al cálculo y consulta preparada. Ese bloqueo se resolvió para el alcance concreto en D051; no reabrirlo como tarea pendiente.

- [D3 implementado](docs/actual/ENTREGA_D3_ADMISION.md): 134 pruebas distintas aprobadas (130 consolidadas y cuatro casos nuevos; repetición final del motor sin doble cómputo). Logs `output/d3-tests.log` y `output/d3-engine-final-tests.log`. Registro confiable real vacío, sin dataset real admitido ni campaña iniciada.

- D3: 49 tablas conservadas exactamente, 14 evaluaciones congeladas y cuatro comandos CLI verificados; `output/d3-20261117-final/acceptance.json` y `cli-*.json`. Apple: 21 barras; las otras dos series revisadas: sin histórico. Ningún dataset real admitido.

- Runtime verificado el 17-11 a las 23:45:59 Europe/Madrid: schema 0015 correcto, órdenes 403 y MASTER NAV/cash 10.000 EUR ficticios, cero posiciones; `output/d3-runtime.json`.

- [D2 entregado](docs/actual/ENTREGA_D2_LOTES.md): 92 pruebas distintas (69 backend, dos regresiones, 21 SDK offline). Fixture 1.000 instrumentos/unidades en 11,457 s con StorageGovernor simulado; no benchmark de red/producción. `UNVERIFIED_ACCOUNT_AND_USE_SCOPE`, gate IBKR denegado y sin descarga real.

- [D1 entregado](docs/actual/ENTREGA_D1_IBKR_DATOS.md): 64 tests distintos pasados; cinco sesiones y feed diferido confirmados. Solo diagnóstico privado, sin precios persistidos ni nuevas copias de base. Doce tablas protegidas intactas, MASTER 10.000 EUR ficticios y órdenes 403. `output/ibkr-data-probe-20261116-r2.json`, `output/d1-validation-20261116.json`. Archivo/minería masivos sujetos a derechos pendientes, no certificados por el acceso.

- [B3.1 entregado](docs/actual/ENTREGA_B3_1.md): 104 tests (33 nuevos quant), migración comprobada, tres ensayos y un dataset sintético compartido. Evidencias `output/b31-tests.log`, `output/b31-cli.json` y `output/b31-20261111/`. Las dos copias de seguridad/verificación ocupan 954,59 MiB; ninguna nueva descarga de mercado.
- Evidencia histórica B3.1 (11-11): backend recargado y verificado a las 17:44:53 Europe/Madrid: salud correcta/schema 0014, órdenes 403 y MASTER 10.000 EUR ficticios, cero posiciones; `output/b31-20261111/runtime.json`.

- Auditoría de lectura actual: `output/audit-20261111-before.json` y cierre `output/audit-20261111-validation.json`; recuentos y huellas, sin secretos.
- Cierre documental: 25 entradas y 138 enlaces locales comprobados; 22 documentos archivados, 318 archivos de implementación y 13 tablas protegidas/18 modelos sin cambios.
- Última entrega funcional previa: [contratos IBKR](docs/actual/ENTREGA_B2_3_CONTRATOS_IBKR.md), **98 backend / 16 frontend afectados, TypeScript/build y navegador correctos**. Son resultados anteriores conservados, no pruebas nuevas de esta auditoría.
- Conciliación IBKR preservó 13 tablas/18 modelos. Al arrancar después, A22 refrescó solo `last_seen_at` de HT/ZSE entre esas tablas; reconstrucción en memoria reprodujo exactamente el hash anterior. Evidencias `output/b23-ibkr-reconciliation-20261111.json`, `output/b23-ibkr-runtime-audit-20261111.json`.
- `dataset_assessment.py` conserva el diagnóstico legacy Alpaca separado. El CLI D3 es la ruta canónica de preparación B3.2; sus validadores no admiten datos reales sin evidencias confiables. Descargar más barras por sí solo no cierra los gates.

PAPER ONLY, 0 EUR, MASTER separado y `POST /api/orders=403` vigentes. Autorización de desarrollar P5/P6 existente; promoción de datasets y activación futura requieren sus gates técnicos. Ninguna rentabilidad está validada.

[Auditoría y hallazgos](docs/actual/AUDITORIA_CONTINUIDAD_2026_11_11.md) · [Bitácora completa anterior](docs/archive/2026-11-11-continuidad/STATUS.md).
