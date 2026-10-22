# Integraciones externas: evaluación real P2, 2026-10-15

**Actualización P4 avanzado, 2026-10-19:** la tabla siguiente conserva la auditoría P2. HQ ya tiene treinta roles operativos y scheduler persistente (no el runtime Vibe); el catálogo declarativo P2 sigue separado. Se ha reutilizado A20 en el caso BCE de research. Liquid continúa con scopes read+trade según su documentación oficial revisada; no conectado. Los factores Vibe STREV/HIGH52W inspeccionados necesitan cierres diarios/panel transversal no disponibles y no se presentan como ejecutados. [Matriz y límites actualizados](P4_AVANZADO_VALIDACION.md#integraciones-read-only).

No se conectaron cuentas, wallets, OAuth ni modelos de pago. Los entornos `.venv-agent-reach` y `.venv-vibe` están aislados e ignorados por Git. Evidencias/SBOM: [integraciones](evidencias/P2/integraciones/); licencias originales, notices, pins y hashes: `assets/integrations/`.

| Integración | Pin / licencia | Comprobación ejecutada | Decisión y límite |
|---|---|---|---|
| Agent Reach 1.5.0 | `94f06c1969dfc1834001269d79d3ad0972d9dee6` · MIT | CLI safe/dry-run, safe y doctor restringidos a RSS, 1/1; sin red, instalaciones globales, cookies ni configuración personal. Feedparser presente. | Canal RSS auditado. La conexión real A20 es RSS oficial BCE mediante el cliente seguro común HQ: cinco noticias con URL/fecha. No se cuentan otros canales ni Agent Reach como proveedor adicional. |
| Vibe-Trading 0.1.16 | `d7f1b9e22b42c10197497a8e2cac4f0e2cc9ca1e` · MIT; NOTICE conservado | Inspección estática del árbol fijado y parseo seguro de **30 YAML**, con SHA-256, nombre, roles y herramientas. Benchmark de 1.000 parseos guardado. Solo PyYAML instalado en evaluación. | **METADATA_ONLY**, 30 presets desactivados. Contrato tipado read-only y reserva de 30 roles HQ. Sin runtime, inferencia, estrategia, backtest ni benchmark quant. No se validaron 6–10 equipos operativos: pendiente P4/P5 y sandbox robusta. |
| Liquid Co-Invest | Documentación oficial; sin SDK | OAuth estándar documenta read+trade y cambio de paper a live. No se confirmó endpoint público gratuito read-only con derechos suficientes en las páginas inspeccionadas. | **BLOCKED_TRADE_SCOPE / NO_PUBLIC_READ_ONLY_API_CONFIRMED**. Sin OAuth/MCP/cuenta/wallet/credenciales. No se afirma inexistencia universal de API. |

## Seguridad y costes

La primera auditoría aislada Agent Reach detectó avisos en pip 26.0.1; se conserva el resultado negativo. Se actualizó ese pip a 26.2.1. Las auditorías finales de los subconjuntos instalados no detectaron vulnerabilidades conocidas. **No certifican el árbol completo Vibe**, que no se instaló. Shell, escritura, código generado, broker tools, red y posibles modelos facturables impiden habilitarlo directamente en HQ.

`scripts/evaluate_integrations.py` usa subprocess con entorno reducido sin secretos; `audit_agent_reach.py` restringe la comprobación a RSS; `audit_vibe_metadata.py` solo usa `yaml.safe_load`. Sin cuentas nuevas ni servicios contratados. Coste adicional de servicios: **0 EUR**.

A20 está desactivado por defecto en `.env.example`; la activación local autorizada usa `AGENT_REACH_PUBLIC_ENABLED=true`. Host/ruta GET BCE cerrados, cache 30 min y presupuesto local dos solicitudes/minuto. Contenido externo **no confiable, nunca instrucciones**: metadatos sanitizados, sin HTML, scripts, cuerpos de artículos ni seguimiento de enlaces. DTD/entidades y XML UTF-16 con bytes nulos rechazados. Noticias BCE atribuidas, sin pretendida confirmación independiente.

Los 30 roles de `agent_role_plan.py` son declaraciones desactivadas, sin trabajos ni herramientas habilitadas. Capacidad futura declarativa: una inferencia local, dos tareas quant CPU y cuatro fetches; no es un scheduler operativo. `vibe_readonly.py` conserva Decimal, UTC, procedencia y derechos; no inventa OHLC desde tipos de referencia.

Fuentes primarias: [Agent Reach](https://github.com/Panniantong/agent-reach), [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading), [Liquid Co-Invest](https://www.liquid.trade/coinvest-docs), [Liquid](https://docs.liquid.trade/about-liquid/what-is-liquid), [RSS BCE](https://www.ecb.europa.eu/home/html/rss.en.html), [condiciones BCE](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html).
