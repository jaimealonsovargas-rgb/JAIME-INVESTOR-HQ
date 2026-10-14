import { useEffect,useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth,fetchProviders,type Health } from '../api';
import { DEPARTMENTS } from './layout';
import { MONITOR_DEFINITIONS } from './terminals';
import { PANEL_CONTENT } from './panels';
import './panels.css';

type Status='available'|'no-data'|'stale'|'offline'|'blocked'|'pending'|'error'|'phase-locked';
const LABELS:Record<Status,string>={available:'Disponible', 'no-data':'Sin datos',stale:'Desactualizado',offline:'Sin conexión',blocked:'Bloqueado',pending:'Comprobando',error:'Error','phase-locked':'NO DISPONIBLE'};
export function StatusBadge({status,children}:{status:Status;children?:React.ReactNode}) {return <span className={`status-badge status-${status}`}>{children??LABELS[status]}</span>;}
export function UnavailableState({message,phase}:{message:string;phase:string}) {return <div className="unavailable-state"><svg viewBox="0 0 48 48" width="42" height="42" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.3"><rect x="9" y="6" width="30" height="36" rx="2"/><path d="M16 16h16M16 23h16M16 30h9"/></svg><h3>{message}</h3><p>Este terminal está preparado. Los datos y funciones se habilitarán en {phase}, con fuentes verificadas.</p></div>;}
export function DataTableShell({columns,message,phase}:{columns:string[];message:string;phase:string}) {return <><div className="data-table-wrap"><table><caption className="sr-only">Estructura de datos prevista; sin registros disponibles</caption><thead><tr>{columns.map(c=><th key={c} scope="col">{c}</th>)}</tr></thead><tbody><tr><td colSpan={columns.length}><UnavailableState message={message} phase={phase}/></td></tr></tbody></table></div><p className="table-note">Sin filas de ejemplo. Ausencia de datos no significa un saldo o rendimiento igual a cero.</p></>;}
export function SectionCard({title,detail}:{title:string;detail:string}) {return <section className="panel-section"><h3>{title}</h3><p>{detail}</p></section>;}
function HealthDetail({health}:{health:Health}) {return <dl className="health-grid"><div><dt>Servicio local</dt><dd>Operativo <StatusBadge status="available"/></dd></div><div><dt>Base de datos</dt><dd>{health.database==='ok'?'Comprobación correcta':'NO DISPONIBLE'}</dd></div><div><dt>Modo de trading</dt><dd>{health.trading_mode}</dd></div><div><dt>Órdenes</dt><dd>Deshabilitadas <StatusBadge status="blocked"/></dd></div><div><dt>Esquema</dt><dd>{health.schema_version}</dd></div><div><dt>Fuente / comprobación</dt><dd>GET /health<br/><time dateTime={health.checked_at}>{new Date(health.checked_at).toLocaleString('es-ES')}</time></dd></div></dl>;}

function containTabFocus(event: React.KeyboardEvent<HTMLDialogElement>) {
 if(event.key!=='Tab')return;
 const dialog=event.currentTarget;
 const items=Array.from(dialog.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')).filter(item=>item.getClientRects().length>0);
 const first=items[0],last=items.at(-1),active=document.activeElement;
 if(!first){event.preventDefault();dialog.focus();return;}
 if(!dialog.contains(active)||(event.shiftKey?active===first:active===last)){event.preventDefault();(event.shiftKey?last!:first).focus();}
}

export default function MonitorOverlay({id,onClose}:{id:string;onClose:()=>void}) {
 const dialog=useRef<HTMLDialogElement>(null),close=useRef<HTMLButtonElement>(null);
 const monitor=MONITOR_DEFINITIONS.find(m=>m.id===id)!;const content=PANEL_CONTENT[id];const live=id==='systems'||id==='reception';
 const health=useQuery({queryKey:['health'],queryFn:({signal})=>fetchHealth(signal),retry:false,refetchInterval:15000,enabled:live});
 const providers=useQuery({queryKey:['providers'],queryFn:({signal})=>fetchProviders(signal),retry:false,refetchInterval:15000,enabled:id==='systems'});
 useEffect(()=>{const previous=document.activeElement as HTMLElement|null;const node=dialog.current!;node.showModal();close.current?.focus();return()=>{node.close();if(previous?.isConnected)previous.focus();};},[]);
 const healthy=health.isSuccess&&!health.isError;const stale=healthy&&Date.now()-Date.parse(health.data.checked_at)>60000;
 return <dialog ref={dialog} className="monitor-dialog" aria-modal="true" aria-labelledby="panel-title" aria-describedby="panel-description" onKeyDown={containTabFocus} onCancel={e=>{e.preventDefault();onClose();}}>
  <div className="panel-chrome"><span>JAIME INVESTOR HQ <span className="chrome-divider">/</span> {monitor.label}</span><button ref={close} onClick={onClose}>Volver a la oficina <kbd>Esc</kbd></button></div>
  <header className="panel-header"><div><h2 id="panel-title">{monitor.panel}</h2><p id="panel-description">{content.description}</p></div><div className="panel-status"><StatusBadge status={live?(health.isPending?'pending':health.isError?'offline':stale?'stale':'available'):'phase-locked'}>{live?undefined:`NO DISPONIBLE · ${monitor.phase}`}</StatusBadge><span>PAPER ONLY</span></div></header>
  <div className="panel-body">
   {live?<section className="panel-health" aria-label="Salud real del backend"><div className="section-heading"><h3>Servicio local</h3><button onClick={()=>{void health.refetch();if(id==='systems')void providers.refetch();}} disabled={health.isFetching}>{health.isFetching?'Comprobando…':'Actualizar estado'}</button></div>{healthy?<><HealthDetail health={health.data}/>{stale?<p className="panel-error" role="status">Respuesta desactualizada; no confirma el estado actual del servicio.</p>:null}</>:<p className="panel-error" role="status">{health.isPending?'Comprobando GET /health…':'NO DISPONIBLE: no se pudo verificar el backend. Puedes cerrar el panel y seguir recorriendo la oficina.'}</p>}</section>:null}
   {id==='reception'?<section className="panel-map"><h3>Nueve departamentos, una planta</h3><ol>{DEPARTMENTS.map(d=><li key={d.id}><span>{d.number}</span><strong>{d.label}</strong><small>{d.use}</small></li>)}</ol><p>El minimapa permite volver a cualquier departamento desde el mundo. NAV y caja: sin datos — P3.</p></section>:null}
   {id==='systems'?<section className="panel-providers"><h3>Adaptadores de datos y paper</h3><p className="source-note">Fuente: GET /api/providers/status · respuesta del backend P0; no es una prueba de conectividad con el proveedor externo.</p>{providers.isSuccess&&!providers.isError?<table><thead><tr><th scope="col">Proveedor</th><th scope="col">Estado</th><th scope="col">Motivo</th><th scope="col">Verificación externa</th></tr></thead><tbody>{providers.data.map(p=><tr key={p.provider}><th scope="row">{p.provider}</th><td><StatusBadge status="phase-locked">{p.status}</StatusBadge></td><td>{p.reason}</td><td>{p.checked_at?new Date(p.checked_at).toLocaleString('es-ES'):'Sin comprobar'}</td></tr>)}</tbody></table>:<p className="panel-error" role="status">{providers.isPending?'Comprobando proveedores…':'NO DISPONIBLE: no se recibió un contrato válido de proveedores.'}</p>}</section>:null}
   {content.columns.length?<DataTableShell columns={content.columns} message={content.empty} phase={monitor.phase}/>:null}
   <div className="panel-sections">{content.sections.map(section=><SectionCard key={section.title} {...section}/>)}</div>
  </div>
  <footer className="panel-footer"><span>Sesión local · Ninguna operación real</span><span>{live?'Datos locales comprobables':'Datos financieros no conectados'}</span></footer>
 </dialog>;
}
