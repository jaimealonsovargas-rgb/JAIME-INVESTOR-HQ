import { useState, type KeyboardEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { decimalText, eur, percent, fetchPortfolio, fetchMarkets, fetchLedger, type Portfolio, type MarketRow } from '../portfolioApi';
import PlayerHud from './PlayerHud';
import MarketSparkline from './MarketSparkline';
import type { PlayerRuntime } from './navigation';
import './financialHud.css';

const STATUS:Record<string,string>={FRESH:'VIGENTE',STALE:'DESACTUALIZADO',NO_DATA:'SIN DATOS',ESTIMATED:'ESTIMADO'};
export const usePortfolio=()=>useQuery({queryKey:['portfolio-master'],queryFn:({signal})=>fetchPortfolio(signal),retry:false,refetchInterval:30000,refetchOnWindowFocus:false});
const time=(value:string)=>new Date(value).toLocaleString('es-ES',{dateStyle:'short',timeStyle:'short'});
function Unavailable({pending=false}:{pending?:boolean}){return <p className="financial-empty" role="status">{pending?'Comprobando el servicio local…':'NO DISPONIBLE · No se puede verificar el backend. Los importes anteriores no se muestran como actuales.'}</p>;}
export function PortfolioMetrics({data,detail=false}:{data:Portfolio;detail?:boolean}){
 return <><p className="rail-eyebrow">MASTER · CAPITAL VIRTUAL <span className={'financial-state state-'+data.valuation_status}>{STATUS[data.valuation_status]}</span></p><div className="nav-value"><small>Patrimonio neto</small><strong>{eur(data.nav_eur)}</strong></div>
 <dl className="financial-metrics"><div><dt>Caja</dt><dd>{eur(data.cash_eur)}</dd></div><div><dt>Invertido</dt><dd>{percent(data.invested_pct)}</dd></div><div><dt>P&L acumulado</dt><dd>{eur(data.total_pnl_eur)}</dd></div><div><dt>Rentabilidad</dt><dd>{percent(data.cumulative_return_pct)}</dd></div><div><dt>Posiciones</dt><dd>{data.positions_count}</dd></div></dl>
 {detail?<dl className="financial-metrics"><div><dt>Valor de mercado</dt><dd>{eur(data.market_value_eur)}</dd></div><div><dt>Realizado</dt><dd>{eur(data.realized_pnl_eur)}</dd></div><div><dt>No realizado</dt><dd>{eur(data.unrealized_pnl_eur)}</dd></div><div><dt>Efecto FX</dt><dd>{eur(data.fx_effect_eur)}</dd></div><div><dt>Ingresos</dt><dd>{eur(data.income_eur)}</dd></div><div><dt>Comisiones separadas</dt><dd>{eur(data.fees_eur)}</dd></div>{(['daily_return_pct','twr_pct','mwr_xirr_pct','max_drawdown_pct'] as const).map((key,i)=><div key={key}><dt>{['Día','TWR','MWR / XIRR','Drawdown máximo'][i]}</dt><dd>{percent(data.performance[key] as string|null)}</dd></div>)}</dl>:null}
 <p className="financial-note">Aportación inicial ≠ beneficio. Las cuentas demo externas están separadas.</p><p className="financial-source">Ledger MASTER verificado · <time dateTime={data.as_of}>{time(data.as_of)}</time></p></>;
}
export function Positions({data,full=false}:{data:Portfolio;full?:boolean}){
 if(!data.positions.length)return <div className="financial-empty"><strong>Sin posiciones</strong><p>{eur(data.cash_eur)} en caja</p><small>Las compras y ventas permanecen bloqueadas. No hay posiciones de ejemplo.</small></div>;
 return <div className="financial-positions">{data.positions.slice(0,full?undefined:5).map(p=><article key={p.instrument}><strong>{p.symbol}</strong><span>{eur(p.market_value_eur)}</span><small>Peso {percent(p.weight_pct)} · P&L {percent(p.pnl_pct)} · {STATUS[p.valuation_status]}</small><small>{p.provenance?.provider??'Sin precio autorizado'} · {p.provenance?.observed_at?time(p.provenance.observed_at):'NO DISPONIBLE'}</small>{full?<small>Cantidad {decimalText(p.qty,6)} · Coste {eur(p.cost_basis_eur)} · {p.currency}</small>:null}</article>)}</div>;
}
function MarketItem({row}:{row:MarketRow}){
 const o=row.observation;
 const labels:Record<string,string>={'EXR.D.USD.EUR.SP00.A':'USD / EUR','CUUR0000SA0':'IPC · EE.UU.','M.N.B.ES':'Índice BIS · España','btc-bitcoin':'BTC · agregado'};
 const change=row.daily_change_pct;
 const historical=o.quality_flags.some(flag=>flag.startsWith('HISTORICAL_'));
 const statusLabel=row.status==='NO_DATA'?STATUS[row.status]:historical?(row.status==='STALE'?'HISTÓRICO CADUCADO':'HISTÓRICO DIARIO'):o.data_kind!=='market_quote'&&row.status==='FRESH'?'REFERENCIA CONSULTADA':STATUS[row.status];
 return <details className="market-row"><summary><span className="market-symbol">{labels[row.symbol]??row.symbol}</span><MarketSparkline history={row.history}/><span className="market-price">{row.status==='NO_DATA'?'NO DISPONIBLE':decimalText(row.value,o.data_kind==='market_quote'?2:4)}<small>{o.unit}</small></span><span className={'market-change '+(change===null?'':change.startsWith('-')?'negative':'positive')} title={row.daily_change_reason} aria-label={change===null?'Sin variación diaria disponible':undefined}>{change===null?'—':percent(change)}</span><span className={'financial-state state-'+row.status}>{statusLabel}</span></summary><div className="market-detail"><p>{row.symbol}<br/>{o.provider} · {o.venue}</p><p>{row.daily_change_reason}</p><p>{row.history?.reason??'Sin histórico comparable.'}</p><p>Observado: {time(o.observed_at)}<br/>Recibido: {time(o.received_at)}<br/>{o.feed} · {o.period_precision}</p><p>{o.rights.attribution}</p><a href={o.source_ref} target="_blank" rel="noopener noreferrer">Fuente original ↗</a></div></details>;
}
const TABS=['Cartera','Posiciones','Actividad','Mapa'] as const;
function tabsKeyboard(e:KeyboardEvent<HTMLDivElement>,selected:string,select:(v:typeof TABS[number])=>void){
 if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
 e.preventDefault();e.stopPropagation();const index=TABS.indexOf(selected as typeof TABS[number]);const next=e.key==='Home'?0:e.key==='End'?3:(index+(e.key==='ArrowRight'?1:3))%4;
 select(TABS[next]);e.currentTarget.querySelectorAll<HTMLButtonElement>('[role=tab]')[next]?.focus();
}

export default function FinancialHud({player,mode}:{player:PlayerRuntime;mode:'play'|'inspection'}){
 const [tab,setTab]=useState<typeof TABS[number]>('Cartera');
 const [left,setLeft]=useState(()=>window.innerWidth>=1280),[right,setRight]=useState(()=>window.innerWidth>=1280);
 const [list,setList]=useState('CORE'),[offset,setOffset]=useState(0);
 const portfolio=usePortfolio();
 const markets=useQuery({queryKey:['markets-watchlist'],queryFn:({signal})=>fetchMarkets(signal),retry:false,refetchInterval:30000,refetchOnWindowFocus:false});
 const ledger=useQuery({queryKey:['portfolio-ledger',offset],queryFn:({signal})=>fetchLedger(signal,offset),enabled:tab==='Actividad',retry:false,refetchInterval:30000,refetchOnWindowFocus:false});
 const data=portfolio.isSuccess&&!portfolio.isError?portfolio.data:undefined;
 return <div className="financial-hud">
 <aside className={'financial-rail rail-left '+(left?'':'rail-collapsed')} aria-label="Watchlist y mercados"><header><h2>Lista</h2><button aria-expanded={left} aria-controls="market-body" onClick={()=>setLeft(!left)} aria-label={left?'Plegar mercados':'Abrir mercados'}>{left?'⌃':'⌄'}</button></header>{left?<div id="market-body" className="rail-body"><label className="watchlist-select">Watchlist<select value={list} onChange={e=>setList(e.target.value)}><option>CORE</option><option>OPPORTUNITIES</option><option>PORTFOLIO</option></select></label>
 {list==='OPPORTUNITIES'?<p className="financial-empty">Aún no hay oportunidades guardadas. El research no añade activos automáticamente.</p>:list==='PORTFOLIO'?(data?<Positions data={data}/>:<Unavailable/>):markets.isError||!markets.data?<Unavailable pending={markets.isPending}/>:<>{markets.data.items.length?markets.data.items.map(r=><MarketItem key={r.observation.id} row={r}/>):<p className="financial-empty">Sin cotizaciones autorizadas disponibles.</p>}<h3 className="rail-section-title">Referencias</h3>{markets.data.pulse.length?markets.data.pulse.map(r=><MarketItem key={r.observation.id} row={r}/>):<p className="financial-empty">Sin referencias autorizadas.</p>}<p className="financial-note">Referencias P2 · No ejecutables. Cada feed conserva su fuente y fecha.</p></>}
 </div>:null}</aside>
 <aside className={'financial-rail rail-right '+(right?'':'rail-collapsed')} aria-label="Cartera y actividad"><header><h2>Capital virtual</h2><button aria-expanded={right} aria-controls="portfolio-body" onClick={()=>setRight(!right)} aria-label={right?'Plegar cartera':'Abrir cartera'}>{right?'⌃':'⌄'}</button></header>{right?<div id="portfolio-body"><div className="rail-tabs" role="tablist" aria-label="Vistas financieras" onKeyDown={e=>tabsKeyboard(e,tab,setTab)}>{TABS.map(t=><button key={t} id={'tab-'+t} role="tab" tabIndex={tab===t?0:-1} aria-selected={tab===t} aria-controls={'view-'+t} onClick={()=>setTab(t)}>{t}</button>)}</div>
 <div className="rail-body" role="tabpanel" id={'view-'+tab} aria-labelledby={'tab-'+tab} tabIndex={0}>
 {tab==='Mapa'?(mode==='play'?<PlayerHud player={player}/>:<p className="financial-empty">Selecciona Recorrer para usar el mapa y los nueve accesos.</p>):tab==='Actividad'?<>{ledger.isError||!ledger.data?<Unavailable pending={ledger.isPending}/>:<><ol className="ledger-activity">{ledger.data.items.map(e=><li key={e.source_ref}><span>{e.kind==='DEPOSIT_VIRTUAL'?'Aportación virtual':e.kind}</span><strong>{decimalText(e.amount)} {e.currency}</strong><time dateTime={e.occurred_at}>{time(e.occurred_at)}</time><small>{e.actor} · {e.source_ref}</small></li>)}</ol>{ledger.data.total>20?<div><button disabled={!offset} onClick={()=>setOffset(Math.max(0,offset-20))}>Anterior</button><button disabled={offset+20>=ledger.data.total} onClick={()=>setOffset(offset+20)}>Siguiente</button></div>:null}</>}<div className="phase-reserved"><strong>ORDERS / FILLS</strong><span>P6 — NO DISPONIBLE</span></div></>:data?(tab==='Cartera'?<PortfolioMetrics data={data}/>:<Positions data={data}/>):<Unavailable pending={portfolio.isPending}/>}
 <button className="resume-office" onClick={()=>document.querySelector('canvas')?.focus()}>Volver al recorrido ↑↓←→</button></div></div>:null}</aside></div>;
}

export function PortfolioDepartment({id}:{id:string}){
 const query=usePortfolio(),[history,setHistory]=useState(false);
 const ledger=useQuery({queryKey:['portfolio-ledger',0],queryFn:({signal})=>fetchLedger(signal),enabled:history,retry:false});
 if(query.isError||!query.data)return <Unavailable pending={query.isPending}/>;
 return <section className="department-portfolio" aria-label="Cartera MASTER"><PortfolioMetrics data={query.data} detail={id==='performance'}/>{id==='trading'?<Positions data={query.data} full/>:null}{id==='performance'?<><p>{query.data.performance.reason}</p><button onClick={()=>setHistory(!history)} aria-expanded={history}>Consultar ledger auditable</button>{history?<div>{ledger.isError||!ledger.data?<Unavailable/>:ledger.data.items.map(e=><p key={e.source_ref}>{e.kind} · {decimalText(e.amount)} {e.currency} · {time(e.occurred_at)}<br/><code>{e.source_ref}</code></p>)}</div>:null}</>:null}</section>;
}
