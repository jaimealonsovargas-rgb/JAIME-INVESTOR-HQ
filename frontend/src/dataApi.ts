export const DATA_STATES=['AVAILABLE_VERIFIED','DELAYED','STALE','NO_DATA','NO_CREDENTIALS','CONFIG_REQUIRED','AUTH_FAILED','RATE_LIMITED','RIGHTS_RESTRICTED','OFFLINE','TIMEOUT','INVALID_PAYLOAD','ERROR','NOT_IMPLEMENTED','PLAN_REQUIRED','DISABLED','NOT_VERIFIED'] as const;
export type DataState=typeof DATA_STATES[number];
export interface DataRights {license:string;source:string;scope:string;attribution:string;access_allowed:boolean;display_allowed:boolean;storage_allowed:boolean;redistribution_allowed:boolean}
export interface DataSource {access_id:string;provider:string;name:string;implemented:boolean;data_kind:string;asset_class:string;country:string|null;market:string;feed:string;docs:string;rights:DataRights;quota_note:string;quota_used:number;next_allowed_at:string|null;state:DataState;reason:string;checked_at:string|null;latency_ms:number|null;http_status:number|null;real_connection:boolean;usable:boolean;normalized_count:number}
export interface DataQuality {checked_at:string;counts:Record<string,number>;sources:DataSource[]}
export interface DataObservation {id:string;series_id:string;provider:string;feed:string;venue:string;data_kind:string;period:string;period_precision:string;observed_at:string;received_at:string;published_at:string|null;value:string|null;currency:string|null;unit:string;metadata:Record<string,string>;quality_flags:string[];rights:DataRights;source_ref:string;execution_eligible:false}
export interface SourceResult {access_id:string;state:DataState;reason:string;checked_at:string|null;latency_ms:number|null;real_connection:boolean;usable:boolean;cache_hit:boolean;normalized_count:number;observations:DataObservation[]}
const object=(value:unknown):value is Record<string,unknown>=>typeof value==='object'&&value!==null&&!Array.isArray(value);
const date=(value:unknown)=>typeof value==='string'&&Number.isFinite(Date.parse(value));
const nullableDate=(value:unknown)=>value===null||date(value);
const text=(value:unknown)=>typeof value==='string'&&value.length>0;
export const safeHttps=(value:unknown):value is string=>{try{const url=new URL(String(value));return url.protocol==='https:'&&!url.username&&!url.password;}catch{return false;}};
const rights=(value:unknown)=>object(value)&&text(value.license)&&safeHttps(value.source)&&text(value.scope)&&text(value.attribution)&&['access_allowed','display_allowed','storage_allowed','redistribution_allowed'].every(key=>typeof value[key]==='boolean');
const state=(value:unknown)=>DATA_STATES.includes(value as DataState);
async function get(path:string,signal?:AbortSignal):Promise<unknown>{
 const response=await fetch(path,{signal:signal?AbortSignal.any([signal,AbortSignal.timeout(45000)]):AbortSignal.timeout(45000),credentials:'omit',cache:'no-store'});
 if(!response.ok)throw new Error('No se pudo consultar el servicio local de datos.');return response.json();
}
export function validateQuality(value:unknown):DataQuality{
 if(!object(value)||!date(value.checked_at)||!object(value.counts)||!Object.values(value.counts).every(v=>Number.isInteger(v)&&Number(v)>=0)||!Array.isArray(value.sources))throw Error('Contrato Data Quality inválido.');
 const ids=new Set<string>();
 for(const row of value.sources){
  if(!object(row)||!['access_id','provider','name','data_kind','asset_class','market','feed','reason','quota_note'].every(k=>text(row[k]))||!safeHttps(row.docs)||!rights(row.rights)||!state(row.state)||!nullableDate(row.checked_at)||!nullableDate(row.next_allowed_at)||(row.country!==null&&!text(row.country))||!['implemented','real_connection','usable'].every(k=>typeof row[k]==='boolean')||!Number.isInteger(row.quota_used)||!Number.isInteger(row.normalized_count)||(row.latency_ms!==null&&(!Number.isInteger(row.latency_ms)||Number(row.latency_ms)<0))||ids.has(String(row.access_id)))throw Error('Fuente Data Quality inválida.');
  if(row.usable&&(!row.real_connection||!(row.rights as unknown as DataRights).display_allowed))throw Error('Fuente utilizable sin prueba o derechos.');
  ids.add(String(row.access_id));
 }
 if(value.counts.candidate_access_modes!==ids.size||value.counts.implemented_adapters!==value.sources.filter(s=>s.implemented).length||value.counts.verified_connections!==value.sources.filter(s=>s.real_connection).length||value.counts.usable_sources!==value.sources.filter(s=>s.usable).length)throw Error('Contadores Data Quality inconsistentes.');
 return value as unknown as DataQuality;
}
export function validateSource(value:unknown):SourceResult{
 if(!object(value)||!text(value.access_id)||!state(value.state)||!text(value.reason)||!nullableDate(value.checked_at)||!Array.isArray(value.observations)||typeof value.real_connection!=='boolean'||typeof value.usable!=='boolean'||typeof value.cache_hit!=='boolean'||!Number.isInteger(value.normalized_count))throw Error('Contrato de observaciones inválido.');
 for(const row of value.observations){
  if(!object(row)||!rights(row.rights)||!(row.rights as unknown as DataRights).display_allowed||!['id','series_id','provider','feed','venue','data_kind','period','period_precision','unit'].every(k=>text(row[k]))||!date(row.observed_at)||!date(row.received_at)||!safeHttps(row.source_ref)||row.execution_eligible!==false||!Array.isArray(row.quality_flags)||!row.quality_flags.every(s=>typeof s==='string')||!object(row.metadata)||!Object.values(row.metadata).every(s=>typeof s==='string')||(row.value!==null&&(typeof row.value!=='string'||!/^[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?$/.test(row.value))))throw Error('Observación sin contrato, precisión o derechos.');
 }
 return value as unknown as SourceResult;
}
export async function fetchDataQuality(signal?:AbortSignal){return validateQuality(await get('/api/data/quality',signal));}
export async function fetchSource(id:string,signal?:AbortSignal){if(!/^[AB]\d{2}$/.test(id))throw Error('Fuente no registrada.');const result=validateSource(await get('/api/data/sources/'+id,signal));if(result.access_id!==id)throw Error('Respuesta de otra fuente.');return result;}
