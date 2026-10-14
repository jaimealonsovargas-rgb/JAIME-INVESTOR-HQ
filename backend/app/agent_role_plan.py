"""Reserva declarativa aprobada. No es un registry operativo, scheduler ni agentes P4."""
ROLE_TEAMS = {
    'research': ('fundamental_equity', 'valuation', 'macro_global', 'macro_europe_spain', 'credit_fixed_income', 'esg_regulation'),
    'trading_execution': ('market_structure', 'liquidity_slippage', 'paper_execution_planning', 'paper_reconciliation'),
    'quant': ('momentum_trend', 'value_quality', 'mean_reversion', 'volatility_regime', 'portfolio_optimization'),
    'risk': ('market_risk', 'credit_counterparty', 'liquidity_risk', 'concentration', 'compliance_kill_switch'),
    'performance': ('nav_attribution', 'benchmark_fx', 'reporting_postmortem'),
    'systems_data': ('data_quality', 'provider_orchestration', 'news_social_intelligence', 'observability_security'),
    'committee': ('cio_chair', 'bull_advocate', 'bear_skeptic'),
}
FUTURE_ROLE_PLAN = tuple({'role_id': role, 'team': team, 'phase_required': 'P4',
    'enabled': False, 'tools_allowed_now': (), 'jobs': (), 'state': 'NO DISPONIBLE',
    'input_schema': 'hq.p2.research.v1', 'output_schema': 'future_evidence_report',
    'evidence_required': True, 'depends_on': ('P2',), 'cost_policy': 'LOCAL_ONLY_NO_PAID_CALLS',
    'timeout_seconds': None, 'model_version': None, 'prompt_version': None,
    'error_states': ('NO_DATA','NO_LOCAL_MODEL','RIGHTS_RESTRICTED','TIMEOUT','CANCELLED')}
    for team, roles in ROLE_TEAMS.items() for role in roles)
FUTURE_CAPACITY = {'local_inference': 1, 'quant_cpu_jobs': 2, 'data_fetches': 4,
    'preset_catalog_maximum': 30, 'initial_preset_target': (6, 10), 'execution_enabled': False}
