/** A person is an office seat for logical roles, never an invented worker. */
export const PERSON_ROLES:Record<string,{label:string;roles:string[]}>= {
 'personal-recepcion': {label:'Informes y seguimiento',roles:['reporting_postmortem']},
 'personal-trading-0': {label:'Estructura de mercado',roles:['market_structure']},
 'personal-trading-1': {label:'Liquidez y costes',roles:['liquidity_slippage']},
 'personal-trading-2': {label:'Planificación de ejecución',roles:['paper_execution_planning']},
 'personal-research-1': {label:'Análisis empresarial',roles:['fundamental_equity','valuation']},
 'personal-research-2': {label:'Macro y crédito',roles:['macro_global','macro_europe_spain','credit_fixed_income']},
 'personal-research-3': {label:'Información y regulación',roles:['esg_regulation','news_social_intelligence']},
 'personal-quant-1': {label:'Investigación cuantitativa',roles:['momentum_trend','mean_reversion','volatility_regime']},
 'personal-quant-2': {label:'Factores y construcción de cartera',roles:['value_quality','portfolio_optimization']},
 'personal-risk-1': {label:'Riesgos de cartera',roles:['market_risk','concentration','credit_counterparty']},
 'personal-risk-2': {label:'Liquidez y controles',roles:['liquidity_risk','compliance_kill_switch']},
 'personal-execution-1': {label:'Reconciliación paper',roles:['paper_reconciliation']},
 'personal-performance': {label:'Resultados y atribución',roles:['nav_attribution','benchmark_fx']},
 'personal-systems-2': {label:'Calidad y proveedores',roles:['data_quality','provider_orchestration']},
 'personal-systems': {label:'Supervisión del sistema',roles:['observability_security']},
 'personal-comite': {label:'Comité de investigación',roles:['bull_advocate','bear_skeptic','cio_chair']},
};

export const ROLE_LABELS:Record<string,string>={
 fundamental_equity:'Fundamentales',valuation:'Valoración',macro_global:'Macro global',macro_europe_spain:'Europa y España',credit_fixed_income:'Crédito y renta fija',esg_regulation:'Sostenibilidad y regulación',news_social_intelligence:'Noticias y fuentes públicas',
 market_structure:'Estructura de mercado',liquidity_slippage:'Liquidez y costes',paper_execution_planning:'Planificación paper',paper_reconciliation:'Reconciliación',momentum_trend:'Tendencia',mean_reversion:'Reversión a la media',volatility_regime:'Volatilidad',value_quality:'Valor y calidad',portfolio_optimization:'Construcción de cartera',market_risk:'Riesgo de mercado',concentration:'Concentración',credit_counterparty:'Contraparte',liquidity_risk:'Riesgo de liquidez',compliance_kill_switch:'Límites y controles',nav_attribution:'NAV y atribución',benchmark_fx:'Benchmark y divisas',data_quality:'Calidad de datos',provider_orchestration:'Proveedores',observability_security:'Supervisión',reporting_postmortem:'Informes y seguimiento',bull_advocate:'Tesis favorable',bear_skeptic:'Revisión crítica',cio_chair:'Síntesis del comité',
};
