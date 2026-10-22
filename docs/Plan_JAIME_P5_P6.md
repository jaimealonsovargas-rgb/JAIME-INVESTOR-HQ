# JAIME INVESTOR HQ — Fábrica de estrategias, validación extrema y plataforma para una futura operativa automatizada

> **Tipo de documento:** investigación estratégica y especificación de diseño para revisión por Codex.\
> **Fecha del informe de origen:** 21 de octubre de 2026.\
> **Estado:** propuesta; **NO constituye una autorización para implementar P5, P6 o ejecución real**.\
> **Ámbito:** JAIME INVESTOR HQ, ordenador Windows local, 16 GB RAM, un único LLM local secuencial, presupuesto adicional objetivo de 0 €, MASTER ficticio de 10.000 €, **PAPER ONLY**.

## Instrucciones de lectura para Codex

Este documento conserva el contenido sustantivo de la investigación avanzada compartida en el chat y reorganiza los requisitos como documento Markdown legible por máquinas y personas. **Es un documento de investigación, no una descripción verificada del código actual ni un mandato de implementación automática.**

1. Leerlo entero antes de proponer cambios.
2. Confrontar cada propuesta con los archivos reales del repositorio, sus `role_id`, `AGENTS.md`, `STATUS.md` y sus puertas de fase. En caso de conflicto, explicar la discrepancia, **no** sustituir silenciosamente las decisiones vigentes.
3. Preservar el único LLM local; los «agentes» de este documento son **roles lógicos secuenciales**, no decenas de procesos/modelos.
4. Mantener MASTER y patrimonio ficticio, P2/P4 en sus estados actuales y las prohibiciones vigentes. **No activar P5 ni P6, no configurar broker LIVE, no habilitar órdenes, no modificar `/api/orders=403`** sin nueva autorización expresa y revisión de seguridad.
5. Tratar tarifas, disponibilidad regional, capacidades de APIs y regulación mencionadas como **afirmaciones de la investigación que requieren verificación documental actualizada**, no como datos garantizados.
6. Las marcas de cita del informe original del tipo `citeturn14search1` proceden de Investigación avanzada en ChatGPT. **No son URLs resolubles fuera de ese informe**. Se preservan para evitar perder trazabilidad, pero Codex deberá obtener las referencias primarias y documentar URL, título, fecha de consulta y alcance antes de implementar integraciones o afirmar vigencia.
7. La entrega inmediata solicitada a Codex después de leer este documento debe ser **auditoría de encaje + diseño técnico + plan de fases + pruebas de aceptación**, no código de ejecución ni cambios peligrosos.

---

# 1. Veredicto ejecutivo

**Recomendación principal del informe: Interactive Brokers (IBKR) como futuro bróker multiactivo de JAIME INVESTOR HQ**, sujeto a verificar condiciones, acceso, precios, disponibilidad de cuenta y mercados desde España. **No utilizar IBKR ni ningún exchange como laboratorio central de estrategias.** El cerebro cuantitativo, los experimentos, su trazabilidad y las decisiones de aceptación deben pertenecer a JAIME y ser independientes de cada bróker.

El objetivo excede un bot de Bitcoin: investigación multicompañía, estrategias cuantitativas, cartera multiactivo y quizá, en una etapa posterior y autorizada, automatización de órdenes. El informe señala que IBKR ofrece acciones, opciones, futuros, FX, bonos, fondos y otras clases en aproximadamente **170 mercados de 40 países** y que Interactive Brokers Ireland Limited figura en CNMV con número **5023**, datos que se deben volver a verificar en los registros oficiales. Referencias del informe original: `citeturn13search1turn17search2`.

La cuenta **IBKR PAPER** y las interfaces Web API / TWS API se describen como cercanas a LIVE, lo que permitiría reutilizar conceptualmente un adaptador de órdenes en un futuro sin rehacer la lógica de investigación. Pero el PAPER no simula perfectamente el mercado: *top of book*, profundidad y tipos de órdenes tienen limitaciones; TWS/IB Gateway necesitan mantenimiento/reinicio/autenticación; y las suscripciones de datos en tiempo real suelen tener costes. Referencias originales: `citeturn14search1turn14search18turn14search5turn19search16turn19search18`.

**Cuatro decisiones de diseño:**

- **IA para idear, formular hipótesis y explicar resultados:** sí.
- **Python para backtests y cálculos financieros deterministas:** sí.
- **Red Team estadístico y de riesgo para intentar falsar estrategias:** sí.
- **LLM con capacidad directa para decidir órdenes arbitrarias y enviarlas al bróker:** no.

Una conexión de ejecución **futura** deberá estar aislada y supeditada a límites deterministas, conciliación, aprobación y permisos mínimos. En la fase actual **no se enviará ninguna orden al mercado**.

## 1.1. Arquitectura objetivo

```text
                         JAIME INVESTOR HQ
                                 │
                                 ▼
                        P2: DATOS + EVIDENCIA
                  point-in-time, calidad, licencias
                                 │
                                 ▼
                       FÁBRICA DE ESTRATEGIAS
                 hipótesis + formalización + variantes
                                 │
                                 ▼
                    BACKTEST DETERMINISTA PYTHON
                                 │
                                 ▼
                       RED TEAM CUANTITATIVO
                    sesgos, costes, OOS, fragilidad
                                 │
                 ┌───────────────┴──────────────┐
                 ▼                              ▼
          RECHAZADAS                        SUPERVIVIENTES
                 │                              │
                 ▼                              ▼
        STRATEGY GRAVEYARD               OOS INTOCABLE
                                                │
                                                ▼
                                       PAPER INTERNO
                                                │
                                                ▼
                                       PAPER DEL BRÓKER
                                                │
                                                ▼
                                        SHADOW TRADING
                                                │
                                                ▼
                                     RIESGO DETERMINISTA
                                                │
                                                ▼
                                   REVISIÓN/AUTORIZACIÓN
                                                │
                                                ▼
                                  ADAPTADOR IBKR (FUTURO)
                                                │
                                                ▼
                                   LIVE: FUERA DE ALCANCE
```

La separación **P2 → motor científico → agentes especializados → validador → paper → potencial ejecución** es más importante que el nombre del proveedor. El manual institucional previo de 30 especialistas sostiene «cálculo fuera del LLM, juicio dentro del LLM», evidencia *point-in-time*, salida verificable y separación entre hechos e inferencias. El informe menciona el manual de origen con la cita local `fileciteturn0file0`; esta referencia también debe vincularse a un archivo real del repositorio para ser utilizable por Codex.

---

# 2. Objetivo de la fábrica de estrategias

La preocupación «**todas las estrategias parecen perfectas**» no debe interpretarse como buena noticia. Es una **alarma de calidad de la validación**. Cuando se prueban cientos o miles de configuraciones sobre un mismo histórico, seleccionar la mejor favorece confundir suerte retrospectiva con habilidad predictiva.

El informe remite a la literatura académica de Bailey, Borwein, López de Prado y Zhu sobre *Probability of Backtest Overfitting* (PBO) y *Combinatorially Symmetric Cross-Validation* (CSCV), al **Deflated Sharpe Ratio** (DSR), a *White's Reality Check* y a *Hansen's SPA* como respuestas al problema de búsqueda múltiple y *data snooping*. Referencias originales: `citeturn15search0turn15search12turn15search6turn15search14turn15search1turn15search8`.

**Objetivo correcto:** «Hipótesis económicas cuya rentabilidad aparente sobreviva a intentos sistemáticos de demostrar que es casualidad, contaminación temporal, sobreajuste, fragilidad, falta de liquidez o una ilusión de costes».

No se busca «la estrategia con el mayor Sharpe» ni una `PERFECT_STRATEGY`. Nunca debe existir ese estado. La simulación permite identificar defectos; **no demuestra que una estrategia no pueda fallar en el futuro**.

## 2.1. ADN o lenguaje interno de estrategias

Evitar que el LLM genere y ejecute 500 scripts arbitrarios inconexos. Debe formular hipótesis en un **DSL/contrato tipado**, que un generador confiable transforme en experimentos comparables, limitados y reproducibles. Ejemplo ilustrativo del informe:

```yaml
strategy_id: EQ_MOM_000184
family: cross_sectional_momentum

universe:
  asset_class: equities
  region: US_EU
  liquidity_floor: ...
  listing_age_min: ...

signal:
  primary:
    metric: total_return
    lookback: 252d
  exclusion:
    recent_period: 21d

portfolio:
  selection: top_decile
  weighting: inverse_volatility
  rebalance: monthly
  max_position: ...
  max_sector: ...

risk:
  vol_target: ...
  stop_policy: none
  max_drawdown_gate: ...

execution:
  order_style: next_open
  slippage_model: ...
  commission_model: ...
  participation_limit: ...

research:
  hypothesis: >
    ...
  economic_mechanism: >
    ...
```

Los `...` son marcadores de campos a especificar y validar, **no datos operativos ni valores por defecto seguros**. Ejemplo de propuesta de un especialista: «Estudiar momentum de 12 meses excluyendo el último mes, solo entre compañías con rentabilidad sobre el capital elevada». Python prueba un espacio definido de parámetros; el LLM interpreta los resultados y límites.

El flujo debe ser:

```text
HIPÓTESIS DOCUMENTADA
          ↓
PLANTILLA DE ESTRATEGIA
          ↓
ESPACIO DE PARÁMETROS ACOTADO
          ↓
EXPERIMENTOS CONTROLADOS Y REGISTRADOS
```

El LLM no debe poder ejecutar código no confiable en el host ni fabricar retornos, operaciones o estadísticas.

## 2.2. Familias que pueden investigarse progresivamente

| Familia | Hipótesis/ejemplo | Condiciones de datos |
|---|---|---|
| Momentum cross-sectional | Ganadores relativos frente a perdedores | Universo histórico correcto, rentabilidad total |
| Trend following | Persistencia temporal de tendencias | Precios y costes según frecuencia |
| Value | Precio frente a fundamentales | Fundamentales point-in-time |
| Quality | ROIC, margen, balance, calidad del beneficio | Estados normalizados y disponibles en fecha |
| Quality + Value | Calidad a precio razonable | Ambas familias sin leakage |
| Reversión a la media | Desviaciones extremas | Muestreo/costes adecuados |
| Low volatility | Estabilidad y prima/riesgo | Historial suficiente |
| Carry | Remuneración de sostener una exposición | Curvas, costes y contratos pertinentes |
| Factores múltiples | Señales con aportación independiente | Control de colinealidad/múltiples pruebas |
| Rotación sectorial | Régimen macro y liderazgo | Composición histórica, calendario de publicación |
| Event-driven | Resultados, revisiones, corporate actions | Eventos con fecha de publicación real |
| Pairs / relative value | Relaciones de precios y economía entre activos | Sesgos y costes, validación de estabilidad |
| Asset allocation | Distribución entre clases | Índices, reinversión, FX, costes |
| Volatilidad/opciones | Distribuciones, primas, exposiciones | **Solo con datos auténticos de opciones** |
| Cripto | Momentum, carry, funding, basis, futuros | Series y permisos específicos de crypto |

No todas las familias tienen que estar activas de entrada. P2 debe determinar la **matriz de cobertura** y cada rol debe abstenerse si carece de inputs válidos.

## 2.3. Registro de todos los intentos — Strategy Registry y Graveyard

**Prohibido guardar únicamente estrategias ganadoras.** La existencia de miles de intentos es relevante para la evaluación estadística del ganador. Mantener genealogías padre/hijo, hipótesis, muestras, versión del código, snapshots y hashes de los datos, configuración, costes y motivos de descarte. Registro conceptual:

```json
{
  "experiment_id": "EXP-008214",
  "strategy_family": "quality_momentum",
  "parent_strategy": "EXP-008103",
  "hypothesis_id": "HYP-204",
  "data_snapshot_hash": "...",
  "code_hash": "...",
  "parameters": {},
  "tested_at": "...",
  "in_sample": {},
  "validation": {},
  "out_of_sample": {},
  "cost_model": "...",
  "status": "REJECTED",
  "rejection_reason": "parameter_instability",
  "counts_as_trial": true
}
```

Ejemplo: si se prueban 10.000 variantes y se comunica solo la mejor, el Sharpe de esa variante resulta estadísticamente engañoso sin información de los otros 9.999 intentos. Los modelos DSR/PBO requieren contexto adecuado de selección y multiplicidad. Referencias originales: `citeturn15search6turn15search14`.

El **Strategy Graveyard** conserva de forma auditable rechazos, fallos, explicaciones y resultados, sujeto únicamente a políticas técnicas de retención razonables y trazabilidad. No borrar perdedoras porque «estropean el ranking».

## 2.4. Hipótesis ex ante frente a narrativa ex post

Antes de iniciar un gran barrido paramétrico registrar:

```text
QUÉ creo que ocurre
POR QUÉ debería ocurrir (mecanismo económico)
QUÉ variables/datos lo representarían
CUÁNDO y para qué universo sería válido
CUÁNDO debería dejar de funcionar
QUÉ observación falsaría la hipótesis
CUÁNTOS experimentos se autorizarán
```

Evitar «probarlo todo → seleccionar ganador → inventar después una explicación plausible». El LLM tiene una capacidad elevada para racionalizaciones retrospectivas.

## 2.5. Presupuesto de investigación estadística

Introducir `RESEARCH_BUDGET` de intentos, no euros, con trazabilidad de variantes y familias investigadas:

```text
Familia: quality_momentum
Experimentos registrados: 387
Variantes materialmente independientes: ...
Optimización utilizada: ...
Datasets consultados: ...
```

Diferenciar explícitamente el **número de combinaciones** del **número de hipótesis independientes**. Limitar explosión combinatoria; declarar el tamaño real de la búsqueda al realizar inferencia estadística.

---

# 3. P5: laboratorio de descubrimiento, falsación y riesgo

**Nombre propuesto para P5:** `Strategy Discovery, Adversarial Validation & Risk Laboratory`. El informe insiste en no hacer de P5 una simple pantalla de backtests. P5 debe ser una **máquina para eliminar falsos positivos**.

## 3.1. Embudo de validación por gates

| Gate | Pregunta de auditoría | Resultado si falla |
|---|---|---|
| Integridad del dato | ¿Datos correctos, trazables, ajustados y existentes en esa fecha? | Rechazo por datos |
| Plausibilidad económica | ¿Hay hipótesis ex ante defendible? | Investigación sin promoción |
| Backtest base | ¿Existe señal histórica reproducible? | Rechazo |
| Sesgos | ¿Hay look-ahead, survivorship, leakage o contaminación? | Rechazo |
| Fricciones | ¿Se incluyen comisiones, spread, slippage y demás costes aplicables? | Solo research/rechazo |
| Robustez | ¿Resiste parámetros vecinos y supuestos razonables? | Cuarentena/rechazo |
| Múltiples pruebas | ¿La señal resiste ajuste por el proceso de selección? | Rechazo/degradación |
| Regímenes | ¿Se conoce cuándo funciona y cuándo falla? | Restricción de dominio/rechazo |
| Cross-market | ¿Existe capacidad de generalización si es parte de la hipótesis? | Restricción/rechazo |
| Out-of-sample | ¿Funciona en datos de prueba realmente no vistos? | Rechazo; sellar exposición |
| Paper interno | ¿Resiste ejecución futura simulada y contabilidad? | No promoción |
| Paper del broker | ¿Se comporta como se espera frente a una API paper externa? | No promoción |
| Shadow | ¿Las operaciones propuestas serían plausibles con mercado observado? | No promoción |
| Candidate | ¿Existe evidencia suficiente para siquiera debatir otra fase? | Sigue PAPER ONLY |

Una estrategia puede morir en cualquier puerta. No es obligatorio que funcione en todos los regímenes, pero sí especificar y probar su **dominio de validez**.

## 3.2. Contaminación temporal y fundamentales point-in-time

El mínimo para un dato fundamental histórico:

```text
period_end
published_at
available_to_strategy_at
restated_at
source_id
```

Ejemplo: saber que `FY2025 EPS = 5.20` no indica **cuándo** un inversor pudo conocer ese valor. Un backtest no puede usarlo en una fecha anterior a su publicación o disponibilización real. P2 tiene que registrar revisiones y fuentes y responder «¿qué sabía JAIME en la fecha t?». Requisito innegociable para estrategias fundamentales, no una mejora estética.

## 3.3. Survivorship bias e identidad de valores

No construir histórico a partir de la lista **actual** de integrantes del S&P 500 (o de cualquier índice), porque el universo histórico también incluye empresas quebradas, retiradas, fusionadas, adquiridas o expulsadas. Sin universo **point-in-time** no atribuir validez a backtests cross-sectional que lo requieran.

Distinguir siempre:

```text
company
security
listing
ticker
exchange
currency
```

Distinguir datos de cotización brutos/ajustados, splits, dividendos, spin-offs, mergers, derechos, cambios de ticker, ADR, delistings, corporate actions, fusiones y efectos de moneda. Un split no debe parecer una pérdida del 90 %, ni un cambio de ticker otra empresa.

## 3.4. Modelo de fricciones y ejecución

Conceptualmente:

\[
R_{net} = R_{gross} - Commissions - Spread - Slippage - MarketImpact - BorrowCosts - FundingCosts - OtherApplicableCosts
\]

*No todos los términos aplican a todos los activos y estilos.* Pero `NO_DATA` **nunca** se convierte automáticamente en coste 0. Si no es posible modelar la ejecución, etiquetar `BACKTEST_RESEARCH_ONLY` y/o `NOT_EXECUTION_VALIDATED`.

Evaluar escenarios de costes:

```text
coste base
coste × 1.5
coste × 2
coste severo
```

Ejemplo ilustrativo de mayor robustez: Sharpe bruto 2,1 → neto 1,6 → doble coste 1,2. Ejemplo ilustrativo de fragilidad: Sharpe bruto 2,1 → neto 0,3 → doble coste -0,7. **Estos valores son escenarios explicativos, no resultados de JAIME ni rendimientos previstos.**

## 3.5. Superficie y estabilidad de parámetros

Analizar vecinos en el espacio de parámetros, no solo el máximo:

```text
lookback 199 días → fuerte
lookback 200 días → fuerte
lookback 201 días → fuerte
```

es más defendible que un pico aislado:

```text
197 → malo
198 → malo
199 → excepcional
200 → malo
201 → malo
```

Métricas internas sugeridas:

```text
parameter_plateau_score
local_sensitivity
neighbor_performance
parameter_rank_stability
```

El Red Team pregunta si hay **región amplia de rendimiento razonable** o «aguja» casual de optimización.

## 3.6. Dependencia del resultado y leave-one-out

Descomponer PnL/rendimiento por **año, trimestre, régimen, activo, sector, operación y días extremos**; cuantificar proporción del beneficio procedente de los cinco mejores trades, mejor año, mejor activo o mejor sector. Si el 95 % proviene de tres operaciones, la conclusión debe reflejar alta concentración.

Tests leave-one-out o exclusión razonada:

```text
sin 2020
sin 2022
sin mega-cap tech
sin NVIDIA
sin Bitcoin
sin EEUU
sin mejor sector
```

No aplicar exclusiones de manera mecánica cuando no corresponda, pero investigar si la conclusión depende de un único episodio/componente.

## 3.7. Regímenes macro y de mercado

Registrar el rendimiento condicional por regímenes coherentes con la estrategia:

```text
inflación ↑ / crecimiento ↑
inflación ↑ / crecimiento ↓
inflación ↓ / crecimiento ↑
inflación ↓ / crecimiento ↓

volatilidad alta / baja
mercado bursátil alcista / bajista
crédito ajustado / relajado
tipos al alza / a la baja
```

No exigir que toda estrategia sea universal, sino que sus restricciones y escenarios adversos estén explícitos. Evitar clasificar un régimen usando información publicada **después** de la fecha del trade.

## 3.8. Métricas profesionales de validación

Registrar con convenciones y límites documentados:

- CAGR y retornos por periodo, volatilidad anualizada y Sharpe.
- Probabilistic Sharpe Ratio (PSR), Deflated Sharpe Ratio (DSR), PBO/CSCV cuando la metodología, muestras e independencia permitan estimarlos.
- Sortino, Calmar, maximum drawdown, average drawdown, *time under water*, duración de recuperación.
- Expected Shortfall, pérdidas de cola, asimetría, curtosis y discontinuidades.
- Hit rate, payoff ratio, profit factor, trade expectancy.
- Turnover, periodo medio de tenencia, exposición bruta/neta.
- Beta, correlaciones, concentración, sensibilidad al mercado y riesgos factoriales.
- Estimación de capacidad, liquidez, slippage, spread y costes.
- Estabilidad de parámetros, mercados, activos, sectores, años y regímenes.
- Concentración de trades y contribución de episodios extraordinarios.

Ejemplo de fórmula descriptiva:

\[
Sharpe = \frac{R_p - R_f}{\sigma_p}
\]

**Hay que definir frecuencias y convenciones.** PSR considera incertidumbre muestral y no normalidad; el número de observaciones condiciona la evidencia. DSR considera además selección entre múltiples estrategias. Referencias originales: `citeturn15search15turn15search6`.

## 3.9. Probabilidad de sobreajuste (PBO) y búsqueda múltiple

Inspirarse en Bailey et al. para estimar hasta qué punto las estrategias elegidas dentro de la muestra se degradan en combinaciones de evaluación fuera de muestra. Reportar siempre:

```text
número de variantes evaluadas
metodología exacta de cálculo PBO/CSCV
número de observaciones
dependencia temporal y supuestos
intervalos/incertidumbre cuando proceda
límites por poca muestra o correlación de estrategias
```

**No presentar `PBO = 23.8127 %` como certeza objetiva.** Complementar con pruebas ajustadas por búsqueda (DSR, White Reality Check/Hansen SPA cuando aplicables), no sobreinterpretar resultados estadísticos.

## 3.10. Out-of-sample final realmente intocable

**Una vez que el investigador, el LLM o la optimización han visto un resultado en un periodo de test, ese periodo deja de ser completamente no visto para esa familia derivada.**

Patrón prohibido:

```text
OOS falla → ajustar parámetros → reusar mismo OOS
         → ajustar otra vez → reusar mismo OOS → «éxito»
```

Guardar genealogía de estrategia:

```text
STRAT-A
 ├── STRAT-A1
 ├── STRAT-A2
 │    ├── STRAT-A2a
 │    └── STRAT-A2b
 └── STRAT-A3
```

Si el padre utilizó para ajuste el año 2025, no declarar que los descendientes aprendidos de ese fallo conservan 2025 como prueba virgen. Usar separación temporal sellada, validación walk-forward y, finalmente, **paper prospectivo** como nuevo conjunto que se genera después de congelar la hipótesis.

---
# 4. Organización de agentes y funciones dentro de P5

No crear treinta procesos de IA. Los especialistas existentes realizan funciones lógicas especializadas y **secuenciales** con el mismo modelo local, y delegan cálculos masivos a Python. El objetivo es construir una **organización cuantitativa virtual**; no un único «agente que inventa estrategias».

| Función | Responsabilidad y salida | Prohibición clave |
|---|---|---|
| **Researcher** | Detecta anomalías, formula hipótesis económicas y las registra ex ante. Ejemplo: aceleración del FCF combinada con desapalancamiento frente a expansión del múltiplo. | No producir supuestos resultados de 40.000 backtests. |
| **Strategy Formalizer** | Traduce hipótesis a universo, features, señal, ranking, entrada/salida, rebalanceo, ponderación, riesgo y ejecución. | No declarar «estrategia cuantitativa» algo imposible de formalizar. |
| **Experiment Designer** | Selecciona variaciones científicamente razonables, presupuesto de búsqueda y pruebas; limita combinatoria. | No adaptar el espacio de búsqueda a resultados ya vistos sin registrar contaminación. |
| **Backtest Engine** | Ejecuta datos, posiciones, cash, comisiones y retornos mediante Python verificable. | No utilizar el LLM como calculadora ni datos futuros. |
| **Statistical Auditor** | Evalúa robustez, DSR, PSR, PBO, significación, muestras, multiplicidad y datos. | No presentar un Sharpe observado como evidencia suficiente. |
| **Execution Simulator** | Modela fills, slippage, fees, latencia, impacto estimado, liquidez y parciales. | No suponer fills perfectos ni costes cero por ausencia de datos. |
| **Adversarial Quant / Red Team** | Intenta falsar causalidad, integridad, generalidad y resultados de la estrategia. | No «mejorar» la estrategia manipulando después el holdout. |
| **Risk Director** | Evalúa pérdida permanente, concentración, dependencia factorial y correlaciones. | No confundir rentabilidad histórica con capacidad de soportar riesgos. |
| **Portfolio Constructor** | Combina estrategias complementarias y controla riesgos cruzados. | No seleccionar únicamente por Sharpe individual. |
| **Strategy Chair** | Emite veredicto sustentado, con pruebas pendientes y factores de invalidación. | No inventar claims nuevos ni declarar estrategias perfectas. |

La misma arquitectura de 30 roles existente puede alimentar el laboratorio: analista fundamental encuentra anomalía económica; valoración formaliza una señal potencial; Quant determina cómo probarla; Data Quality valida fechas/entidades; Risk/Bear atacan; Bull produce la mejor defensa compatible con la evidencia; Chair adjudica. **No sustituir ni renombrar automáticamente los `role_id`**.

## 4.1. Ejemplo de configuración del Experiment Designer

```text
FCF acceleration window:
  2Q / 4Q / 6Q

leverage filter:
  none / median / quartile

rebalance:
  weekly / monthly / quarterly
```

Es un ejemplo de espacio de parámetros; se debe probar si existen fundamentos e historia suficiente. **No ejecutar combinaciones sin registrar todas las pruebas.**

## 4.2. Ejemplo de informe del Red Team

```text
ATTACK 01 — Possible look-ahead contamination.
ATTACK 02 — 82 % of PnL produced between 2020-2021.
ATTACK 03 — Parameter optimum has no neighboring plateau.
ATTACK 04 — Strategy fails after 1.6× base transaction cost.
ATTACK 05 — Signal loses effect outside US large caps.
ATTACK 06 — Search-adjusted statistical evidence is weak.
```

Los valores anteriores son **ilustraciones**, no hallazgos reales de JAIME. Cada ataque verdadero debe citar experimentos, configuraciones y evidencias rastreables.

## 4.3. Portfolio Constructor y riesgo agregado

Una estrategia con Sharpe moderado, baja correlación y distinta exposición puede aportar más a una cartera que otra con Sharpe elevado y factores redundantes. Para varianza de cartera:

\[
\sigma_p = \sqrt{w^\top \Sigma w}
\]

La estimación debe mostrar supuestos sobre pesos, covarianza, ventana, cambios de régimen, concentración y colas. El manual previo de especialistas recoge este enfoque de riesgo `fileciteturn0file0`.

## 4.4. Estados de decisión del Strategy Chair

```text
REJECTED_DATA_QUALITY
REJECTED_LOOKAHEAD
REJECTED_OVERFIT
REJECTED_COSTS
REJECTED_FRAGILITY
REJECTED_CAPACITY
REJECTED_RISK
RESEARCH_ONLY
PROMOTE_TO_UNTOUCHED_OOS
PROMOTE_TO_INTERNAL_PAPER
PROMOTE_TO_BROKER_PAPER
PROMOTE_TO_SHADOW
LIVE_CANDIDATE
```

**`LIVE_CANDIDATE` no equivale a autorización de ejecución.** En el proyecto actual todo permanece **PAPER ONLY**. `PERFECT_STRATEGY` es un estado inválido.

---

# 5. Arquitectura para una eventual ejecución automatizada

La propuesta no es «conectar agentes al exchange». Se trata de que un **ejecutor aislado, pequeño, determinista y auditable** sea el único componente con capacidad técnica de remitir solicitudes a una API. Para JAIME actual esa capacidad no se habilita y el sistema no dispone de permiso operativo real.

```text
LLM / AGENTES         piensan, investigan, proponen hipótesis
       │
       ▼
STRATEGY ENGINE      transforma hipótesis validadas en señales
       │
       ▼
PORTFOLIO ENGINE     propone exposición y pesos
       │
       ▼
RISK ENGINE          acepta/rechaza mediante reglas externas al LLM
       │
       ▼
ORDER MANAGEMENT     prepara y contabiliza intents, si la fase lo permite
       │
       ▼
EXECUTION GATEWAY    único con acceso a credenciales, fase futura
       │
       ▼
BROKER               PAPER externo primero; LIVE fuera de alcance
```

La idea es **hacer menos libre, no más libre, la parte que pueda mover dinero**. Un LLM puede proponer, nunca poseer por sí mismo autoridad de ejecución.

## 5.1. Trade Intent — propuesta, NO orden

```json
{
  "intent_id": "TI-283010",
  "strategy_id": "STRAT-204",
  "instrument_id": "...",
  "direction": "LONG",
  "target_weight": 0.025,
  "reason_codes": ["QUALITY_SIGNAL", "MOMENTUM_CONFIRMATION"],
  "valid_until": "...",
  "model_version": "...",
  "evidence_snapshot": "...",
  "confidence_class": "..."
}
```

Lo anterior es un contrato ilustrativo. No contiene parámetros completos ni autorización operativa. El usuario debe poder entender **por qué** se propone la exposición, qué evidencia la soporta y cuándo deja de ser válida.

## 5.2. Portfolio Proposal

Consolidar propuestas individuales, conflictos y límites de estrategias antes de preparar ninguna orden:

```json
{
  "target_portfolio": {
    "A": 0.025,
    "B": 0.018,
    "C": 0.0
  }
}
```

Resolver cash, exposiciones solapadas, señal opuesta en distintos modelos, correlaciones, concentración, divisas y riesgos factoriales.

## 5.3. Risk Gate determinista — fuera del control del LLM

El motor independiente usa reglas predeterminadas, versionadas e imposibles de modificar libremente mediante conversación en runtime:

```text
max_position_weight
max_sector_weight
max_gross_exposure
max_net_exposure
max_order_notional
max_daily_turnover
max_daily_loss
max_portfolio_drawdown
max_strategy_allocation
max_correlation_cluster
min_liquidity
max_participation
stale_data_limit
price_deviation_limit
allowed_symbols
allowed_asset_classes
allowed_order_types
trading_hours
```

Si una falla, **REJECT**; no importa cuánto insista Chair o si el LLM describe una «oportunidad extraordinaria».

## 5.4. Order Intent — solo después de risk gate y fase autorizada

```json
{
  "order_intent_id": "...",
  "instrument": "...",
  "side": "BUY",
  "max_quantity": "...",
  "limit_constraints": {},
  "time_in_force": "...",
  "strategy_id": "...",
  "risk_check_hash": "..."
}
```

**No activar este flujo hacia mercado real.** El contrato es una referencia de diseño para una fase futura.

## 5.5. Order Management System (OMS)

La integración debe conocer el estado real y resistir duplicados:

```text
¿ya se envió esta orden?
¿es una petición repetida?
¿se ejecutó total o parcialmente?
¿la cancelación fue aceptada?
¿quedó una orden abierta?
¿hay fill desconocido o retrasado?
¿se reconcilian saldo y posición?
¿se reintentó sin certeza de resultado?
```

Se cita como ejemplo crítico la Public API de Trading 212: documentación del informe la caracteriza como beta y advierte que determinados endpoints de órdenes market/limit/stop-limit **no son idempotentes**. Reenviar puede generar órdenes duplicadas, de modo que el OMS debe poder manejar resultados inciertos y evitar reintentos ciegos. Referencias originales: `citeturn14search8turn14search9turn14search15`.

## 5.6. Execution Gateway y adaptadores

El gateway futuro sería el único lugar con acceso a secretos y una interfaz mínima:

```text
get_positions()
get_cash()
get_open_orders()
place_validated_order()
cancel_order()
replace_order()
reconcile()
emergency_cancel_all()
```

Interfaz conceptual intercambiable:

```text
BrokerAdapter
├── InternalPaperBroker
├── IBKRAdapter
└── CryptoExchangeAdapter
    ├── Binance
    └── Kraken
```

`IBKRAdapter` puede reservar dos modos estructurales `PAPER` y `LIVE`, **pero el modo LIVE debe permanecer inaccesible en JAIME actual**. El motor de investigación no puede depender de particularidades de IBKR. Cripto y valores negociables deben mantener reglas y costes apropiados a sus mercados.

## 5.7. Kill switch y fail-closed

Un **STOP ALL TRADING** independiente del LLM, y condiciones automáticas:

```text
broker disconnected          → halt
stale market data            → halt
position mismatch            → halt
unknown fill                 → halt
daily loss limit             → halt
risk engine unavailable      → halt
clock desynchronization      → halt
duplicate-order uncertainty  → halt
unexpected leverage          → halt
unrecognized security        → halt
```

La norma general es **ante incertidumbre se detiene**, nunca «Qwen improvisa». El informe menciona como ejemplo el *Dead Man's Switch* de Kraken Futures, mecanismo que cancela órdenes al faltar el refresco de heartbeat, `citeturn17search1`. Diseñar un watchdog propio incluso si la plataforma ofrece protección de este tipo.

## 5.8. Heartbeat, desconexiones y reinicios

```text
JAIME   → EXECUTOR : alive
EXECUTOR→ BROKER   : session OK
BROKER  → EXECUTOR : account state
EXECUTOR→ JAIME    : reconciled
```

Si falla cualquier eslabón, **no abrir posiciones nuevas**. La restricción real del usuario —portátil no disponible 24/7— impide tratar este diseño como un servicio continuo de operativa real. Un PC apagado **no vigila posiciones ni órdenes**; no simular que la API hace desaparecer ese riesgo.

## 5.9. Reconciliación con estado externo

En una futura integración, la fuente autoritativa de ejecución es el bróker:

```text
BROKER POSITION
BROKER CASH
BROKER OPEN ORDERS
BROKER FILLS
```

Comparar:

```text
expected_state
vs
broker_state
```

Si `expected AAPL = 10` y `broker AAPL = 11`, entrar en `RECONCILIATION_HALT`, no reparar a ciegas. Debe poder diagnosticar fills retrasados, parciales, cancelaciones pendientes, acciones corporativas y cambios de sesión.

## 5.10. Aislamiento de credenciales y permisos mínimos

```text
LLM process         → NO secrets
research process    → NO trading keys
risk process        → NO trading keys
execution gateway   → trading permission ONLY, fase futura
withdrawal          → NONE
```

Prohibido exponer contraseñas, private keys, API secret o session token al LLM, a prompts, logs, frontend, repositorio, IA conectada o terceros. No otorgar permiso de retiradas. Segregar entornos y validar credenciales, cuenta e identidad legal del proveedor antes de contemplar ejecución.

## 5.11. Human-in-the-loop

Empezar por:

```text
AGENT PROPOSES
     ↓
RISK ACCEPTS
     ↓
JAIME SHOWS
     ↓
HUMAN APPROVES
     ↓
ORDER (solo en futura fase aprobada)
```

El informe describe una iniciativa de IBKR de 2026 de *agentic trading* con revisión y aprobación humana, como referencia conceptual; esa afirmación **se debe verificar** antes de reproducirla como una capacidad operativa: `citeturn14search18`.

**API automatizable ≠ estrategia probada ≠ autorización para gestionar dinero.**

---

# 6. Comparativa de plataformas, APIs, ventajas y límites

Evaluación cualitativa del informe, **específica para JAIME**, no ranking universal. La disponibilidad por jurisdicción, fecha, nivel de cuenta, instrumento y tarifas debe revalidarse mediante documentación contractual oficial.

| Plataforma | Paper/API según el informe | Cobertura | Encaje con equity research | Automatización | Principal problema | Función recomendada |
|---|---|---|---|---|---|---|
| **Interactive Brokers** | Muy alta | Multiactivo, internacional | Muy alta | Alta | Complejidad operacional; datos RT potencialmente de pago | **Futuro bróker principal** |
| **Alpaca** | Muy alta | Buena, en evolución | Muy buena | Muy alta, API-first | Oferta/regulación para individuo residente en España por verificar | Plan B/prototipo |
| **Trading 212** | API demo/live; beta según informe | Orientado a inversión retail | Buena | Media | API beta; órdenes no idempotentes | No núcleo autónomo por defecto |
| **Binance** | Testnet y API spot/futuros según productos | Cripto | No sustituye fundamentales de equity | Alta | Alcance cripto y situación MiCA/entidad | Adaptador cripto opcional |
| **Kraken** | API sólida; demo histórico de futures afectado | Cripto | No sustituye fundamentales de equity | Alta | Entorno demo-futures retirado según informe | Adaptador cripto opcional |
| **JAIME InternalPaperBroker** | Lo construye JAIME | Depende de P2 | Control completo | Total para simulación | Modelo de fills/costes debe ser realista | **Simulador primario** |

## 6.1. Interactive Brokers — elección principal para el destino futuro

**Ventajas argumentadas:**

- Multiactivo en unos 170 mercados de 40 países según la investigación; acciones, ETF, opciones, futuros, divisas, bonos, fondos. Es la cobertura más coherente con un JAIME de investigación empresarial y cartera diversa, no sólo cripto. `citeturn13search1turn13search7`.
- Entidad IBKR Ireland Limited mencionada en registro CNMV número 5023, en prestación transfronteriza a España. Verificar ficha e instrumentos autorizados. `citeturn17search2turn17search14`.
- Infraestructura de APIs: Web API REST/HTTP/WebSocket, TWS API socket y alternativas institucionales, para automatización e integración. `citeturn14search18turn14search19`.
- Paper account con APIs similares a las reales. Potencial reutilización del contrato de órdenes y reconciliación. `citeturn14search1`.

**Cuatro inconvenientes críticos:**

1. **Paper ≠ mercado real.** *Top of book* en llenados simulados, profundidad y tipos de orden con limitaciones. No interpretar paper PnL como prueba definitiva de execution alpha. `citeturn14search1`.
2. **Operación local complicada.** TWS/IB Gateway, reinicios, sesiones, posible autenticación manual semanal, auto-restart. No es «instalar y olvidar» en portátil. `citeturn14search5turn14search11`.
3. **Market data no necesariamente gratis.** Acceso API a muchas cotizaciones en tiempo real requiere suscripción; según mercado/cuenta hay cotizaciones retrasadas —se cita ejemplo de ~15 minutos para algunas acciones de EE. UU. sin suscripción aplicable—. `citeturn19search7turn19search16turn19search18`.
4. **Más complejidad y mantenimiento** que soluciones API-first. Hay que gestionar instrumentos/contratos, status, rate limits, cambio de APIs, autenticación y conciliación.

**Conclusión:** preferirlo como **destino futuro** por su techo multiactivo, no por facilidad de integración. **No abrir/conectar cuenta ahora para implementar P5.**

## 6.2. Alpaca — alternativa API-first

Alpaca es la alternativa seria para prototipar por su diseño API-first (REST, SSE, WebSocket), paper/live y experiencia enfocada en desarrolladores. La investigación señala actividades europeas vía WealthKernel Spain AV, CNMV número 328, y cambios anunciados en octubre 2026 relativos a integración de paper trading con ChatGPT; ambos extremos **requieren verificación contextual y actual**. `citeturn13search18turn18search3turn13search11`.

**Razones para no darla por ganadora:** el usuario quiere mercados y activos diversos; la oferta europea, el despliegue de Xetra/Euronext/LSE, la relación con instituciones y partners y la disponibilidad real para **persona física residente en España** pueden diferir de la oferta en EE. UU. `citeturn13search16turn18search9turn18search0turn18search6`.

**Checklist de verificación Alpaca antes de usarla:**

```text
¿Cuenta individual para residente español realmente disponible?
¿Qué entidad legal y qué supervisión?
¿Acciones estadounidenses? ¿Acciones UE? ¿ETF?
¿PAPER sin cuenta live? ¿API paper? ¿API live?
¿Opciones? ¿Cripto? ¿Qué productos autorizados para España?
¿Qué tipos de orden? ¿Qué exchanges?
¿Qué condiciones de data y licencias?
¿Qué comisiones, FX, market data, custodia y actividad?
```

**Conclusión:** segunda elección global en el informe; potencial primera para prototipo API-first si la disponibilidad y coste resultan adecuados.

## 6.3. Trading 212 — no núcleo de ejecución autónomo por defecto

El informe indica API pública `v0` etiquetada **beta**, con entornos **demo** y **live**, acceso a instrumentos, posiciones y órdenes. La desventaja citada es ausencia de idempotencia en determinados endpoints de creación de órdenes: el reintento puede crear otra orden. `citeturn14search8turn14search21turn14search14turn14search9turn14search15`.

**No se concluye que sea mal bróker minorista.** Se concluye que, salvo necesidades propias del usuario, resulta menos apropiado para construir desde cero un OMS de ejecución autónoma frente a otras alternativas. Un OMS robusto puede manejar ese riesgo, pero no se debe subestimar.

## 6.4. Binance — brazo cripto separado, no JAIME completo

Spot REST/WebSocket y entornos Spot/Futures Testnet documentados según investigación; actualización del Spot Testnet citada en septiembre de 2026. Útil para BTC, ETH, momentum cripto, funding, basis y futuros si los instrumentos están permitidos y los datos son adecuados. `citeturn16search13turn16search17`.

**No reemplaza** investigación de compañías, fondos, acciones, bonos y mercados tradicionales. No reducir el proyecto a `JAIME = Binance bot`.

**España/UE y MiCA:** el informe señala fin del periodo transitorio español el **1 de julio de 2026**, registro ESMA de proveedores de servicios de criptoactivos autorizados y necesidad de identificar la **entidad jurídica concreta** que sirve a la cuenta del usuario y sus permisos; no basta con la marca comercial. Revalidar situación actual en ESMA/CNMV. `citeturn13search10turn17search4turn17search5turn17search6`.

## 6.5. Kraken — API cripto sólida; comprobar paper/sandbox

Kraken dispone de APIs y mecanismos relevantes de seguridad, incluido *Dead Man's Switch* en futures (según investigación). El antiguo entorno `demo-futures` habría sido retirado el **14 de julio de 2026**, por lo que no diseñar P6 suponiendo que ese sandbox sigue disponible. Verificar qué entornos, productos, endpoints y licencias existen para usuario español. `citeturn17search1turn16search0turn16search4`.

**Conclusión:** adaptador cripto opcional; no sustituto de IBKR para multiactivo; su trayectoria paper puede requerir simulador propio.

## 6.6. QuantConnect / LEAN — referencia arquitectónica, no dependencia automática

LEAN/QuantConnect dispone de herramientas avanzadas de backtesting, optimización y conectores live. La investigación advierte que determinadas funciones CLI paper/live y datasets pueden exigir **organización de pago o compras**, incompatible con «0 € adicionales» como requisito absoluto. `citeturn19search6turn19search13`.

**Decisión sugerida:** estudiar métodos y arquitectura pero mantener el núcleo del laboratorio **local, propio y portable** con Python + los datos de P2 + almacenamiento existente (SQLite/Parquet si justificado) + motores deterministas. No hacer depender una fase básica de SaaS de pago.

## 6.7. Valoración comparativa desde los requisitos de JAIME

La comparación debe verificar, antes de fijar un proveedor:

```text
jurisdicción: España/UE
licencia, entidad exacta y términos API
instrumentos disponibles: equity/ETF/bond/FX/options/futures/crypto
paper y sandbox reales
API oficial y soporte/documentación
coste de cuenta, negociación, FX, market data y custodia
persistencia/suscripción de datos y derechos de redistribución
latencia, rate limit, autenticación y reinicios
órdenes soportadas, fills y simulación
idempotencia/reintentos/estado final
separación PAPER/LIVE y permisos
reconciliación y kill switch
compatibilidad Windows 11 y RAM disponible
complejidad de mantenimiento para usuario no programador
continuidad con PC apagado y dependencia de nube
```

**No existe evidencia en el informe de que una sola oferta garantice simultáneamente API gratis, market data global profesional gratis, cobertura completa de clases de activos y ejecución real sin costes desde España.** Coste de acceso no es igual a coste total. El requisito 0 € obliga a degradar o posponer funcionalidades que requieran pago.

---
# 7. Ampliación del alcance de P5, P6 y P7; propuesta futura P8

El informe recomienda **revisar el diseño de las fases futuras antes de implementarlas**, para no dejar P5 como un backtester superficial ni confundir P6 con operar ficticiamente una cuenta de 10.000 €. **Esta propuesta no autoriza la apertura técnica de ninguna fase.**

## 7.1. P5 — Strategy Research & Adversarial Validation Lab

**Misión:** registrar ideas, formalizarlas, experimentar con control, falsar señales, medir la robustez y aceptar/rechazar estrategias con evidencia reproducible. Requerimientos esenciales:

1. **Strategy Registry:** hipótesis, versiones, relaciones parent/child, parámetros y todas las variantes generadas.
2. **Backtest Engine:** Python determinista, point-in-time, universo correcto, decisiones y fills coherentes con calendario, cash y corporate actions.
3. **Adversarial Validation Engine:** sesgos, contaminación, costes, parámetros, regímenes, pruebas múltiples, DSR/PSR/PBO cuando aplicables, stress y riesgos económicos.
4. **Strategy Graveyard:** registro duradero y explicable de todos los fracasos, no solo ganadores.
5. **Decision gates:** primero datos y plausibilidad; después resultados; después OOS sellado; después autorización futura para pasar a simulación prospectiva.
6. **Risk / Portfolio Engine:** papel real de concentraciones, dependencia factorial, covarianzas y coherencia global entre estrategias.
7. **LLM role orchestration:** Qwen formula/examina hipótesis y evidencia compacta, no realiza operaciones matemáticas masivas ni ve gigantescos historiales en texto.

**Por qué:** literatura sobre PBO, DSR y *data snooping* demuestra la importancia de contabilizar intentos y controlar selección. Las citas originales aparecen en el apartado 2 y en `citeturn15search0turn15search1turn15search6`.

### Interfaz de salida analítica esperada

Un informe de familia puede dar al LLM únicamente resultados compactos, calculados por Python, por ejemplo:

```json
{
  "family": "quality_momentum",
  "experiments": 632,
  "survivors_initial": 48,
  "survivors_cost_stress": 17,
  "survivors_parameter_stability": 9,
  "survivors_search_adjusted": 4,
  "survivors_oos": 2,
  "dominant_failure_modes": ["...", "..."]
}
```

Estos valores son **hipotéticos para mostrar el formato**, no resultados comprobados. El LLM puede explicar qué se ha aprendido, pero no reescribir el conteo de supervivientes ni falsificar indicadores.

## 7.2. P6 — Forward Testing & Execution Lab

**No reducirlo a un saldo ficticio de 10.000 €.** La cuenta MASTER de JAIME actual es una restricción vigente y debe preservarse. P6 propuesta incorpora **tres capas sucesivas**:

### Capa A. Simulación interna reproducible

`InternalPaperBroker` con:

```text
fills
slippage
partial fills
fees
latency assumptions
market impact approximations
cash and settlement
corporate actions
position ledger
trade audit
```

Su función es proporcionar un simulador determinista, auditable y configurable, no prometer que replica exactamente la liquidez de cada mercado. Debe integrarse sin alterar posiciones MASTER existentes ni saldos salvo conforme a las puertas vigentes.

### Capa B. Paper del bróker — preferencia IBKR PAPER futura

Comprobar mediante la cuenta adecuada y documentación verificada:

```text
login/authentication
session lifetime
instrument resolution
order submission in PAPER
rejections and errors
fills and partial fills
cancellations
positions
cash
reconciliation
disconnect/restart behavior
idempotency and retry
```

El informe afirma que IBKR ofrece APIs operables con PAPER, con límites de simulación `citeturn14search1turn14search3`. **No confundir acceso paper técnico con permiso actual de JAIME para enviar órdenes**; P6 no está habilitada.

### Capa C. Shadow trading

JAIME prepara propuestas «habría comprado X / habría vendido Y» **sin enviar órdenes**, y luego analiza:

```text
observed price
available spread (if sourced)
hypothetical fill validity
estimated slippage
portfolio drift
order constraints
market hours
```

Distinguir *shadow* de una afirmación de ejecución: sin nivel suficiente de datos, no se conoce el fill real contrafactual. El valor principal es probar la hipótesis hacia adelante, **después de congelarla**, reduciendo el sesgo retrospectivo.

## 7.3. P7 — QA de ingeniería y fallos operativos

Ampliar el QA global para cubrir al menos las siguientes incidencias:

```text
network loss
broker API down
stale prices
duplicate events
out-of-order fills
process crash
Windows restart
LLM crash
database unavailable
clock drift
partial fill
cancel rejected
order rejected
market closed
corporate action
unexpected position
cash mismatch
API schema change
```

Verificar pruebas de no órdenes en los entornos que las prohíben, reconexión segura, sistemas fail-closed, logs no secretos, idempotencia, conciliación y ausencia de operaciones implícitas durante reinicios. Las APIs son dependencias vivas: el informe cita por ejemplo cambios de TWS API en agosto de 2026, cuyo detalle debe verificarse en *changelog* oficial `citeturn14search0turn14search17`.

## 7.4. P8 — Controlled Live Execution: fase separada, no autorizada

**P8 es una propuesta conceptual para otro momento. No debe existir un cambio `LIVE = true` que convierta P6 en ejecución real.** Secuencia de gobernanza futura:

```text
READ ONLY
    ↓
SHADOW
    ↓
ORDER PROPOSAL + HUMAN APPROVAL
    ↓
revisión explícita de idoneidad de estrategia y seguridad
    ↓
consideración separada de mayor automatización
```

Una eventual integración requiere autorización expresa del usuario, evaluación de riesgos reales, contrato/condiciones del bróker, regulación aplicable, recursos para continuidad, credenciales segregadas, límites cuantificados, monitorización independiente y mecanismos de apagado. **No fijar umbrales arbitrarios** como «100 operaciones», «3 meses» o «Sharpe 2» para habilitar LIVE: dependen de frecuencia, universo, duración, dependencia temporal, costes y propiedades estadísticas. La literatura PSR/DSR citada advierte sobre representatividad de muestra `citeturn15search15`.

---

# 8. P2 es una dependencia esencial, no opcional

P5 no podrá realizar investigación fiable multicompañía solo porque P2 descargue BTC y una serie macro. Para estrategias fundamentales y carteras históricas, P2 necesitará, con licencias apropiadas:

| Área | Requisito para el laboratorio |
|---|---|
| Entity master | Empresa, valor, listing, ticker, CIK/LEI/ISIN si procede, bolsa, divisa |
| Quotes/prices | Raw/adjusted, observación, frecuencia, mercado, derechos y metadatos |
| Corporate actions | Splits, dividendos, fusiones, spin-offs, delistings, cambios de ticker |
| Financial statements | US GAAP/IFRS, periodo fiscal, fecha de publicación y revisiones |
| Fundamentals | Ingresos, EBIT, FCF, ROIC, leverage, valoraciones y definiciones consistentes |
| Segments | Distribuciones por negocio, regiones, costes, activos cuando se publiquen |
| Shares/dilution | Acciones básicas/diluidas, recompras, emisiones, SBC, convertibles |
| Credit/FX/rates | Vencimientos, tipos y moneda, observación válida en la fecha |
| Indices/universe | Composición histórica, altas/bajas, delisted, sesgo de supervivencia |
| Market frictions | Comisiones, spreads, volumen/liquidez cuando estén disponibles |
| Publication clocks | `period_end`, `published_at`, `available_to_strategy_at`, `restated_at` |
| Evidence/rights | Fuente, URL/ID, almacenamiento permitido, límites de redistribución |
| Quality | Missing, anomaly, stale, confidence del dato, no asimilar NA a 0 |

Cada fuente debe poder indicar:

```text
AS_OF
OBSERVED_AT
PUBLISHED_AT
AVAILABLE_AT
INGESTED_AT
REVISED_AT
LICENSE_SCOPE
DATA_QUALITY
```

**Backtest temporalmente coherente exige comparar lo que era conocible en la fecha**, no usar una revisión futura. **Survivorship bias** exige universo histórico reconstruido, no lista de supervivientes actuales. Sin estas garantías, marcar el resultado `RESEARCH_ONLY`; no promocionar a P6.

Los precios y datos retrasados de terceros pueden ser útiles para prototipos, pero no deben convertirse silenciosamente en series de alta frecuencia o feeds gratuitos profesionales para toda clase de activos. No inferir licencia de persistencia/distribución por el mero hecho de que un endpoint responda.

---

# 9. Encaje con la máquina local y el presupuesto 0 €

**Restricciones actuales conocidas del proyecto:** Windows 11, Intel Core 5 120U, 16 GB RAM, integrada, PC no disponible permanentemente, un LLM Qwen pequeño mediante llama.cpp, 30 roles lógicos y coste nuevo 0 €. Esta especificación debe verificarse contra `AGENTS.md`/`STATUS.md` del repositorio actual antes de implementación.

**Compatible conceptualmente:**

- LLM secuencial propone un grupo pequeño de hipótesis.
- Python/NumPy/pandas/Polars u otras bibliotecas justificadas realizan muchas pruebas por lotes, sin mantener 30 modelos de IA.
- SQLite/almacenamiento ya existente y, si justificado, Parquet para snapshots y arrays grandes, con presupuesto de disco/RAM.
- Mantener un `experiment registry` y cachear datos y cálculos inmutables.
- Enviar al LLM **resúmenes compactos, métricas deterministas, anomalías, contraejemplos y evidencias**, no decenas de miles de filas de retorno.
- Medir tiempos, memoria, CPU, temperatura/estabilidad y número de experimentos por lote antes de diseñar una factoría masiva.

**No compatible o no demostrado bajo esas restricciones:**

- 30 LLM funcionando en paralelo.
- Miles de backtests de alta frecuencia sobre libro de órdenes completo sin infraestructura ni datos apropiados.
- Interpretación de «0 €» como acceso universal a todo mercado y market data profesional en tiempo real.
- Operativa real 24/7 segura con el único portátil apagable.
- Cualquier expectativa de beneficios garantizados o decisiones financieras infalibles.

«Minar cientos de estrategias» es técnicamente plausible para hipótesis acotadas y datasets adecuados **de forma secuencial**. La cifra depende de universo, longitud histórica, granularidad y complejidad; no prometer rendimiento de hardware sin benchmark local.

---

# 10. Orquestación completa en el ecosistema JAIME

El laboratorio no sustituye el análisis fundamental; ambos deben integrarse en el proceso de inversión:

```text
                     JAIME INVESTOR HQ
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
ANÁLISIS FUNDAMENTAL               RESEARCH CUANTITATIVO
30 especialistas secuenciales       fábrica de estrategias
         │                                   │
         ▼                                   ▼
 tesis económica                     cientos/miles de tests
         │                                   │
         ▼                                   ▼
Bull / Bear / Chair                 Red Team Quant
         │                                   │
         └─────────────────┬─────────────────┘
                           │
                           ▼
                    PORTFOLIO ENGINE
                           │
                           ▼
                     RISK DIRECTOR
                     reglas rígidas
                           │
                           ▼
                      PAPER ONLY
                           │
                 forward test prolongado
                           │
                           ▼
                      SHADOW MODE
                           │
                           ▼
                HUMAN APPROVAL (FUTURO)
                           │
                           ▼
                IBKR EXECUTION (FUTURO)
                           │
                           ▼
           EVENTUAL AUTOMATION (NO AUTORIZADA)
```

Y el flujo de componentes detallado:

```text
┌─────────────────────────────────────────────────────────┐
│                    JAIME INVESTOR HQ                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                    P2 DATA PLATFORM
                point-in-time / provenance
                          │
                          ▼
                 RESEARCH SPECIALISTS
                     hypotheses only
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    STRATEGY FACTORY                     │
│ hypothesis | formalizer | generator | experiment registry│
└─────────────────────────┬───────────────────────────────┘
                          ▼
                 BACKTEST ENGINE PYTHON
                          │
                          ▼
              ADVERSARIAL VALIDATION LAB
          contamination / frictions / regimes
      parameter robustness / PSR / DSR / PBO / stress
                          │
             ┌────────────┴──────────────┐
             ▼                           ▼
     STRATEGY GRAVEYARD              SURVIVOR
                                         │
                                         ▼
                                    UNTOUCHED OOS
                                         │
                                         ▼
                                INTERNAL PAPER BROKER
                                         │
                                         ▼
                                    IBKR PAPER
                                         │
                                         ▼
                                  SHADOW TRADING
                                         │
                                         ▼
                               PORTFOLIO CONSTRUCTOR
                                         │
                                         ▼
                                 DETERMINISTIC RISK
                                         │
                                         ▼
                                     TRADE INTENT
                                         │
                                         ▼
                                        OMS
                                         │
                                         ▼
                                 HUMAN GATE (FUTURO)
                                         │
                                         ▼
                               IBKR ADAPTER (FUTURO)
                                         │
                                         ▼
                         LIVE ACCOUNT — NOT AUTHORIZED
```

**Idea central:** la institución debe generar ideas, recordar experimentos, eliminar las falsas, intentar destruir las supervivientes, aprender de fracasos, investigar compañías, controlar exposición independientemente y no permitir que un LLM eluda gates. **El bróker es un periférico intercambiable; no el cerebro**.

---

# 11. Criterios de aceptación y evaluación que debería pedir Codex

Esta tabla traduce la investigación a **objetivos para una futura planificación**, sin autorizar cambios actuales.

| Área | Prueba mínima propuesta | Fallo bloqueante |
|---|---|---|
| Datos | Reconstrucción `as-of` de fundamentales y calendario | Futuros vistos / fuente sin fecha |
| Universo | Delisted y miembros históricos representables | Survivorship sin advertencia |
| Corporate actions | Casos split/dividend/fusión reproducibles | Precio ajustado mal interpretado |
| LLM | Rol formula hipótesis; cálculos deterministic Python | Números inventados/ejecución de código arbitrario |
| Registry | Registra ganadores y perdedores, variantes y semillas | Selección sin número de trials |
| Backtest | Correcto a mano en caso sintético conocido | Fill imposible, retorno inconsistente |
| Fees | Prueba con comisiones/spread/slippage | `NO_DATA → 0` por defecto |
| OOS | Holdout bloqueado y genealogía visible | Reusar test tras tuning como virgen |
| Robustez | Sensibilidad local, costes 1/1,5/2× | Pico aislado disfrazado de robustez |
| Estadística | PSR/DSR/PBO calculados solo si aplicables y auditables | Porcentajes sin muestra ni método |
| Portfolio | Risk aggregation y concentración reproducibles | Confundir gran Sharpe con bajo riesgo |
| Paper | Ledger y saldos conciliados | Posiciones/caja inconsistentes |
| OMS futura | Idempotencia y parciales simulados | Órdenes duplicadas o inciertas sin halt |
| Fail closed | Caída de datos/broker detiene nuevas órdenes | LLM sortea kill switch |
| Seguridad | Sin API secrets en prompts/logs/código | Exposición de credenciales |
| Estado actual | P5/P6 sin activación, PAPER ONLY, `/api/orders=403` | Se habilitan órdenes o LIVE |

### Escenarios adversariales que no deben omitirse

```text
1. Datos deliberadamente corregidos después de la fecha de backtest.
2. Titular publicado horas después de la supuesta señal.
3. Split 10:1 que aparentaría crash sin ajuste.
4. Empresa que quiebra o deja de cotizar.
5. Sharpe excelente en una sola compañía/año.
6. Pico exacto en un parámetro; vecinos malos.
7. Rendimiento se evapora al duplicar comisiones.
8. Coste o spread ausente; no sustituir por 0.
9. Optimización repetida sobre holdout ya observado.
10. LLM afirma una trayectoria contradictoria con cálculos.
11. Señales duplicadas y orden/reintento duplicado.
12. Partial fill, cancel pending, estado incierto.
13. Caída Windows o internet durante simulación/paper.
14. Broker positions ≠ ledger interno.
15. Reloj desincronizado y precio antiguo.
16. Universo actual usado retroactivamente.
17. 1000 variantes altamente correlacionadas presentadas como independencia.
18. API externa cambia el esquema.
19. LLM insiste en operar pese al veto del motor de riesgo.
20. Falsa equivalencia entre PAPER fill y ejecución live.
```

**El dato de una prueba previa mencionado en la investigación:** un modelo local llegó a describir una serie de Bitcoin como subida diaria continua, a pesar de que los cálculos identificaban **22 días alcistas y 20 bajistas**. Esto es un ejemplo de por qué `JSON válido ≠ análisis semánticamente correcto` y de por qué el LLM jamás debe ser juez único de posiciones/riesgo. Verificar la reproducción de esa prueba en el repositorio; el informe no incluye artefacto ejecutable de aquella ejecución.

---

# 12. Recomendación final y decisiones pendientes

## 12.1. Elección de plataformas

- **Elección futura recomendada:** Interactive Brokers, por cobertura multiactivo, mercados, APIs y PAPER potencialmente reutilizable. No exige conectarlo hoy. Validar costes, permisos, disponibilidad real, sesión y condiciones España antes de tomar una decisión contractual. `citeturn13search1turn17search2turn14search18turn14search1`.
- **Plan B serio:** Alpaca, especialmente para prototipo API-first si se demuestra disponibilidad de cuenta individual española, activos y condiciones. `citeturn13search11turn13search18turn18search0turn18search6`.
- **No preferida como núcleo autónomo:** Trading 212 por estado beta y condiciones de endpoints documentadas en el informe; no se descarta como bróker para inversión personal. `citeturn14search8turn14search14`.
- **Solo módulo cripto:** Binance/Kraken, sujeto a datos, testnets en vigor, productos y situación ESMA/CNMV de la entidad concreta desde España. `citeturn13search10turn17search4`.
- **Laboratorio central:** motor local propio Python/P2/registrador de experimentos y validadores, no dependiente de ningún bróker. Estudiar LEAN/QuantConnect sin adoptar costes no autorizados. `citeturn19search6turn19search13`.

## 12.2. Política de ejecución

**Ahora:** investigación, revisión, documentación y los módulos que ya estén expresamente habilitados. **PAPER ONLY**; sin órdenes reales ni activar rutas bloqueadas. No conceder capacidad directa de orden al LLM ni a outputs textuales de Bull/Bear/Chair.

**Futuro condicionado:** P5 (fábrica de estrategias validada) → P6 (paper interno, paper externo, shadow) → P7 (ingeniería de fallos) → nueva fase P8 separada y autorizada para estudiar ejecución con dinero. No existe atajo de P6 a LIVE por cambio de configuración.

**Punto clave:** «No quiero que los agentes se conecten directamente a mi exchange y operen». Quiero que una infraestructura separada y auditable traduzca señales aprobadas a acciones controladas, si algún día existe autorización y una base de validación suficiente.

---

# 13. Encargo recomendado a Codex: auditoría de diseño ANTES de escribir código

> **No confundir este documento con autorización.** Especificación objetivo para revisar la viabilidad del roadmap.

Codex debe:

1. **Leer completo** el presente Markdown, `AGENTS.md`, `STATUS.md`, contratos de P2/P4, estado del MASTER y bloqueos vigentes; inspeccionar la arquitectura real antes de proponer cambios.
2. Producir una **matriz de correspondencia** entre los 30 roles que ya existen y las funciones de Strategy Researcher, Formalizer, Experiment Designer, Quant/Red Team, Risk, Portfolio y Chair. Conservar IDs y no crear treinta inferencias simultáneas.
3. Identificar requisitos disponibles/faltantes en **P2**, especialmente entidades, fundamentales, fechas de disponibilidad, corporate actions, universos históricos, licencia y modelos de costes. Marcar metodologías que no pueden validarse aún.
4. Definir **arquitectura técnica modular** de P5: strategy DSL, generador tipado, registry, hashes/snapshots, motor determinista, validación estadística/adversarial y Strategy Graveyard; especificar formatos y dependencias sin ejecutarlas todavía.
5. Diseñar **gates** y tests reproducibles, incluidos look-ahead, survivorship, costes, OOS sellado, búsqueda múltiple, PBO/DSR condicionados, sensibilidad a parámetros y simulación de fallos.
6. Proponer **P6** con `InternalPaperBroker`, IBKR PAPER como candidato futuro y shadow, sin entrar en LIVE y sin romper el MASTER.
7. Definir fronteras de seguridad del **Risk Gate, OMS, Gateway y kill switch**, incluyendo exclusión total de credenciales de LLM y frontend, prueba de idempotencia y reconciliación.
8. Comprobar documentación oficial y condiciones actuales de Interactive Brokers, Alpaca, Trading 212, Binance y Kraken: requisitos España/UE, API, paper, datos, coste, permisos y rate limits. Convertir marcadores de cita internos en fuentes oficiales con URLs verificadas; si no puede, dejar `PENDIENTE_VERIFICACIÓN`.
9. Diseñar un **plan incremental**, con riesgos, criterios de aceptación, recursos RAM/CPU/almacenamiento, comprobación coste 0 € y puertas de autorización por fase.
10. Entregar un **informe de gap analysis + especificación + plan priorizado**, separando aquello que puede hacerse desde ya en documentación de aquello que requeriría permiso del usuario.

### Prohibiciones explícitas para el primer encargo

```text
NO empezar P5 ni P6 sin nueva autorización.
NO modificar rutas de órdenes ni desactivar /api/orders=403.
NO añadir credenciales ni enlazar cuenta IBKR real.
NO crear, enviar o simular externamente órdenes sin la puerta vigente.
NO cambiar saldo inicial/patrimonio MASTER (10.000 € ficticios).
NO desplegar infraestructura de pago o contratar datos.
NO sustituir los 30 role_id del proyecto por una taxonomía inventada.
NO afirmar que PAPER demuestra rentabilidad live.
NO cambiar P2/P4 silenciosamente para adaptarlos al documento.
NO presentar como verificadas citas opacas de Investigación avanzada.
```

---

# 14. Trazabilidad del informe y bibliografía que necesita verificarse

La investigación original incluía referencias en forma de identificadores de búsqueda de ChatGPT; el archivo importado conserva las marcas relevantes en sus apartados. **Estas referencias no son enlaces permanentes ni aportan por sí mismas las URLs de las fuentes.** Se debe consultar el informe original si se quieren recuperar citas navegables; en el repositorio se deben incorporar fuentes primarias con enlaces y fechas de consulta.

## 14.1. Fuentes que debe recuperar Codex

| Asunto | Fuente primaria/documentación a buscar y verificar |
|---|---|
| IBKR mercados, productos y cobertura | Página oficial de productos/mercados de Interactive Brokers |
| IBKR España y entidad regulada | Registro oficial CNMV — Interactive Brokers Ireland Limited; documento de entidad contractual |
| IBKR TWS/Web APIs | Documentación oficial IBKR API (Web API, TWS API, Gateway), changelogs y condiciones |
| IBKR PAPER y limitaciones de fills | Guía oficial IBKR Paper Trading Account y API |
| IBKR market data y precio | Documentación oficial de suscripciones, delayed quotes y acceso API |
| Alpaca disponibilidad internacional | Páginas oficiales de eligibility, account opening, brokerage API, restricciones por jurisdicción |
| Alpaca Europe/WealthKernel Spain | Registros CNMV y documentación jurídica de servicio y entidad |
| Trading 212 Public API | Documentación oficial, estado beta, idempotencia, demo/live y rate limits |
| Binance API/Testnet | Documentación oficial Binance Spot/Futures y condiciones de testnet |
| Kraken API/Demo | Documentación Kraken Spot/Futures y anuncio de retirada demo-futures |
| MiCA España/UE | Comunicados y registros actuales CNMV/ESMA de CASPs autorizados |
| QuantConnect/LEAN | Documentación oficial local/CLI/cloud, condiciones de pago y datos |
| PBO/CSCV | Bailey, Borwein, López de Prado, Zhu: publicaciones originales y limitaciones |
| Deflated/Probabilistic Sharpe | Publicaciones originales de Bailey/López de Prado y autores pertinentes |
| Data snooping/White Reality Check/SPA | White y Hansen, artículos académicos originales |
| Seguridad y términos de trading algorítmico | Condiciones oficiales del bróker, normativa aplicable sin trasladar automáticamente reglas institucionales a retail |

## 14.2. Advertencias sobre el carácter del informe

- La **valoración comparativa** es una recomendación de diseño, no comprobación de apertura de cuenta española por ese usuario.
- Ningún resultado de rentabilidad, éxito de estrategias o número de supervivientes está medido en JAIME por el mero hecho de aparecer como ejemplo.
- Los esquemas YAML/JSON son **contratos conceptuales**, no archivos ejecutables verificados.
- La lista de métodos estadísticos no autoriza a calcularlos cuando no se cumplen supuestos de muestra, dependencia, diseño temporal o disponibilidad de datos.
- Los ejemplos de tipos de órdenes y API no autorizan romper el bloqueo PAPER actual.
- Un software de backtest «sin licencia de pago» no equivale a un conjunto completo de **datos financieros legalmente utilizables y gratuitos**.
- La plataforma óptima puede variar con requisitos nuevos y con las condiciones vigentes de brokers/exchanges.

---

# 15. Síntesis de decisión para la carpeta `docs/`

**Qué significa este documento en JAIME INVESTOR HQ:**

1. **P5 futuro:** desarrollar un laboratorio científico de estrategias con registro exhaustivo de variantes, falsación, datos point-in-time y controles de sobreajuste.
2. **P6 futuro:** construir simulación robusta, luego considerar paper externo y shadow, nunca confundirlo con live.
3. **IBKR:** bróker principal **candidato futuro** para multiactivo; independencia estructural mediante `BrokerAdapter`. Alpaca plan B; Binance/Kraken módulos cripto si procede.
4. **Riesgo:** determinista, capaz de vetar al LLM, independiente de narrativa y de la ejecución.
5. **Seguridad:** ningún secreto/orden directa al LLM, conciliación autoritativa del bróker, apagado de emergencia, fail-closed.
6. **Recursos:** un LLM local secuencial y Python por lotes, 16 GB RAM, sin asumir market data de pago ni PC 24/7.
7. **Ahora:** pedir a Codex **auditoría y plan**; mantener MASTER 10.000 € ficticios, P2/P4 y `/api/orders=403`, no activar P5/P6 ni P8.

**Principio final del informe:**

> El objetivo no es que una IA «opere por mí» sin controles. Es construir una organización de inversión que genere hipótesis, recuerde todos los experimentos, descarte falsos positivos, ataque sus supervivientes, analice compañías rigurosamente y solo permita operar después de superar controles verificables que el propio LLM no pueda eludir.
