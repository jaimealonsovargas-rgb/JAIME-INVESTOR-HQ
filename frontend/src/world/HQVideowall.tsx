import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { validateSource, type DataObservation } from '../dataApi';
import { eur,percent,nullableDecimal } from '../portfolioApi';
import './videowall.css';

export const HQ_TITLES:Record<string,string>={portfolio:'Cartera MASTER',positions:'Posiciones',operations:'Operaciones',markets:'Mercados',news:'Noticias',risk:'Riesgos',committee:'Comité',agents:'Agentes',systems:'Sistemas'};
const COUNTS:Record<string,string>={candidate_providers:'Proveedores candidatos',candidate_access_modes:'Modalidades candidatas',implemented_adapters:'Adaptadores implementados',verified_connections:'Conexiones reales verificadas',usable_sources:'Fuentes utilizables ahora',no_credentials:'Sin credenciales',rights_restricted:'Derechos restringidos'};
export type ExecutiveValue={nav_eur?:string|null;cash_eur?:string|null;cumulative_return_pct?:string|null;valuation_status?:string;performance?:Record<string,string|number|null>;positions_count?:number;market_value_eur?:string|null;invested_pct?:string|null;positions?:unknown[]};
type Section={section_id:string;phase_required:string;status:string;as_of_utc:string|null;source:string|null;reason:string;value:ExecutiveValue|null;quality:Record<string,number|string>;rights:string|null;items:DataObservation[]};
export interface HQOverviewData {checked_at:string;sections:Section[]}
export function validateOverview(value:unknown):HQOverviewData{
 if(typeof value!=='object'||!value)throw Error('Contrato no válido');const data=value as Record<string,unknown>;
 if(data.trading_mode!=='PAPER_ONLY'||data.orders_enabled!==false||typeof data.checked_at!=='string'||!Number.isFinite(Date.parse(data.checked_at))||!Array.isArray(data.sections)||data.sections.length!==9)throw Error('Contrato no válido');
 const ids=new Set<string>();
 for(const section of data.sections as Section[]){
  if(!HQ_TITLES[section.section_id]||ids.has(section.section_id)||!Array.isArray(section.items)||!['AVAILABLE','STALE','NOT_IMPLEMENTED','OFFLINE'].includes(section.status)||typeof section.reason!=='string'||typeof section.quality!=='object'||!section.quality)throw Error('Sección no válida');ids.add(section.section_id);
  if(!['markets','news','systems','portfolio','positions'].includes(section.section_id)&&(section.items.length||section.status!=='NOT_IMPLEMENTED'||section.value!==null))throw Error('Fase futura no habilitada');
  if(section.value!==null){
   if(!['portfolio','positions'].includes(section.section_id)||typeof section.value!=='object'||section.phase_required!=='P3'||!section.source?.startsWith('Ledger MASTER local')||!section.as_of_utc||!Number.isFinite(Date.parse(section.as_of_utc)))throw Error('Capital sin ledger.');
   if(section.section_id==='portfolio'&&(!nullableDecimal(section.value.nav_eur)||!nullableDecimal(section.value.cash_eur)||!nullableDecimal(section.value.cumulative_return_pct)))throw Error('Importe P3 inválido.');
   if(section.section_id==='positions'&&(!Number.isInteger(section.value.positions_count)||!nullableDecimal(section.value.market_value_eur)||!nullableDecimal(section.value.invested_pct)||!Array.isArray(section.value.positions)||section.value.positions.length!==section.value.positions_count))throw Error('Posiciones P3 inválidas.');
  }else if(['portfolio','positions'].includes(section.section_id)&&section.status==='AVAILABLE')throw Error('Cartera sin datos.');
  for(const item of section.items)validateSource({access_id:(item as DataObservation & {access_id:string}).access_id,state:'AVAILABLE_VERIFIED',reason:'Cache',checked_at:data.checked_at,real_connection:true,usable:true,cache_hit:true,normalized_count:1,observations:[item]});
 }
 return data as unknown as HQOverviewData;
}
export function ExecutiveSummary({id,value}:{id:string;value:ExecutiveValue}){
 return id==='portfolio'?<dl className="hq-counts"><div><dt>NAV · virtual</dt><dd>{eur(value.nav_eur)}</dd></div><div><dt>Caja</dt><dd>{eur(value.cash_eur)}</dd></div><div><dt>Rentabilidad</dt><dd>{percent(value.cumulative_return_pct)}</dd></div><div><dt>Performance</dt><dd>{value.performance?.twr_pct==null?'Historia insuficiente':percent(value.performance.twr_pct as string)}</dd></div></dl>:<dl className="hq-counts"><div><dt>Posiciones</dt><dd>{value.positions_count}</dd></div><div><dt>Valor de mercado</dt><dd>{eur(value.market_value_eur)}</dd></div><div><dt>Exposición</dt><dd>{percent(value.invested_pct)}</dd></div></dl>;
}
async function fetchOverview(signal:AbortSignal):Promise<HQOverviewData>{
 const response=await fetch('/api/hq/overview',{signal:AbortSignal.any([signal,AbortSignal.timeout(6000)]),credentials:'omit',cache:'no-store'});
 if(!response.ok)throw Error('Servicio local no disponible');return validateOverview(await response.json());
}
export default function HQVideowall({onPause,onOverview}:{onPause:(paused:boolean)=>void;onOverview:(data:HQOverviewData|undefined)=>void}){
 const [open,setOpen]=useState(false),dialog=useRef<HTMLDialogElement>(null),button=useRef<HTMLButtonElement>(null);
 const query=useQuery({queryKey:['hq-overview'],queryFn:({signal})=>fetchOverview(signal),retry:false,refetchInterval:30000,refetchOnWindowFocus:false});
 useEffect(()=>{onOverview(query.isSuccess&&!query.isError?query.data:undefined);},[query.data,query.isSuccess,query.isError,onOverview]);
 const close=()=>{setOpen(false);onPause(false);};
 useEffect(()=>{const node=dialog.current;if(open){node?.showModal();node?.querySelector('button')?.focus();}else if(node?.open){node.close();(document.querySelector('canvas')??button.current)?.focus();}},[open]);
 return <><div className="videowall-access"><span>SIMULACIÓN · PAPER ONLY</span><button ref={button} onClick={()=>{onPause(true);setOpen(true);}}>Ver centro de control</button></div>
 <dialog ref={dialog} className="hq-dialog" aria-labelledby="hq-title" onCancel={e=>{e.preventDefault();close();}} onKeyDown={e=>{if(e.key!=='Tab')return;const controls=Array.from(e.currentTarget.querySelectorAll<HTMLElement>('button,a[href]')).filter(n=>n.getClientRects().length);const first=controls[0],last=controls.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}}>
 <header><div><h2 id="hq-title">Centro de control</h2><p>SIMULACIÓN · PAPER ONLY · Órdenes bloqueadas</p></div><button onClick={close}>Volver a la oficina · Esc</button></header>
 {query.isError||!query.data?<p role="status">NO DISPONIBLE: {query.isPending?'comprobando el servicio local…':'sin conexión con el backend. Ningún dato se considera en directo.'}</p>:<><p className="hq-time">Comprobación local: <time dateTime={query.data.checked_at}>{new Date(query.data.checked_at).toLocaleString('es-ES')}</time>. Solo lectura; sin consultas externas automáticas.</p><div className="hq-sections">{query.data.sections.map(section=><section key={section.section_id} data-section={section.section_id}><h3>{HQ_TITLES[section.section_id]}</h3><span className="hq-state">{section.status==='NOT_IMPLEMENTED'?'NO DISPONIBLE':section.status==='STALE'?'DESACTUALIZADO':section.value?'LEDGER MASTER · VIRTUAL':section.section_id==='systems'?'ESTADO LOCAL':'REFERENCIA · NO EJECUTABLE'}</span><p>{section.reason}</p>{section.value?<ExecutiveSummary id={section.section_id} value={section.value}/>:null}{section.section_id==='systems'?<dl className="hq-counts">{Object.entries(COUNTS).map(([key,label])=><div key={key}><dt>{label}</dt><dd>{section.quality[key]??'NO DISPONIBLE'}</dd></div>)}</dl>:null}<div className="hq-items">{section.items.map(item=><article key={item.id}><strong>{item.metadata.title??item.series_id}</strong>{item.value!==null?<p>{item.value} <span>{item.unit}{item.currency&&!item.unit.includes(item.currency)?' · '+item.currency:''}</span></p>:null}<small>{item.metadata.title?<>{item.metadata.publisher??item.provider} · Autor: {item.metadata.author||'No informado'} · Idioma: {item.metadata.language??'No informado'}<br/>{item.metadata.confirmation}<br/></>:null}{item.provider} · {item.feed} · {item.venue}<br/>{item.period} · {item.period_precision} · Retraso {(item as DataObservation & {delay_seconds?:number|null}).delay_seconds==null?'desconocido':(item as DataObservation & {delay_seconds?:number|null}).delay_seconds+' s'}<br/>Recibido: {new Date(item.received_at).toLocaleString('es-ES')}<br/>{item.rights.attribution}</small><a href={item.source_ref} target="_blank" rel="noopener noreferrer">Fuente original</a></article>)}</div></section>)}</div></>}
 </dialog></>;
}
