# Agentes — 16 NPC visuales y 30 roles IA lógicos

**Fuente vinculante P4:** `docs/PLAN_P4_AGENTES_RESEARCH_LOCAL_AI.md`. Los NPC P1 son representación visual; los estados IA deben proceder de jobs reales.

## 16 NPC visuales

| Sala | NPC | Principales |
|---|---:|---:|
| Recepción | 1 | 1 |
| Trading | 3 | 1 |
| Research | 3 | 1 |
| Quant | 2 | 1 |
| Riesgos | 2 | 1 |
| Ejecución | 1 | 1 |
| Comité | 1 | 1 |
| Performance | 1 | 1 |
| Sistemas | 2 | 1 |
| **Total** | **16** | **9** |

## 30 roles IA P4

| Equipo | Especialidades | Total |
|---|---|---:|
| Research | Fundamental Equity, Valuation, Macro Global, Macro Europa/España, Crédito/Renta Fija, ESG/Regulación | 6 |
| Trading & Execution | Market Structure, Liquidity/Slippage, Execution Planning PAPER, Paper Operations/Reconciliation | 4 |
| Quant | Momentum/Trend, Value/Quality, Mean Reversion, Volatility/Regime, Portfolio Optimization | 5 |
| Risk | Market Risk, Credit/Counterparty, Liquidity Risk, Concentration, Compliance/Kill-Switch | 5 |
| Performance | NAV/Attribution, Benchmark/FX, Reporting/Postmortem | 3 |
| Systems & Data | Data Quality, Provider Orchestration, News/Social Intelligence, Observability/Security | 4 |
| Committee | CIO/Chair, Bull Advocate, Bear/Skeptic | 3 |
| **Total** | | **30** |

Los 30 roles existen como identidades, contratos y permisos, **no como 30 modelos**. Configuración por defecto: 1 inferencia LLM local, 2 jobs quant CPU y 4 fetches ligeros. El scheduler es persistente, on-demand y con deny-by-default.

## Pipeline inicial
Activar 6–10 roles por caso, no todos siempre. Base recomendada: Data Quality → Fundamental → Valuation → Macro → Momentum/Trend → Volatility/Regime → Bull → Bear/Skeptic → CIO/Chair. Crédito, ESG, liquidez, atribución, etc. entran por clase de activo/contexto.

Los roles Risk de P4 son **advisory**; el motor determinista y veto formal pertenecen a P5. Los roles Execution de P4 solo analizan microestructura/plan PAPER conceptual; P6 será la única fase que podrá generar ejecución simulada.

## Contrato común
Cada job guarda role/version, inputs, tools autorizadas, model/runtime si aplica, timestamps, hashes, evidence IDs, status y output versionado. Estados mínimos: `IDLE`, `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`, `BLOCKED`, `NO_LOCAL_MODEL`.

Claims numéricos sin evidencia se rechazan o marcan `UNVERIFIED`. Contenido externo es `UNTRUSTED_CONTENT`. Ningún agente puede mutar MASTER, ledger, cash, positions, NAV, orders o fills.

## Terceros
Vibe-Trading solo tras auditoría del subset; sin broker tools ni código generado no confiable. Agent Reach solo público/read-only y sin cookies/cuentas personales. Liquid OAuth read+trade continúa prohibido.
