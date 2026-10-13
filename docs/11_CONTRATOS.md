# Contratos de dominio y órdenes

## Instrument
id; symbol; venue; currency; asset_class; isin/cusip; bond_terms; provider_capabilities (research, valuation, internal_paper, broker_paper, checked_at, reason).

## Position
instrument_id; account_scope (MASTER, ALPACA_PAPER, T212_DEMO); qty_decimal; currency; cost_basis; market_value; fx_to_eur; fx_timestamp; pnl_realized_eur; pnl_unrealized_eur; as_of; quality_flags; thesis_id.

## Trade
id; side; fills[]; opened_at; closed_at?; thesis_version; committee_decision; risk_decision; pnl_eur; pnl_pct; postmortem.

## Job
id; agent_id; state; started_at; updated_at; progress; output_refs[]; evidence_refs[]; error_code.

## RiskDecision
approved; hard_blocks[]; warnings[]; rule_version; inputs_hash; as_of.

## Máquina de órdenes
DRAFT → PROPOSED → RISK_APPROVED → SUBMITTING → ACKNOWLEDGED → PARTIAL_FILLED → FILLED/CANCELED/REJECTED. Timeout de SUBMITTING → UNKNOWN: **prohibido reintentar** hasta reconciliación de bróker. Kill switch bloquea órdenes nuevas. Solo endpoint paper allowlisted.

## Eventos auditables
UUID, schema_version, occurred_at UTC, source, actor, correlation_id, causation_id, idempotency_key si existe, payload validado, hash. No guardar claves ni datos privados en auditoría.
