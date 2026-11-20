> ARCHIVO INACTIVO · copia anterior a la auditoría del 11-11-2026. Sus próximos pasos y autorizaciones no gobiernan el trabajo actual. Enlaces relativos reubicados; contenido histórico conservado.

# Hoja de ruta única de JAIME



27-10-2026. P0–P7 quedan como dominios e historia. **P5 y P6 Alpaca PAPER autorizadas. LIVE excluido.** Circuito acordado: n8n → datos → 30 especialistas → minería → riesgo → Alpaca PAPER → seguimiento. El orden de construcción verifica dependencias antes de activar el siguiente tramo. Estado y evidencia en STATUS.



| Bloque | Estado | Resultado | Aceptación |

|---|---|---|---|

| B0 Reorganización | Completado | Mandato, auditoría y cola única | Entradas coherentes, histórico separado y enlaces comprobados |

| B1 Integridad y claridad | Completado el 28-10; verificación en STATUS | Datos sin colisiones y paneles honestos | Revisiones/historia/aliases/mandatos + frescura/capacidades + ficha persona |

| B2 Universo y empresas | En curso; B2.1/B2.2 completos, B2.3 lectura/vínculos del piloto y diagnóstico, B2.4 conciliado, B2.5 verificado | Tres vínculos actuales y divisa observada IBKR revisada; 21 sesiones Apple exploratorias; ningún histórico aceptado para backtest. Presupuesto y conservación entregados; pendientes identidad temporal, históricos y escala | Ingesta incremental, PIT, paginación, normalización y modelos auditables |

| B3 Laboratorio determinista | Pendiente; P5 autorizada | Experimento reproducible con costes | Genome, registro completo, backtest exacto, aislamiento MASTER |

| B4 Validación y selección | Pendiente; P5 autorizada | Candidatos/descartes explicables | Walk-forward, OOS, genealogía, costes adversos, robustez y diversidad |

| B5 n8n, autonomía y riesgo | Autorizado, pendiente | Ciclos completos, recuperación y decisiones | Idempotencia n8n/JAIME, recursos, selección de roles y veto determinista |

| B6 Alpaca PAPER | Autorizado, pendiente de gates | Operación simulada externa reconciliada | RiskGate → OMS/outbox → Alpaca PAPER → fills/reconciliación → seguimiento |



## Dependencias y entregas



B1: [entrega y evidencia](../../../actual/ENTREGA_B1.md). Identidades y presentación corregidas antes de ampliar captación. El trabajo siguiente es [B2](ACTUAL.md).



B2: Entity/Instrument/Listing + aliases temporales; fuentes por CIK/filing, periodo, unidad y revisión; bootstrap por lotes reanudables y cuotas. Separar universo de conocimiento, cotizaciones e históricos aptos. Centro de activos con búsqueda/paginación, cobertura y fechas. DatasetManifest/readiness por familia. Pruebas de revisión futura, cambios de ticker, delistings, ajustes y FX cuando correspondan. Escala por hitos: 100 emisores piloto, 1.000 entidades identificadas, después miles con cobertura real declarada.



B2 incluye la adaptación de **Model Builder, Earnings Reviewer y Valuation Reviewer**: normalización → modelo financiero determinista → actualización por resultados → revisión independiente. Piloto de tres emisores con distinto ejercicio fiscal y una revisión antes de escalar. DCF/comps solo si están los inputs. Consenso/transcript ausentes se declaran; no se fabrican. Estas rutas aportan investigación y features, no sustituyen P5. [Diseño específico](../../../actual/AGENTES_FINANCIEROS_ANTHROPIC.md).



B3: contratos y fixtures pueden desarrollarse tras B1 en paralelo al tramo final de B2; experimentos reales requieren dataset admisible. Hipótesis/protocolo antes de resultados; todos los intentos registrados. Primera familia tendencia diaria y controles benchmark/cash; prueba manual exacta, costes, cronología, repetibilidad, cancelación/restart. UI de laboratorio junto al contrato real, sin métricas de relleno.



B4: muestras congeladas y presupuesto de búsqueda, walk-forward, purga/embargo cuando aplique, OOS con exposición heredada y estabilidad. Probar look-ahead, revisión futura, survivorship, selección solo de ganadores y reutilización de holdout. Cero supervivientes es válido. Comité opcional, estadísticas y veto deterministas.



B5: extender AutonomyEvent/ResearchTask con rutas por datos/filings y deterioro de estrategias cuando exista su semántica. ResourceGovernor para I/O/CPU/LLM, prioridades/backpressure, presupuestos y caché por versión. Continuar con oficina cerrada, no con PC apagado. Portfolio/RiskEngine produce propuestas con escenarios/límites, sin órdenes. BACKTEST y MASTER separados.



B6 ya tiene autorización del usuario en este chat. Simulador interno para pruebas de contrato y fallos, seguido de Alpaca PAPER: cuenta/credenciales separadas, riesgo revalidado, client_order_id, UNKNOWN sin reenvío ciego, fills parciales y reconciliación. Activación progresiva únicamente al superar los gates; LIVE fuera de alcance.



n8n se integra mediante un contrato de ciclos idempotentes; primer flujo de captura/research en modo sombra tras el piloto B2, promoción al circuito completo en B5/B6. No duplicar agendas con el scheduler actual ni trasladar órdenes a nodos n8n. Ver [arquitectura de seis etapas](../docs/actual/VISION_Y_ARQUITECTURA.md) y [suficiencia de proveedores](../docs/actual/PROVEEDORES_Y_COBERTURA.md).



## Forma de trabajar



Un bloque activo; problema, comportamiento esperado y prueba de salida por cambio. Actualizar ACTUAL/STATUS, sin otro plan maestro paralelo. Migraciones conservadoras, backfill explícito e historia preservada. Tests focalizados y regresión/build proporcionales; revisión visual agrupada. Separar evidencia de ingeniería, validez financiera y experiencia de usuario. Mantener autorizaciones previas: no pedir permiso rutinario por activo, job o subpaso ya autorizado.



08-11: [B2.3 identidad y diagnóstico](../../../actual/ENTREGA_B2_3_IDENTIDAD_HISTORICOS.md) entrega tres vínculos actuales y razones reproducibles de bloqueo para backtest; [B2.4](../../../actual/ENTREGA_B2_4.md) conciliado y [B2.5](../../../actual/ENTREGA_B2_5.md) n8n en sombra verificado. 09-11: presupuesto y conservación entregados; [TWS API evaluada como candidato](../docs/actual/IBKR_TWS_EVALUACION.md). 11-11: piloto de contratos conectado y [revisión USD/SEC/Alpaca archivada](../../../actual/ENTREGA_B2_3_CONTRATOS_IBKR.md); no hay precios IBKR ni proveedor continuo. Siguiente: identidad temporal y ampliación histórica acotada. Continuidad de divisa/clase/mercado, ajustes, streaming y benchmark conservan sus pendientes. [Day Trader](../../../actual/DAY_TRADER_ADAPTACION.md) aporta referencias para las fases indicadas; su control de cobertura anual está incorporado en B2.4.

