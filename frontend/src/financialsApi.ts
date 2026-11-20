export interface FinancialFact {id:string;cik:string;metric:string;taxonomy:string;concept:string;unit:string;value:string;start:string|null;end:string;days:number|null;period_type:string;accession:string;filed:string;form:string;filing_fiscal_year:number|null;published_bound:string;quality_flags?:string[]}
export interface FinancialMetric {metric:string;label:string;state:string;fact:FinancialFact|null;candidate_ids:string[]}
export interface AnnualAccounts {start:string;end:string;accession:string;filed:string;currency:string|null;form:string;metrics:FinancialMetric[];core_available:number;core_total:number;state:string;url:string;age_days?:number;stale?:boolean}
export interface Filing {accession:string;form:string;filed:string;report_date:string|null;accepted_at:string|null;url:string;amended:boolean}
export interface Page<T> {items:T[];total:number;offset:number;limit:number;older_history_pending?:boolean}
export interface Financials {cik:string;as_of:string;annual:AnnualAccounts|null;profile:{name:string;fiscal_year_end:string|null;sic_description:string;older_files:{name:string}[]}|null;coverage:{facts:number;metrics:number;metric_denominator:number;periods:number;changed_value_groups:number;quarantined_facts:number;oldest_period:string|null;newest_period:string|null};documents:Page<Filing>;sources:{id:string;kind:string;source:string;payload_hash:string;received_at:string;parser_version:string}[];readiness:{use:string;state:string;reason:string}[];limitations:string[]}
export interface FinancialJob {id:string;state:string;created_at:string;updated_at:string;total:number;completed:number;counts:Record<string,number>;manifest:{issuers:{cik:string;name:string;symbol:string}[];selection:string};current:{cik:string;kind:string;state:string;error:string|null;next_at:string}[];errors:{cik:string;kind:string;state:string;error:string}[]}
export interface FinancialSummary {counts:{issuers_with_facts:number;issuers_with_documents:number;snapshots:number;receipts:number};latest_job:FinancialJob|null;metric_denominator:number;access:string;worker_running:boolean;worker_error:string|null}
const object=(v:unknown):v is Record<string,unknown>=>typeof v==='object'&&v!==null;
const count=(v:unknown)=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0;
const fact=(v:unknown)=>object(v)&&['id','unit','value','end','accession','filed','concept'].every(k=>typeof v[k]==='string')&&Number.isFinite(Number(v.value));
const job=(v:unknown)=>object(v)&&typeof v.id==='string'&&typeof v.state==='string'&&count(v.total)&&count(v.completed)&&object(v.manifest)&&Array.isArray(v.manifest.issuers)&&Array.isArray(v.errors)&&Array.isArray(v.current)&&object(v.counts);
const page=(v:unknown)=>object(v)&&Array.isArray(v.items)&&count(v.total)&&count(v.offset)&&count(v.limit);
async function request<T>(path:string,valid:(value:unknown)=>boolean,signal?:AbortSignal,init?:RequestInit):Promise<T>{
  const response=await fetch('/api/universe/'+path,{credentials:'omit',cache:'no-store',...init,signal:signal?AbortSignal.any([signal,AbortSignal.timeout(20000)]):AbortSignal.timeout(20000)});
  if(!response.ok)throw new Error(response.status===409?'Ya hay una captación activa o falta preparación de la fuente. Consulta su estado antes de reintentar.':response.status===403?'La fuente está desactivada o tiene el acceso restringido.':'No se pudieron consultar las cuentas. Comprueba el backend y reintenta.');
  const result:unknown=await response.json();
  if(!valid(result))throw new Error('La respuesta financiera no es válida; se han ocultado las cifras.');
  return result as T;
}
export const fetchFinancialSummary=(signal?:AbortSignal)=>request<FinancialSummary>('financials/summary',v=>object(v)&&object(v.counts)&&['issuers_with_facts','issuers_with_documents','snapshots','receipts'].every(k=>count((v.counts as Record<string,unknown>)[k]))&&(v.latest_job===null||job(v.latest_job)),signal);
export const fetchFinancials=(cik:string,signal?:AbortSignal)=>request<Financials>('issuers/'+encodeURIComponent(cik)+'/financials',v=>object(v)&&object(v.coverage)&&['facts','metrics','metric_denominator','periods','changed_value_groups'].every(k=>count((v.coverage as Record<string,unknown>)[k]))&&Array.isArray(v.sources)&&Array.isArray(v.readiness)&&Array.isArray(v.limitations)&&page(v.documents)&&(v.annual===null||object(v.annual)&&Array.isArray(v.annual.metrics)&&v.annual.metrics.every(m=>object(m)&&typeof m.label==='string'&&(m.fact===null||fact(m.fact)))),signal);
export const fetchDocuments=(cik:string,offset:number,signal?:AbortSignal)=>request<Page<Filing>>('issuers/'+encodeURIComponent(cik)+'/documents?limit=25&offset='+offset,v=>page(v)&&object(v)&&(v.items as unknown[]).every(d=>object(d)&&typeof d.accession==='string'&&typeof d.url==='string'),signal);
export const fetchFactHistory=(cik:string,metric:string,offset:number,signal?:AbortSignal)=>request<Page<FinancialFact>>('issuers/'+encodeURIComponent(cik)+'/facts?'+new URLSearchParams({metric,limit:'25',offset:String(offset)}),v=>page(v)&&object(v)&&(v.items as unknown[]).every(fact),signal);
const post=(body:unknown,key?:string):RequestInit=>({method:'POST',headers:{'Content-Type':'application/json','X-HQ-Universe':'1',...(key?{'Idempotency-Key':key}:{})},body:JSON.stringify(body)});
export const startFinancialImport=(key:string,ciks?:string[])=>request<FinancialJob>('financials/jobs',job,undefined,post(ciks?{ciks}:{},key));
export const controlFinancialImport=(key:string,action:'pause'|'resume'|'cancel')=>request<FinancialJob>('financials/jobs/'+encodeURIComponent(key)+'/control',job,undefined,post({action}));
export const financialTime=(value:string)=>new Intl.DateTimeFormat('es-ES',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Madrid'}).format(new Date(value))+' · Madrid';
export const financialDay=(value:string)=>new Intl.DateTimeFormat('es-ES',{dateStyle:'medium',timeZone:'Europe/Madrid'}).format(new Date(value+'T12:00:00Z'));
export function financialValue(value:string,unit:string){
  const amount=Number(value);
  if(!Number.isFinite(amount))return 'Dato no válido';
  if(/^[A-Z]{3}$/.test(unit))return new Intl.NumberFormat('es-ES',{maximumFractionDigits:2,minimumFractionDigits:2,useGrouping:true}).format(amount/1e6)+' M '+unit;
  if(unit==='shares')return new Intl.NumberFormat('es-ES',{maximumFractionDigits:3,useGrouping:true}).format(amount/1e6)+' M acciones';
  return new Intl.NumberFormat('es-ES',{maximumFractionDigits:4,useGrouping:true}).format(amount)+' '+unit;
}
