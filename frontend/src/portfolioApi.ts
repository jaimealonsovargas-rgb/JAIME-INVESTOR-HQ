import { validateSource, type DataObservation } from './dataApi';

export type ValuationStatus='FRESH'|'STALE'|'NO_DATA'|'ESTIMATED';
export interface Position {instrument:string;symbol:string;currency:string;qty:string;cost_basis_eur:string;price:string|null;market_value_eur:string|null;unrealized_pnl_eur:string|null;pnl_pct:string|null;weight_pct:string|null;valuation_status:ValuationStatus;provenance:DataObservation|null}
export interface Portfolio {portfolio_id:'MASTER';base_currency:'EUR';trading_mode:'PAPER_ONLY';orders_enabled:false;as_of:string;seeded_at:string;ledger_hash:string;ledger_status:string;valuation_status:ValuationStatus;nav_eur:string|null;cash_eur:string|null;market_value_eur:string|null;liabilities_eur:string;accruals_eur:string|null;positions_count:number;events_count:number;invested_pct:string|null;realized_pnl_eur:string;unrealized_pnl_eur:string|null;fx_effect_eur:string|null;total_pnl_eur:string|null;cumulative_return_pct:string|null;income_eur:string;fees_eur:string;positions:Position[];performance:Record<string,string|number|null>}
export interface LedgerRow {kind:string;source_ref:string;occurred_at:string;amount:string;currency:string;actor:string;entries:{account:string;currency:string;debit:string;credit:string}[]}
export interface LedgerPage {items:LedgerRow[];total:number;offset:number;limit:number;ledger_hash:string}
export interface MarketHistory {state:'AVAILABLE'|'STALE'|'NO_DATA';reason:string;identity:Record<string,string|null>;points:{observed_at:string;value:string;observation_id:string}[]}
export interface MarketRow {history?:MarketHistory;symbol:string;name:string;value:string|null;daily_change_pct:string|null;daily_change_reason:string;status:ValuationStatus;observation:DataObservation}
export interface Markets {checked_at:string;items:MarketRow[];pulse:MarketRow[];reason:string}
export const isDecimal=(v:unknown):v is string=>typeof v==='string'&&/^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(v)&&v.length<=150;
export const nullableDecimal=(v:unknown)=>v===null||isDecimal(v);
const record=(v:unknown):v is Record<string,unknown>=>typeof v==='object'&&v!==null&&!Array.isArray(v);
const validTime=(v:unknown)=>typeof v==='string'&&Number.isFinite(Date.parse(v));
const validStatus=(v:unknown)=>['FRESH','STALE','NO_DATA','ESTIMATED'].includes(String(v));

/** Decimal formatting only: no Number/parseFloat conversion of financial values. */
export function decimalText(value:string|null|undefined, places=2):string {
 if(value==null||!isDecimal(value))return 'NO DISPONIBLE';
 const [mantissa,exponent='0']=value.toLowerCase().split('e');
 const negative=mantissa.startsWith('-'),[whole,fraction='']=mantissa.replace('-','').split('.');
 const shift=Number(exponent); // exponent is a formatting index, not a financial value
 if(Math.abs(shift)>100)return value;
 const digits=whole+fraction,point=whole.length+shift;
 const expanded=point<=0?'0.'+'0'.repeat(-point)+digits:point>=digits.length?digits+'0'.repeat(point-digits.length):digits.slice(0,point)+'.'+digits.slice(point);
 const [integer,tail='']=expanded.split('.');
 let units=BigInt(integer+tail.padEnd(places,'0').slice(0,places));
 const discarded=tail.slice(places),first=discarded[0]??'0';
 if(first>'5'||(first==='5'&&(/[1-9]/.test(discarded.slice(1))||units%2n===1n)))units++;
 const result=units.toString().padStart(places+1,'0');
 const major=places?result.slice(0,-places):result;
 return (negative&&units!==0n?'−':'')+major.replace(/\B(?=(\d{3})+(?!\d))/g,'.')+(places?','+result.slice(-places):'');
}
export const eur=(value:string|null|undefined)=>value==null?'NO DISPONIBLE':decimalText(value)+' €';
export const percent=(value:string|null|undefined)=>value==null?'NO DISPONIBLE':decimalText(value)+' %';

export function validatePortfolio(value:unknown):Portfolio {
 if(!record(value)||value.portfolio_id!=='MASTER'||value.base_currency!=='EUR'||value.trading_mode!=='PAPER_ONLY'||value.orders_enabled!==false||!validTime(value.as_of)||!validTime(value.seeded_at)||!validStatus(value.valuation_status)||value.ledger_status!=='VERIFIED_APPEND_ONLY'||typeof value.ledger_hash!=='string'||!/^[0-9a-f]{64}$/.test(value.ledger_hash))throw Error('Cartera sin contrato verificable.');
 for(const key of ['nav_eur','cash_eur','market_value_eur','liabilities_eur','accruals_eur','invested_pct','realized_pnl_eur','unrealized_pnl_eur','fx_effect_eur','total_pnl_eur','cumulative_return_pct','income_eur','fees_eur'])if(!nullableDecimal(value[key]))throw Error('Importe sin precisión Decimal.');
 if(!Number.isInteger(value.positions_count)||!Number.isInteger(value.events_count)||!Array.isArray(value.positions)||value.positions.length!==value.positions_count||!record(value.performance))throw Error('Cartera inconsistente.');
 for(const p of value.positions){if(!record(p)||typeof p.symbol!=='string'||typeof p.instrument!=='string'||!isDecimal(p.qty)||!validStatus(p.valuation_status)||!['cost_basis_eur','price','market_value_eur','unrealized_pnl_eur','pnl_pct','weight_pct'].every(k=>nullableDecimal(p[k])))throw Error('Posición inválida.');}
 for(const key of ['daily_return_pct','twr_pct','mwr_xirr_pct','max_drawdown_pct'])if(!nullableDecimal(value.performance[key]))throw Error('Métrica no válida.');
 return value as unknown as Portfolio;
}
export function validateMarkets(value:unknown):Markets {
 if(!record(value)||!validTime(value.checked_at)||!Array.isArray(value.items)||!Array.isArray(value.pulse)||typeof value.reason!=='string')throw Error('Mercados sin contrato.');
 for(const row of [...value.items,...value.pulse]){
  if(!record(row)||typeof row.symbol!=='string'||!nullableDecimal(row.value)||!nullableDecimal(row.daily_change_pct)||!validStatus(row.status)||!record(row.observation))throw Error('Fila de mercado inválida.');
  const observation=row.observation;
  if(row.history!==undefined){const h=row.history as MarketHistory;if(!record(h)||!['AVAILABLE','STALE','NO_DATA'].includes(h.state)||!Array.isArray(h.points)||h.points.length>60||!record(h.identity)||!['provider','feed','series_id','venue','currency','unit','period_precision','data_kind'].every(k=>h.identity[k]===observation[k])||h.points.some((p,i)=>!validTime(p.observed_at)||!isDecimal(p.value)||typeof p.observation_id!=='string'||(i>0&&p.observed_at<=h.points[i-1].observed_at))||(h.state==='NO_DATA'?h.points.length!==0:h.points.length<3))throw Error('Historia no comparable.');}
  validateSource({access_id:row.observation.access_id,state:'AVAILABLE_VERIFIED',reason:'Cache P2',checked_at:value.checked_at,real_connection:true,usable:false,cache_hit:true,normalized_count:1,observations:[row.observation]});
 }
 return value as unknown as Markets;
}
export function validateLedger(value:unknown):LedgerPage {
 if(!record(value)||!Array.isArray(value.items)||!Number.isInteger(value.total)||!Number.isInteger(value.offset))throw Error('Ledger no válido.');
 for(const e of value.items)if(!record(e)||!validTime(e.occurred_at)||typeof e.kind!=='string'||!isDecimal(e.amount)||!Array.isArray(e.entries)||e.entries.some(p=>!isDecimal(p.debit)||!isDecimal(p.credit)))throw Error('Asiento no válido.');
 return value as unknown as LedgerPage;
}
async function get(path:string,signal:AbortSignal){const response=await fetch(path,{signal:AbortSignal.any([signal,AbortSignal.timeout(6000)]),credentials:'omit',cache:'no-store'});if(!response.ok)throw Error('Servicio local no disponible.');return response.json();}
export const fetchPortfolio=async(signal:AbortSignal)=>validatePortfolio(await get('/api/portfolio/master/summary',signal));
export const fetchMarkets=async(signal:AbortSignal)=>validateMarkets(await get('/api/markets/watchlist',signal));
export const fetchLedger=async(signal:AbortSignal,offset=0)=>validateLedger(await get('/api/portfolio/master/ledger?limit=20&offset='+offset,signal));
