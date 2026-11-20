import type {AnnualAccounts,FinancialFact} from './financialsApi';

export type ModelMetric={id:string;label:string;formula:string;unit:string;state:string;value:string|null;reason:string|null;evidence_ids:string[]};
export type ModelChange=ModelMetric&{current:string|null;previous:string|null;delta:string|null;source_unit:string|null};
export type ModelBrief={id:string;cik:string;name:string;version:number;created_at:string;as_of:string;period_end:string;state:string;reason:string;evidence_count:number};
type FilingReference={url:string;sha256:string};
type FilingEquation={blocked:string}|{role:string;total:{concept:string;value:string};terms:{concept:string;context:string;value:string|null;weight:number}[]};
type FilingStatement={receipt:{received_at:string;calculation:FilingReference;instance:FilingReference};equations:Record<string,FilingEquation>};
export type CompanyModel={id:string;cik:string;version:number;created_at:string;as_of:string;previous_id:string|null;payload_hash:string;payload:{
 template_version:string;entity_id:string;source:{name:string;snapshot_id:string;receipt_id:string;received_at:string;payload_hash:string;url:string};
 annual:AnnualAccounts;comparative:AnnualAccounts|null;metrics:ModelMetric[];
 evidence:Record<string,FinancialFact&{snapshot_id:string;receipt_id:string;received_at:string;url:string}>;
 earnings:{changes:ModelChange[];period_note:string};valuation:{state:string;missing:string[];target_price:null};
 filing_statement?:FilingStatement;
 review:{state:string;scope:string;checks:{id:string;state:string;reason:string;evidence_ids:string[];residual?:string;reported_residual?:string;cross_residual?:string;source_residual?:string;unit?:string}[]};
 update:{reason:string;changes:{metric:string;label:string;before:FinancialFact|null;after:FinancialFact|null}[]};
 narrative:{state:string;reason:string};limitations:string[];execution_ready:false;backtest_ready:false;
}};
type Versions={items:ModelBrief[];total:number;offset:number;limit:number};
const object=(v:unknown):v is Record<string,unknown>=>!!v&&typeof v==='object';
const numeric=(v:unknown)=>typeof v==='string'&&/^-?\d+(\.\d+)?$/.test(v)&&Number.isFinite(Number(v));
const strings=(v:unknown)=>Array.isArray(v)&&v.every(x=>typeof x==='string');
const dateText=(v:unknown)=>typeof v==='string'&&Number.isFinite(Date.parse(v));
function filedStatement(v:unknown){
 if(!object(v)||!object(v.receipt)||!object(v.equations)||!dateText(v.receipt.received_at))return false;
 const refs=[v.receipt.calculation,v.receipt.instance];
 if(!refs.every(r=>object(r)&&typeof r.url==='string'&&/^https:\/\/www\.sec\.gov\/Archives\/edgar\/data\/\d+\/\d+\/[\w-]+\.(xml|xsd)$/.test(r.url)&&typeof r.sha256==='string'&&/^[a-f0-9]{64}$/.test(r.sha256)))return false;
 return Object.values(v.equations).every(e=>object(e)&&(typeof e.blocked==='string'||
   (object(e.total)&&numeric(e.total.value)&&typeof e.total.concept==='string'&&Array.isArray(e.terms)&&e.terms.every(t=>object(t)&&typeof t.concept==='string'&&typeof t.context==='string'&&(t.value===null||numeric(t.value))&&(t.weight===1||t.weight===-1)))));
}
const fact=(f:unknown)=>object(f)&&['id','unit','accession','concept','end','filed','taxonomy'].every(k=>typeof f[k]==='string')&&numeric(f.value)&&dateText(f.end)&&(f.start===null||dateText(f.start));
const brief=(v:unknown)=>object(v)&&['id','cik','name','created_at','as_of','period_end','state','reason'].every(k=>typeof v[k]==='string')&&Number.isSafeInteger(v.version)&&Number(v.version)>0;
export function validCompanyModel(v:unknown):v is CompanyModel{
 if(!object(v)||!object(v.payload)||typeof v.id!=='string'||typeof v.cik!=='string'||!Number.isSafeInteger(v.version)||!dateText(v.created_at)||!dateText(v.as_of))return false;
 const p=v.payload;
 if(!object(p.annual)||!object(p.source)||!object(p.evidence)||!Array.isArray(p.metrics)||!object(p.earnings)||!Array.isArray(p.earnings.changes)||!object(p.review)||!Array.isArray(p.review.checks)||!object(p.valuation)||!strings(p.valuation.missing)||!object(p.update)||!Array.isArray(p.update.changes)||!object(p.narrative)||!strings(p.limitations))return false;
 const evidence=p.evidence;
 if(p.filing_statement!==undefined&&!filedStatement(p.filing_statement))return false;
 if(!dateText(p.annual.start)||!dateText(p.annual.end)||typeof p.annual.form!=='string'||typeof p.annual.currency!=='string'||!dateText(p.source.received_at)||typeof p.narrative.reason!=='string'||typeof p.review.scope!=='string'||p.entity_id!==v.cik||p.valuation.target_price!==null)return false;
 if(!p.review.checks.every(c=>object(c)&&['id','state','reason'].every(k=>typeof c[k]==='string')&&['residual','reported_residual'].every(k=>c[k]===undefined||numeric(c[k]))&&(c.unit===undefined||typeof c.unit==='string')))return false;
 if(!p.update.changes.every(c=>object(c)&&typeof c.label==='string'&&typeof c.metric==='string'&&(c.before===null||fact(c.before))&&(c.after===null||fact(c.after))))return false;
 if(!p.earnings.changes.every(c=>object(c)&&['current','previous','delta'].every(k=>c[k]===null||numeric(c[k]))))return false;
 if(!Object.values(evidence).every(f=>object(f)&&['id','unit','accession','concept','end','filed','snapshot_id','receipt_id','received_at'].every(k=>typeof f[k]==='string')&&numeric(f.value)&&typeof f.url==='string'&&/^https:\/\/www\.sec\.gov\/Archives\/edgar\/data\//.test(f.url)))return false;
 return [...p.metrics,...p.earnings.changes].every(m=>object(m)&&typeof m.id==='string'&&typeof m.label==='string'&&typeof m.formula==='string'&&typeof m.unit==='string'&&strings(m.evidence_ids)&&(m.evidence_ids as string[]).every(id=>id in evidence)&&(['AVAILABLE','BLOCKED'].includes(String(m.state)))&&(m.state==='AVAILABLE'?numeric(m.value):m.value===null))&&p.execution_ready===false&&p.backtest_ready===false;
}
const errors:Record<string,string>={NO_FINANCIAL_DATA:'Primero actualiza las cuentas SEC de esta empresa.',NO_ANNUAL_ACCOUNTS:'No hay un ejercicio anual con datos suficientes.',AMBIGUOUS_CURRENCY:'El informe contiene divisas ambiguas; requiere revisión.',SOURCE_UNAVAILABLE:'La fuente SEC está desactivada. No se muestran sus modelos.',MODEL_STORAGE_LIMIT:'Se alcanzó el límite local de modelos; revisa la retención antes de continuar.',INVALID_KNOWLEDGE_CUTOFF:'La fecha debe incluir zona horaria y no puede ser futura.',IDEMPOTENCY_CONFLICT:'El identificador corresponde a otra solicitud. Recarga la ficha.'};
Object.assign(errors,{ORIGINAL_UNAVAILABLE:'No se puede leer el original SEC guardado. Revisa el archivo local antes de reconstruir.',ORIGINAL_INTEGRITY_FAILED:'El original SEC no supera el control de integridad. No se ha creado una versión.',INVALID_ARCHIVE_HASH:'La referencia del original SEC no es válida. No se ha creado una versión.'});
async function request<T>(path:string,valid:(v:unknown)=>boolean,signal?:AbortSignal,init?:RequestInit):Promise<T>{
 const response=await fetch('/api/universe/'+path,{credentials:'omit',cache:'no-store',...init,signal:signal?AbortSignal.any([signal,AbortSignal.timeout(20000)]):AbortSignal.timeout(20000)});
 if(!response.ok){const body:unknown=await response.json().catch(()=>null);throw new Error(object(body)&&typeof body.detail==='string'&&errors[body.detail]||'No se pudo consultar el modelo. Comprueba la conexión y reintenta.');}
 const result:unknown=await response.json();if(!valid(result))throw new Error('El modelo recibido no es válido; se han ocultado las cifras.');return result as T;
}
const path=(cik:string)=>'issuers/'+encodeURIComponent(cik)+'/models';
export const fetchModelVersions=(cik:string,offset=0,signal?:AbortSignal)=>request<Versions>(path(cik)+'?limit=20&offset='+offset,v=>object(v)&&Array.isArray(v.items)&&v.items.every(brief)&&Number.isSafeInteger(v.total),signal);
export const fetchCompanyModel=(cik:string,id:string,signal?:AbortSignal)=>request<CompanyModel>(path(cik)+'/'+encodeURIComponent(id),validCompanyModel,signal);
export const buildCompanyModel=(cik:string,key:string)=>request<CompanyModel>(path(cik),validCompanyModel,undefined,{method:'POST',headers:{'Content-Type':'application/json','X-HQ-Universe':'1','Idempotency-Key':key},body:'{}'});
export const fetchRecentModels=(signal?:AbortSignal)=>request<ModelBrief[]>('models/recent',v=>Array.isArray(v)&&v.every(brief),signal);
