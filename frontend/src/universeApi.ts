export interface Listing {id:string;provider:string;cik:string|null;name:string;symbol:string;venue:string;state:string;first_seen_at:string;last_seen_at:string;currency:string|null;category:string}
export interface ListingPage {items:Listing[];total:number;offset:number;limit:number}
export interface ImportResult {id:string;provider:string;state:string;started_at:string;finished_at:string|null;reason?:string;listings?:number;entities?:number;next_allowed_at?:string}
export interface UniverseSummary {counts:{entities:number;listings:number;versions:number;conflicts:number;current_listings:number};imports:ImportResult[];sources:{provider:string;state:string;implemented:boolean;purpose:string;reason:string;docs:string}[];temporal_scope:string}
export interface HistoricalClose {price:string;currency:'EUR';isin:string;session:string;received_at:string;stale:boolean;source:string;observation_id:string;payload_hash:string}
export interface ListingDetail extends Listing {historical_close?:HistoricalClose|null;as_of:string|null;versions:{id:string;known_from:string;known_until:string|null;source:string;payload_hash:string;payload:{symbol:string;name:string;state:string}}[];readiness:{use:string;state:string;reason:string}[]}

const object=(v:unknown):v is Record<string,unknown>=>typeof v==='object'&&v!==null;
const count=(v:unknown)=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0;
const listing=(v:unknown)=>object(v)&&['id','provider','name','symbol','venue','state','first_seen_at','last_seen_at'].every(k=>typeof v[k]==='string');

async function request<T>(url:string, valid:(v:unknown)=>boolean, signal?:AbortSignal, init?:RequestInit):Promise<T>{
  const response=await fetch(url,{credentials:'omit',cache:'no-store',...init,signal:signal?AbortSignal.any([signal,AbortSignal.timeout(init?45000:8000)]):AbortSignal.timeout(init?45000:8000)});
  if(!response.ok)throw new Error(response.status===404?'El registro ya no está disponible.':'No se pudo consultar el catálogo. Comprueba el backend local e inténtalo de nuevo.');
  const data:unknown=await response.json();
  if(!valid(data))throw new Error('La respuesta del catálogo no es válida. No se mostrarán datos incompletos.');
  return data as T;
}

export const fetchUniverse=(signal?:AbortSignal)=>request<UniverseSummary>('/api/universe/summary',v=>object(v)&&object(v.counts)&&['entities','listings','versions','conflicts','current_listings'].every(k=>count((v.counts as Record<string,unknown>)[k]))&&Array.isArray(v.sources)&&v.sources.every(s=>object(s)&&['provider','state','purpose','reason','docs'].every(k=>typeof s[k]==='string'))&&Array.isArray(v.imports),signal);
export function fetchListings(q:string,state:string,offset:number,signal?:AbortSignal){
  const params=new URLSearchParams({q,offset:String(offset),limit:'50'});if(state)params.set('state',state);
  return request<ListingPage>('/api/universe/listings?'+params,v=>object(v)&&Array.isArray(v.items)&&v.items.every(listing)&&count(v.total)&&count(v.offset)&&count(v.limit),signal);
}
function validClose(value:unknown){
  if(value===undefined||value===null)return true;
  return object(value)&&typeof value.price==='string'&&/^\d+(\.\d+)?$/.test(value.price)&&Number(value.price)>0
    &&value.currency==='EUR'&&value.isin==='HRHT00RA0005'&&typeof value.session==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value.session)
    &&typeof value.received_at==='string'&&Number.isFinite(Date.parse(value.received_at))&&typeof value.stale==='boolean'
    &&value.source==='https://zse.hr/en/papir/310?isin=HRHT00RA0005';
}
export const fetchListing=(id:string,signal?:AbortSignal)=>request<ListingDetail>('/api/universe/listings/'+encodeURIComponent(id),v=>listing(v)&&object(v)&&Array.isArray(v.versions)&&Array.isArray(v.readiness)&&validClose(v.historical_close),signal);
export const refreshEuropeanClose=()=>request<{state:string;reason:string;normalized_count:number}>('/api/data/sources/A22',v=>object(v)&&typeof v.state==='string'&&typeof v.reason==='string'&&count(v.normalized_count),undefined,{method:'GET'});
export const syncCatalogue=(key:string)=>request<ImportResult>('/api/universe/sync',v=>object(v)&&typeof v.id==='string'&&typeof v.state==='string',undefined,{method:'POST',headers:{'Content-Type':'application/json','X-HQ-Universe':'1','Idempotency-Key':key},body:JSON.stringify({provider:'SEC'})});
