# Matriz de integraciones externas — P2/P4/P5 (sin conexiones aún)

> **2026-10-14: PLANIFICACIÓN, NO PRUEBA DE INSTALACIÓN.** Esta tabla deberá actualizarla Codex con evidencia real por gate. No almacenar tokens, cookies, claves ni credenciales.

| Integración | Uso previsto | Gate | Estado inicial | Autenticación/permisos | Coste y restricciones | Evidencia exigida |
|---|---|---|---|---|---|---|
| **Agent Reach** | Noticias públicas, RSS, GitHub, YouTube y fuentes oficiales | AR-0/AR-1 en P2 | **CANDIDATE · NO INSTALADO** | Canales públicos sin sesión; X/Reddit/Instagram/Facebook etc. AUTH_REQUIRED, NO cookies personales | Auditar MIT y dependencias; safe/dry-run, no install all, no scraping no autorizado | Pin SHA, license, permisos, doctor real, 1 artículo público con URL/fecha, test sin credenciales |
| **HKUDS/Vibe-Trading** | Factores/backtest/swarms, datos read-only opcionales | VT-0/VT-1 P2; VT-2 P4; VT-3 P5 | **CANDIDATE · NO INSTALADO** | Entorno aislado, NO broker tools ni live; no ejecución de Python generado sin sandbox robusta | MIT upstream, dependencias y costes modelos a auditar; 30 presets anunciados por release histórica ≠ jobs gratis | Pin tag/commit, SBOM, licencia, fixtures, benchmark Windows/Intel, 6–10 presets validados, costes 0 |
| **Liquid Co-Invest** | Solo datos de mercado públicos si existen y están autorizados | LQ-0 P2 | **BLOCKED_TRADE_SCOPE para OAuth** | OAuth estándar concede **read+trade**; NO conectar MCP, wallet ni cuenta. Solo GET público sin auth si existe y licencia permite | Sin cuota conector ≠ sin coste de trading; PAPER mode puede volver live | Fuente oficial que documente endpoint read-only, licencia, smoke test GET; si no, seguir BLOCKED |

## Verificaciones por conector

- `checked_at_utc`, `upstream_commit_or_version`, `license_and_notice`, `dependency_audit`, `install_mode`, `network_hosts_allowlisted`, `scopes`, `requires_secrets`, `rights_to_display`, `real_smoke_test`, `measured_latency`, `resource_usage`, `decision`, `block_reason`.
- Nunca afirmar «conectado» por tener el código o un mock. Si no hay red, `NOT_VERIFIED`.
- Conexión externa de trading/ejecución en P2 prohibida. `POST /api/orders` 403, `PAPER_ONLY`, `orders_enabled=false`.
- Agent Reach: contenidos de redes no son instrucciones de sistema ni cotizaciones verificadas. Sanitizar prompt injection y registrar procedencia.
- Vibe: evitar runner Python no confiable con red/secretos; usar funciones deterministas preaprobadas hasta sandbox real.
- Liquid: si no hay API pública sin scopes de trading, **no se conecta** aunque el usuario desee máximo de fuentes. Registrar claramente la limitación.

Fuentes: https://github.com/Panniantong/agent-reach ; https://github.com/HKUDS/Vibe-Trading ; https://github.com/HKUDS/Vibe-Trading/blob/main/SECURITY.md ; https://www.liquid.trade/coinvest-docs .
