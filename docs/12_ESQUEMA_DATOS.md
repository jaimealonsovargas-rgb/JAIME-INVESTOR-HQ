# Esquema relacional inicial

accounts(id, scope, provider, currency, active)
instruments(id, asset_class, venue, currency, isin, terms_json)
provider_capabilities(provider, instrument_type, capability, checked_at, reason)
observations(id, instrument_id, provider, observed_at, received_at, bid, ask, last, quality, rights)
fx_rates(pair, timestamp, provider, rate)
portfolios(id, base_currency, seed_virtual)
ledger_events(id, portfolio_id, type, amount, currency, fx_ref, source_ref, occurred_at, hash)
ledger_entries(event_id, account_code, debit, credit)
lots(id, instrument_id, qty_remaining, cost_basis, acquired_at)
orders(id, account_id, instrument_id, state, client_ref, external_id, created_at)
fills(id, order_id, qty, price, fee, fx_ref, filled_at)
research_cases(id, instrument_id, thesis_version, status)
evidence(id, case_id, source_url, retrieved_at, excerpt_hash, rights)
committee_decisions(id, case_id, outcome, dissent, timestamp)
risk_decisions(id, order_id, approved, rules_json, timestamp)
agents(id, name, role)
jobs(id, agent_id, state, started_at, updated_at, result_ref)
audit_events(id, actor, action, object_ref, before_hash, after_hash, timestamp)

Migraciones Alembic, claves foráneas, índices por timestamp/instrument/order/job, unique(client_ref, account_id) si procede, backup local y SQLite WAL. No secretos en DB. Los snapshots de NAV no reemplazan el ledger append-only.
