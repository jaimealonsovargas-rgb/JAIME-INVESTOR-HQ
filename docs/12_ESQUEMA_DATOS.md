# Esquema relacional inicial

> **P3 autorizado 2026-10-16:** ver `PLAN_P3_LEDGER_CARTERA_Y_HUD.md`. Antes de añadir tablas, Codex debe inspeccionar migraciones/modelos reales y extenderlos sin duplicar conceptos existentes.

accounts(id, scope, provider, currency, active)
instruments(id, asset_class, venue, currency, isin, terms_json)
provider_capabilities(provider, instrument_type, capability, checked_at, reason)
observations(id, instrument_id, provider, observed_at, received_at, bid, ask, last, quality, rights)
fx_rates(pair, timestamp, provider, rate)
portfolios(id, base_currency, seed_virtual, status)
ledger_events(id, portfolio_id, type, amount, currency, fx_ref, source_ref, occurred_at, hash)
ledger_entries(event_id, account_code, debit, credit)
lots(id, portfolio_id, instrument_id, qty_original, qty_remaining, cost_basis, currency, acquired_at, source_event_id)
valuation_snapshots(id, portfolio_id, as_of, cash_eur, market_value_eur, accruals_eur, liabilities_eur, nav_eur, realized_pnl_eur, unrealized_pnl_eur, fx_pnl_eur, quality, provenance_json)
orders(id, account_id, instrument_id, state, client_ref, external_id, created_at)
fills(id, order_id, qty, price, fee, fx_ref, filled_at)
research_cases(id, instrument_id, thesis_version, status)
evidence(id, case_id, source_url, retrieved_at, excerpt_hash, rights)
committee_decisions(id, case_id, outcome, dissent, timestamp)
risk_decisions(id, order_id, approved, rules_json, timestamp)
agents(id, name, role)
jobs(id, agent_id, state, started_at, updated_at, result_ref)
audit_events(id, actor, action, object_ref, before_hash, after_hash, timestamp)

## Invariantes P3

- `DEPOSIT_VIRTUAL` MASTER de 10.000,00 EUR se crea una sola vez; `source_ref`/clave equivalente debe impedir duplicado.
- Cada evento contable cumple débitos = créditos.
- Posiciones se derivan de lotes/ledger; si se materializan, deben reconciliarse.
- `valuation_snapshots` nunca reemplaza el ledger append-only; es caché/auditoría reproducible con referencias de precio y FX.
- Dinero/precio/qty/FX nunca usan `float`; elegir representación Decimal segura para SQLite tras inspeccionar el código actual.
- Índices por portfolio/timestamp/instrument/source_ref; constraints de idempotencia donde proceda.
- `orders`/`fills` permanecen inactivos en P3 salvo fixtures aislados de tests; `/api/orders` sigue 403.

Migraciones Alembic, claves foráneas, backup local y SQLite WAL. No secretos en DB. Los snapshots de NAV no reemplazan el ledger append-only.
