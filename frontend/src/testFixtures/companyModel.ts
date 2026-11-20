import type {CompanyModel} from '../companyModelsApi';
import type {FinancialFact} from '../financialsApi';
export function sampleModel():CompanyModel{
 const fact:FinancialFact={id:'test-fact',cik:'0000000001',metric:'revenue',taxonomy:'us-gaap',concept:'Revenues',unit:'USD',value:'100',start:'2025-01-01',end:'2025-12-31',days:365,period_type:'ANNUAL',accession:'0000000001-26-000001',filed:'2026-02-01',form:'10-K',filing_fiscal_year:2025,published_bound:'2026-02-02T05:00:00Z'};
 const source={name:'TEST ONLY',snapshot_id:'test-snapshot',receipt_id:'test-receipt',received_at:'2026-02-03T00:00:00Z',payload_hash:'test-hash',url:'https://data.sec.gov/'};
 return {id:'test-model',cik:'0000000001',version:1,created_at:'2026-02-03T00:00:00Z',as_of:'2026-02-03T00:00:00Z',previous_id:null,payload_hash:'test-hash',payload:{template_version:'test-only',entity_id:'0000000001',source,
 annual:{start:'2025-01-01',end:'2025-12-31',accession:fact.accession,filed:fact.filed,currency:'USD',form:'10-K',state:'PARTIAL',metrics:[],core_available:1,core_total:6,url:'https://www.sec.gov/'},comparative:null,
 metrics:[{id:'operating_margin',label:'Margen operativo',formula:'operating_income / revenue × 100',unit:'percent',state:'BLOCKED',value:null,reason:'Falta resultado operativo.',evidence_ids:['test-fact']}],
 evidence:{'test-fact':{...fact,...source,url:'https://www.sec.gov/Archives/edgar/data/1/000000000126000001/'}},earnings:{changes:[],period_note:'Sin comparativo.'},valuation:{state:'BLOCKED',missing:['WACC documentado'],target_price:null},review:{state:'PARTIAL',scope:'TEST ONLY',checks:[{id:'balance',state:'BLOCKED',reason:'Falta patrimonio total.',evidence_ids:[]}]},update:{reason:'FIRST_MODEL',changes:[]},narrative:{state:'NOT_REQUESTED',reason:'Sin inferencia local.'},limitations:['TEST ONLY'],execution_ready:false,backtest_ready:false}};
}
