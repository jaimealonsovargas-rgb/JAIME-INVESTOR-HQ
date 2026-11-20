import { useEffect,useRef,useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth,fetchProviders,type Health } from '../api';
import { DEPARTMENTS } from './layout';
import { MONITOR_DEFINITIONS } from './terminals';
import { PANEL_CONTENT } from './panels';
import DataQuality from './DataQuality';
import ResearchPanel from './ResearchPanel';
import {PortfolioDepartment} from './FinancialHud';
import './panels.css';
import PersonInspector from './PersonInspector';
import {PERSON_ROLES} from './personRoles';

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
 const items=Array.from(dialog.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], summary, input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')).filter(item=>item.getClientRects().length>0);
 const first=items[0],last=items.at(-1),active=document.activeElement;
 if(!first){event.preventDefault();dialog.focus();return;}
 if(!dialog.contains(active)||(event.shiftKey?active===first:active===last)){event.preventDefault();(event.shiftKey?last!:first).focus();}
}

export default function MonitorOverlay({id,personId,onClose}:{id:string;personId?:string;onClose:()=>void}) {
 const dialog=useRef<HTMLDialogElement>(null),close=useRef<HTMLButtonElement>(null);
 const [view,setView]=useState<'person'|'work'|'department'>(personId?'person':'department');
 const [selectedCase,setSelectedCase]=useState({id:'',run:''});
 const monitor=MONITOR_DEFINITIONS.find(m=>m.id===id)!;
 const content=PANEL_CONTENT[id],person=personId?PERSON_ROLES[personId]:undefined;
 const financial=['reception','trading','performance'].includes(id);
 const health=useQuery({queryKey:['health'],queryFn:({signal})=>fetchHealth(signal),retry:false,refetchInterval:15000});
 const providers=useQuery({queryKey:['providers'],queryFn:({signal})=>fetchProviders(signal),retry:false,enabled:id==='systems'&&view==='department'});
 useEffect(()=>{const previous=document.activeElement as HTMLElement|null;const node=dialog.current!;node.showModal();close.current?.focus();return()=>{node.close();if(previous?.isConnected)previous.focus();};},[]);
 const healthy=health.isSuccess&&!health.isError;
 const stale=healthy&&Date.now()-Date.parse(health.data.checked_at)>60000;
 const capability=id==='execution'?'Ejecución P6 pendiente; órdenes bloqueadas':id==='risk'?'Riesgo determinista pendiente; análisis P4 parcial':id==='quant'?'Estadística descriptiva disponible; minería P5 pendiente':id==='committee'?'Debate P4 parcial; sin decisión ejecutable':id==='research'?'Investigación P4 parcial; cobertura de empresas limitada':id==='systems'?'Datos P2 y supervisión local implementados':'Contabilidad virtual MASTER implementada';
 function openCase(caseId:string,runKey:string){setSelectedCase({id:caseId,run:runKey});setView('work');}
 return <dialog ref={dialog} className="monitor-dialog" aria-modal="true" aria-labelledby="panel-title" aria-describedby="panel-description" onKeyDown={containTabFocus} onCancel={e=>{e.preventDefault();onClose();}}>
  <div className="panel-chrome"><span>JAIME INVESTOR HQ <span className="chrome-divider">/</span> {monitor.label}</span><button ref={close} onClick={onClose}>Volver a la oficina <kbd>Esc</kbd></button></div>
  <header className="panel-header"><div><h2 id="panel-title">{person?.label??monitor.panel}</h2><p id="panel-description">{person?'Mandato, trabajo y entregas de las especialidades representadas en este puesto.':content.description}</p></div><div className="panel-status"><StatusBadge status={health.isPending?'pending':health.isError?'offline':stale?'stale':'available'}>{health.isPending?'Servicio: comprobando':health.isError?'Servicio: sin conexión':stale?'Servicio: comprobación antigua':'Servicio: conectado'}</StatusBadge><span>PAPER ONLY</span></div></header>
  <nav className="panel-view-switch" aria-label="Contenido del panel">
   {person?<button aria-pressed={view==='person'} onClick={()=>setView('person')}>Especialista</button>:null}
   <button aria-pressed={view==='work'} onClick={()=>setView('work')}>Casos y entregas</button>
   <button aria-pressed={view==='department'} onClick={()=>setView('department')}>Departamento</button>
  </nav>
  <div className="panel-body">
   {view==='person'&&personId?<PersonInspector key={personId} personId={personId} onOpenCase={openCase}/>:null}
   {view==='work'?<ResearchPanel key={selectedCase.id+selectedCase.run} department={id} initialCaseId={selectedCase.id} initialRun={selectedCase.run} roleIds={person?.roles}/>:null}
   {view==='department'?<>
    <section className="department-capability"><h3>Capacidad del departamento</h3><p>{capability}.</p><p>La conexión al servicio indica que el backend responde. Cada fuente, tarea y resultado conserva su propio estado.</p></section>
    {id==='systems'?<DataQuality/>:null}
    {financial?<PortfolioDepartment id={id}/>:null}
    {id==='reception'?<section className="panel-map"><h3>Departamentos</h3><ol>{DEPARTMENTS.map(d=><li key={d.id}><span>{d.number}</span><strong>{d.label}</strong><small>{d.use}</small></li>)}</ol></section>:null}
    <details className="panel-reference"><summary>Alcance y funciones previstas</summary><div className="panel-sections">{content.sections.map(section=><SectionCard key={section.title} {...section}/>)}</div></details>
    <details className="panel-reference"><summary>Diagnóstico del servicio</summary><section className="panel-health" aria-label="Salud real del backend"><div className="section-heading"><h3>Servicio local</h3><button onClick={()=>void health.refetch()} disabled={health.isFetching}>Comprobar conexión</button></div>{healthy?<HealthDetail health={health.data}/>:<p className="panel-error" role="status">{health.isPending?'Comprobando…':'No se pudo verificar el servicio local.'}</p>}</section>
    {id==='systems'?<section className="panel-providers"><h3>Protecciones de ejecución</h3><p>Estado local; no acredita conexión externa.</p>{providers.isSuccess&&!providers.isError?providers.data.map(p=><p key={p.provider}><strong>{p.provider}</strong> · {p.status} · {p.reason}</p>):<p>Sin comprobar</p>}</section>:null}</details>
   </>:null}
  </div>
  <footer className="panel-footer"><span>Investigación y capital virtual</span><span>Órdenes deshabilitadas</span></footer>
 </dialog>;
}
