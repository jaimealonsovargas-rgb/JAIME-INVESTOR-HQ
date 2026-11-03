# Skills de agente vendoreadas (ADR D028)

39 skills curadas de tres colecciones externas, copiadas al repo para que Codex (y Claude Code) las
use sin depender de marketplaces externos. Ubicación: `.agents/skills/` (ámbito de proyecto, se
versionan con el repo). Codex las descubre automáticamente; se invocan implícitamente o con
`$nombre-de-skill`.

## Reglas permanentes (leen esto antes de usarlas)

- Las skills son **consultas, análisis y simulación**. Nunca autorizan escritura a
  brókeres/exchanges/cuentas ni rompen los invariants del proyecto: PAPER ONLY, 0 EUR, Nivel 3
  de la política D027, `POST /api/orders = 403`.
- Datos de las skills no oficiales (Yahoo en `trader-*`) son **Nivel 2**: etiqueta
  `UNOFFICIAL_SOURCE`, sin redistribución, nunca fuente primaria si hay alternativa oficial.
- No se copian números de salida de una skill al dominio del producto sin pasar por el pipeline
  P2 (derechos, frescura, calidad). Una skill acelera al agente; el pipeline sigue siendo la fuente
  de verdad.
- Cuando una skill genere código (vectorbt, backtrader), ese código hereda las reglas del repo:
  tests, `manage.py check`, sin datos inventados.

## Inventario y mapeo a fases

### Research / P4 (de Maybern/claude-skills, Apache-2.0)
Workflows de analista de equity research, en inglés, solo instrucciones (sin scripts).

| Skill | Para qué | Fase |
|---|---|---|
| `morning-note` | Nota matinal de mercado del meeting de las 7 | P4 |
| `thesis-tracker` | Tesis con pilares, riesgos, catalizadores y log de actualizaciones (mapea al dominio tesis/evidencias/postmortems) | P4 |
| `catalyst-calendar` | Calendario de earnings/eventos/reguladores por universo (trigger por evento para la autonomía) | P4 |
| `earnings-analysis` | Análisis de resultados trimestrales (equivale a "Earnings Reviewer") | P4 |
| `earnings-preview` | Previsualización de earnings | P4 |
| `sector-overview` | Panorama sectorial | P4 |
| `idea-generation` | Generación de ideas de inversión | P4 |
| `model-update` | Actualización de modelo financiero tras filings (parte de "Model Builder") | P4 |
| `3-statement-model` | Modelo de 3 estados enlazados | P4 |
| `dcf-model` | Valoración DCF | P4 |
| `comps-analysis` | Comparables | P4 |

### Quant / P5 (de agiprolabs/claude-trading-skills, MIT)
Instrucciones sobre librerías Python estándar del sector. Listas para cuando se autorice P5.

`vectorbt` (backtesting vectorizado, grid search de parámetros), `backtrader` (backtesting
dirigido por eventos), `pandas-ta` (indicadores), `position-sizing`, `kelly-criterion`,
`risk-management`, `mean-reversion`, `exit-strategies`, `trade-journal`, `portfolio-analytics`,
`regime-detection`, `volatility-modeling`, `feature-engineering`, `walk-forward-validation`,
`slippage-modeling`, `market-microstructure-traditional`, `fixed-income`, `yield-analysis`,
`options-pricing`.

### Trading floor / P6 (de Jakeschincariol/day-trader-skill, MIT)
Pipeline de day trading con scripts Python (stdlib, sin claves). Datos: Yahoo (Nivel 2) y
SEC EDGAR. **Excluidas a propósito**: `trader-broker` (ejecuta órdenes en brokers; el proyecto
tiene su propio guard 403 y P6 define InternalPaperBroker) y `trader-pelosi` (fuera de alcance).

`trader-scanner` (escanea ~5.900 acciones US con setups), `trader-news`, `trader-entry`,
`trader-exit`, `trader-timemachine` (Monte Carlo + replay histórico), `trader-budget`,
`trader-risk` (puerta determinista PASS/BLOCK — patrón de referencia para el risk engine de P6),
`trader-alerts`, `trader-analyst` (earnings desde SEC EDGAR XBRL).

## Procedencia y licencias

Ver `LICENSES/`. Resumen: Maybern = Apache-2.0; agiprolabs (AGIPro) = MIT;
Jakeschincariol = MIT. Cada skill conserva su aviso de copyright. No se ha modificado el
contenido de las skills salvo este README, que las gobierna.

## Mantenimiento

- Actualizar = sustituir la carpeta de la skill y anotar la versión/commit de origen aquí.
- Una skill que deje de ser útil se borra de este directorio (no de las colecciones originales).
- Antes de añadir una skill nueva: verificar licencia, que no requiera claves de pago y que no
  contradiga los invariants del proyecto.
