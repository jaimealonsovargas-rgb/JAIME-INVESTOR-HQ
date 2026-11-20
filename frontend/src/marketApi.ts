export type Adjustment = 'raw' | 'split' | 'all';
export type MarketJobKind = 'connection' | 'catalogue' | 'snapshot' | 'history';
export interface MarketJob {
  id:string;kind:MarketJobKind;state:string;created_at:string;updated_at:string;reason:string;
  progress:{pages:number;bars:number};listing_id:string|null;
}
export interface MarketRequest {kind:MarketJobKind;listing_id?:string;start?:string;end?:string;adjustment?:Adjustment}
export interface PaperAccount {currency:string;status:string;cash:string;equity:string;buying_power:string}
export interface PaperPosition {symbol:string;qty:string;market_value:string}
export interface MarketSummary {
  source:{state:string;reason:string;feed:'iex';mode:'PAPER_READ_ONLY'};
  endpoints:{id:string;label:string;state:string;checked_at:string|null;reason:string}[];
  counts:{assets:number;bar_sets:number;bars:number};jobs:MarketJob[];
  paper:{state:string;as_of:string|null;account:PaperAccount|null;positions:PaperPosition[];positions_complete?:boolean};
}
export interface MarketBar {t:string;o:string;h:string;l:string;c:string;v:string}
export interface ObservedContract {
  source:'IBKR_TWS';con_id:number;symbol:string;currency:string;primary_exchange:string;routing_exchange:string;
  observed_at:string;known_from:string;report_sha256:string;documentation_url:string;
  scope:'OBSERVED_CONTRACT_ONLY';historical_identity:false;
}
export interface DatasetAssessment {
  policy:string;family:string;as_of:string;manifest_id:string;research_state:'EXPLORATORY_ONLY'|'INSUFFICIENT_DATA';backtest_state:'BLOCKED';
  identity:{state:'DOCUMENTED'|'UNREVIEWED'|'REVIEW_REQUIRED';reason:string;cik:string|null;security_title:string|null;known_from:string|null;market_listing_id:string|null;
    native_currency:string|null;native_currency_state:'UNVERIFIED'|'DOCUMENTED_OBSERVATION';native_currency_reason:string;current_contract:ObservedContract|null;
    evidence:{kind:string;id:string;url:string;sha256:string;received_at:string}[]};
  dataset:{sessions:number;expected_sessions:number|null;price_currency:string}|null;
  checks:{code:string;state:'PASS'|'WARN'|'BLOCKED';label:string;detail:string}[];
}
export interface BarManifest {
  id:string;start:string;end:string;adjustment:Adjustment;feed:string;state:string;bars:number;
  first_at:string|null;last_at:string|null;received_at:string;missing_sessions:number|null;
  expected_sessions:number|null;coverage_note:string;
}
export interface InstrumentMarketData {
  assessment?:DatasetAssessment;
  listing_id:string;
  identity:{state:string;reason:string;asset_id:string|null;symbol:string;venue:string;currency:string|null;issuer_link:string;
    candidates:{id:string;name:string;symbol:string;venue:string;reason:string}[]};
  quote:{state:string;as_of:string|null;received_at:string|null;feed:string;price:string|null;bid:string|null;ask:string|null;
    reason:string;quote_at?:string|null;market_state:'OPEN'|'CLOSED'|'UNKNOWN';market_checked_at:string|null};
  history:{series:MarketBar[];manifest:BarManifest|null;sets:BarManifest[]};
}

const object=(v:unknown):v is Record<string,unknown>=>typeof v==='object'&&v!==null&&!Array.isArray(v);
const text=(v:unknown):v is string=>typeof v==='string';
const count=(v:unknown)=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0;
const decimal=(v:unknown)=>text(v)&&/^-?\d+(?:\.\d+)?$/.test(v)&&Number.isFinite(Number(v));
const numeric=(v:unknown)=>decimal(v)&&Number(v)>=0;
const time=(v:unknown):v is string=>text(v)&&Number.isFinite(Date.parse(v));
const hash=(v:unknown)=>text(v)&&/^[a-f0-9]{64}$/.test(v);
const maybe=(valid:(v:unknown)=>boolean)=>(v:unknown)=>v===null||valid(v);
const strings=(v:Record<string,unknown>,keys:string[])=>keys.every(k=>text(v[k]));
const validJob=(v:unknown)=>object(v)&&strings(v,['id','kind','state','reason'])&&time(v.created_at)&&time(v.updated_at)
  &&object(v.progress)&&count(v.progress.pages)&&count(v.progress.bars)&&maybe(text)(v.listing_id);
const validAccount=(v:unknown)=>object(v)&&strings(v,['currency','status'])&&['cash','equity','buying_power'].every(k=>decimal(v[k]));
const validManifest=(v:unknown)=>object(v)&&strings(v,['id','start','end','feed','state','coverage_note'])
  &&['raw','split','all'].includes(v.adjustment as string)&&count(v.bars)&&time(v.received_at)
  &&maybe(time)(v.first_at)&&maybe(time)(v.last_at)&&maybe(count)(v.missing_sessions)&&maybe(count)(v.expected_sessions);
const validBar=(v:unknown)=>object(v)&&time(v.t)&&['o','h','l','c','v'].every(k=>numeric(v[k]))
  &&Number(v.l)<=Math.min(Number(v.o),Number(v.c))&&Number(v.h)>=Math.max(Number(v.o),Number(v.c));
const evidenceUrl=(v:unknown)=>{if(!text(v))return false;try{const u=new URL(v);return u.protocol==='https:'&&!u.username&&!u.password&&['www.sec.gov','data.sec.gov','paper-api.alpaca.markets','data.alpaca.markets'].includes(u.hostname);}catch{return false;}};
const validContract=(identity:Record<string,unknown>,asOf:string)=>{
  const c=identity.current_contract;
  if(!text(identity.native_currency_reason))return false;
  if(identity.native_currency_state==='UNVERIFIED')return c===null&&identity.native_currency===null;
  return identity.state==='DOCUMENTED'&&identity.native_currency_state==='DOCUMENTED_OBSERVATION'
    &&object(c)&&c.source==='IBKR_TWS'&&count(c.con_id)&&(c.con_id as number)>0&&text(c.symbol)&&c.symbol.length>0
    &&c.currency==='USD'&&identity.native_currency===c.currency&&c.primary_exchange==='NASDAQ'&&c.routing_exchange==='SMART'
    &&c.scope==='OBSERVED_CONTRACT_ONLY'&&c.historical_identity===false&&hash(c.report_sha256)
    &&c.documentation_url==='https://www.interactivebrokers.com/docs/tws-api/doc/contracts/object'
    &&time(c.observed_at)&&time(c.known_from)&&time(identity.known_from)
    &&Date.parse(c.observed_at)<=Date.parse(c.known_from)&&Date.parse(identity.known_from)<=Date.parse(c.known_from)&&Date.parse(c.known_from)<=Date.parse(asOf);
};
export const validAssessment=(v:unknown)=>object(v)&&strings(v,['policy','family'])&&hash(v.manifest_id)&&time(v.as_of)
  &&['EXPLORATORY_ONLY','INSUFFICIENT_DATA'].includes(v.research_state as string)&&v.backtest_state==='BLOCKED'
  &&object(v.identity)&&['DOCUMENTED','UNREVIEWED','REVIEW_REQUIRED'].includes(v.identity.state as string)&&text(v.identity.reason)
  &&validContract(v.identity,v.as_of)
  &&['cik','security_title','market_listing_id'].every(k=>maybe(text)((v.identity as Record<string,unknown>)[k]))&&maybe(time)(v.identity.known_from)
  &&Array.isArray(v.identity.evidence)&&v.identity.evidence.every(e=>object(e)&&strings(e,['kind','id'])&&hash(e.sha256)&&evidenceUrl(e.url)&&time(e.received_at)&&Date.parse(e.received_at)<=Date.parse(v.as_of as string))
  &&(v.identity.state!=='DOCUMENTED'||(text(v.identity.cik)&&/^\d{10}$/.test(v.identity.cik)&&text(v.identity.security_title)&&v.identity.security_title.length>0&&hash(v.identity.market_listing_id)&&time(v.identity.known_from)&&Date.parse(v.identity.known_from)<=Date.parse(v.as_of as string)&&v.identity.evidence.some(e=>object(e)&&e.kind==='SEC_COMMON_STOCK_COVER')))
  &&maybe(d=>object(d)&&count(d.sessions)&&maybe(count)(d.expected_sessions)&&text(d.price_currency))(v.dataset)
  &&Array.isArray(v.checks)&&v.checks.every(c=>object(c)&&strings(c,['code','label','detail'])&&['PASS','WARN','BLOCKED'].includes(c.state as string));
const validSummary=(v:unknown)=>object(v)&&object(v.source)&&strings(v.source,['state','reason'])
  &&v.source.feed==='iex'&&v.source.mode==='PAPER_READ_ONLY'&&object(v.counts)
  &&['assets','bar_sets','bars'].every(k=>count((v.counts as Record<string,unknown>)[k]))
  &&Array.isArray(v.endpoints)&&v.endpoints.every(e=>object(e)&&strings(e,['id','label','state','reason'])&&maybe(time)(e.checked_at))
  &&Array.isArray(v.jobs)&&v.jobs.every(validJob)&&object(v.paper)&&text(v.paper.state)&&maybe(time)(v.paper.as_of)
  &&maybe(validAccount)(v.paper.account)&&Array.isArray(v.paper.positions)
  &&v.paper.positions.every(p=>object(p)&&text(p.symbol)&&decimal(p.qty)&&decimal(p.market_value));
const validInstrument=(v:unknown)=>object(v)&&(v.assessment===undefined||validAssessment(v.assessment))&&text(v.listing_id)&&object(v.identity)
  &&strings(v.identity,['state','reason','symbol','venue','issuer_link'])&&maybe(text)(v.identity.asset_id)&&maybe(text)(v.identity.currency)
  &&Array.isArray(v.identity.candidates)&&v.identity.candidates.every(c=>object(c)&&strings(c,['id','name','symbol','venue','reason']))
  &&object(v.quote)&&strings(v.quote,['state','feed','reason'])&&['OPEN','CLOSED','UNKNOWN'].includes(v.quote.market_state as string)
  &&['as_of','received_at','market_checked_at'].every(k=>maybe(time)((v.quote as Record<string,unknown>)[k]))
  &&['price','bid','ask'].every(k=>maybe(numeric)((v.quote as Record<string,unknown>)[k]))
  &&object(v.history)&&Array.isArray(v.history.series)&&v.history.series.every(validBar)
  &&maybe(validManifest)(v.history.manifest)&&Array.isArray(v.history.sets)&&v.history.sets.every(validManifest);

async function request<T>(url:string,valid:(v:unknown)=>boolean,signal?:AbortSignal,init?:RequestInit):Promise<T>{
  const timeout=AbortSignal.timeout(20000);
  const response=await fetch(url,{credentials:'omit',cache:'no-store',...init,signal:signal?AbortSignal.any([signal,timeout]):timeout});
  if(!response.ok)throw new Error(response.status===409?'Ya hay una captación en curso o el instrumento necesita revisión. Consulta su estado antes de reintentar.':response.status===403?'La fuente está desactivada o su acceso está restringido. Revisa la configuración local.':'No se pudo consultar el servicio de mercado. Comprueba el backend y vuelve a intentarlo.');
  const data:unknown=await response.json();
  if(!valid(data))throw new Error('La respuesta de mercado no es válida. No se mostrarán precios ni cobertura sin comprobar.');
  return data as T;
}

export const fetchMarketSummary=(signal?:AbortSignal)=>request<MarketSummary>('/api/universe/market/summary',validSummary,signal);
export const fetchInstrumentMarket=(id:string,adjustment:Adjustment,signal?:AbortSignal)=>request<InstrumentMarketData>('/api/universe/listings/'+encodeURIComponent(id)+'/market?adjustment='+adjustment,validInstrument,signal);
export const startMarketJob=(key:string,body:MarketRequest)=>request<MarketJob>('/api/universe/market/jobs',validJob,undefined,{method:'POST',headers:{'Content-Type':'application/json','X-HQ-Universe':'1','Idempotency-Key':key},body:JSON.stringify(body)});
export const controlMarketJob=(id:string,action:'cancel'|'resume')=>request<MarketJob>('/api/universe/market/jobs/'+encodeURIComponent(id)+'/control',validJob,undefined,{method:'POST',headers:{'Content-Type':'application/json','X-HQ-Universe':'1'},body:JSON.stringify({action})});
export const marketTime=(value:string|null)=>value&&time(value)?new Intl.DateTimeFormat('es-ES',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Madrid'}).format(new Date(value))+' · Madrid':'Sin observación';
export const marketNumber=(value:string|null,unit='')=>value===null?'No disponible':decimal(value)?new Intl.NumberFormat('es-ES',{maximumFractionDigits:4,minimumFractionDigits:unit?2:0}).format(Number(value))+(unit?' '+unit:''):'Dato no válido';
