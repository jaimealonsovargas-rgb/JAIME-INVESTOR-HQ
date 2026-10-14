import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { validateSource, type DataObservation } from '../dataApi';
import './videowall.css';

const TITLES:Record<string,string>={portfolio:'Cartera MASTER',positions:'Posiciones',operations:'Operaciones',markets:'Mercados',news:'Noticias',risk:'Riesgos',agents:'Agentes'};
type Section={section_id:string;phase_required:string;status:string;as_of_utc:string|null;source:string|null;reason:string;value:null;items:DataObservation[]};
async function fetchOverview(signal:AbortSignal):Promise<{checked_at:string;sections:Section[]}>{
 const response=await fetch('/api/hq/overview',{signal:AbortSignal.any([signal,AbortSignal.timeout(6000)]),credentials:'omit',cache:'no-store'});
 if(!response.ok)throw Error('Servicio local no disponible');const value=await response.json();
 if(value.trading_mode!=='PAPER_ONLY'||value.orders_enabled!==false||!Number.isFinite(Date.parse(value.checked_at))||!Array.isArray(value.sections)||value.sections.length!==7)throw Error('Contrato no válido');
 const ids=new Set<string>();
 for(const section of value.sections){
  if(!TITLES[section.section_id]||ids.has(section.section_id)||section.value!==null||!Array.isArray(section.items)||!['AVAILABLE','STALE','NOT_IMPLEMENTED','OFFLINE'].includes(section.status)||typeof section.reason!=='string')throw Error('Sección no válida');ids.add(section.section_id);
  if(!['markets','news'].includes(section.section_id)&&section.items.length)throw Error('Fase futura no habilitada');
  for(const item of section.items)validateSource({access_id:item.access_id,state:'AVAILABLE_VERIFIED',reason:'Cache',checked_at:value.checked_at,real_connection:true,usable:true,cache_hit:true,normalized_count:1,observations:[item]});
 }
 return value;
}
export default function HQVideowall({onPause}:{onPause:(paused:boolean)=>void}){
 const [open,setOpen]=useState(false),dialog=useRef<HTMLDialogElement>(null),button=useRef<HTMLButtonElement>(null);
 const query=useQuery({queryKey:['hq-overview'],queryFn:({signal})=>fetchOverview(signal),retry:false,refetchInterval:30000,refetchOnWindowFocus:false});
 const close=()=>{setOpen(false);onPause(false);button.current?.focus();};
 useEffect(()=>{if(open){dialog.current?.showModal();dialog.current?.querySelector('button')?.focus();}else dialog.current?.close();},[open]);
 return <><div className="videowall-access"><span>SIMULACIÓN · PAPER ONLY</span><button ref={button} onClick={()=>{onPause(true);setOpen(true);}}>Ver centro de control</button></div>
 <dialog ref={dialog} className="hq-dialog" aria-labelledby="hq-title" onCancel={e=>{e.preventDefault();close();}} onKeyDown={e=>{if(e.key!=='Tab')return;const controls=Array.from(e.currentTarget.querySelectorAll<HTMLElement>('button,a[href]')).filter(n=>n.getClientRects().length);const first=controls[0],last=controls.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}}>
 <header><div><h2 id="hq-title">Centro de control</h2><p>SIMULACIÓN · PAPER ONLY · Órdenes bloqueadas</p></div><button onClick={close}>Volver a la oficina · Esc</button></header>
 {query.isError||!query.data?<p role="status">NO DISPONIBLE: {query.isPending?'comprobando el servicio local…':'sin conexión con el backend. Ningún dato se considera en directo.'}</p>:<><p className="hq-time">Comprobación local: <time dateTime={query.data.checked_at}>{new Date(query.data.checked_at).toLocaleString('es-ES')}</time>. Solo lectura; sin consultas externas automáticas.</p><div className="hq-sections">{query.data.sections.map(section=><section key={section.section_id}><h3>{TITLES[section.section_id]}</h3><span className="hq-state">{section.status==='NOT_IMPLEMENTED'?'NO DISPONIBLE':section.status==='STALE'?'DESACTUALIZADO':'REFERENCIA · NO EJECUTABLE'}</span><p>{section.reason}</p>{section.items.map(item=><article key={item.id}><strong>{item.metadata.title??item.series_id}</strong>{item.value!==null?<p>{item.value} <span>{item.unit} {item.currency??''}</span></p>:null}<small>{item.provider} · {item.feed} · {item.venue}<br/>{item.period} · {item.period_precision} · Retraso {(item as DataObservation & {delay_seconds?:number|null}).delay_seconds==null?'desconocido':(item as DataObservation & {delay_seconds?:number|null}).delay_seconds+' s'}<br/>Recibido: {new Date(item.received_at).toLocaleString('es-ES')}<br/>{item.rights.attribution}</small><a href={item.source_ref} target="_blank" rel="noopener noreferrer">Fuente original</a></article>)}</section>)}</div></>}
 </dialog></>;
}
