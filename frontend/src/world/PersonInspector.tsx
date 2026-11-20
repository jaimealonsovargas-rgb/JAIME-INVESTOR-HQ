import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {researchRead,validateStatus,type Role} from '../researchApi';
import {PERSON_ROLES,ROLE_LABELS} from './personRoles';
import './personInspector.css';
import CompanyModelDeliveries from './CompanyModelDeliveries';

export const localTime=(value:string)=>new Date(value).toLocaleString('es-ES',{dateStyle:'medium',timeStyle:'short'})+' · hora local';
const DELIVERY:Record<string,string>={VERIFIED_DATA:'Datos y cálculos verificados',ACCEPTED:'Contrato validado; revisión pendiente',REJECTED:'Resultado rechazado',ABSTAINED:'Abstención',NOT_APPLICABLE:'No aplicable',PROVISIONAL:'Resultado provisional',PENDING_REVIEW:'Pendiente de revisión'};

export default function PersonInspector({personId,onOpenCase}:{personId:string;onOpenCase:(caseId:string,runKey:string)=>void}){
 const profile=PERSON_ROLES[personId];
 const [selected,setSelected]=useState(profile.roles[0]);
 const query=useQuery({queryKey:['research-roles'],queryFn:({signal})=>researchRead<Role[]>('/api/agents',signal),refetchInterval:10000,retry:false});
 const status=useQuery({queryKey:['research-status'],queryFn:async({signal})=>validateStatus(await researchRead('/api/agents/status',signal)),refetchInterval:10000,retry:false});
 const role=!query.isError?query.data?.find(r=>r.role_id===selected):undefined;
 const current=role?.current_job,delivery=role?.last_delivery;
 const runtime=!status.isError?status.data?.runtime:undefined;
 return <section className="person-inspector" aria-label="Ficha del especialista">
  <div className="person-roles" role="group" aria-label="Especialidades de esta persona">{profile.roles.map(id=><button key={id} aria-pressed={selected===id} onClick={()=>setSelected(id)}>{ROLE_LABELS[id]}</button>)}</div>
  {query.isError?<div className="person-empty" role="status"><h3>No se puede comprobar la actividad</h3><p>El servicio de investigación no responde. Reintenta para consultar tareas y entregas.</p><button onClick={()=>void query.refetch()}>Reintentar</button></div>:!role?<p role="status">Consultando al especialista…</p>:<>
   <div className="person-mandate"><h3>{ROLE_LABELS[role.role_id]??role.name}</h3><p>{role.mission}</p><details className="person-runtime"><summary>Capacidad y disponibilidad</summary><div className="person-capabilities"><span>Contrato: {role.enabled===false?'deshabilitado':'habilitado'}</span><span>{role.llm_required?'Inferencia local':'Cálculos Python'}</span>{role.llm_required?<span>Modelo: {runtime?.state??'sin comprobar'}</span>:null}</div></details></div>
   <div className="person-work">
    <section><h4>Trabajo actual</h4>{current?<><p className="person-state">{current.state==='RUNNING'?'En ejecución':'En cola'}</p><p>Desde <time dateTime={current.started_at??current.queued_at}>{localTime(current.started_at??current.queued_at)}</time></p><button onClick={()=>onOpenCase(current.case_id,current.run_key)}>Ver caso en curso</button></>:<><p className="person-state">Sin tarea activa</p><details className="person-explanation"><summary>Acerca de este estado</summary><p>Este rol no tiene trabajo en ejecución ni en cola. Tener un contrato habilitado no implica que esté investigando.</p></details></>}</section>
    <section><h4>Última entrega registrada</h4>{delivery?<><p className="person-state">{DELIVERY[delivery.quality_state]??delivery.quality_state}</p><p><time dateTime={delivery.finished_at}>{localTime(delivery.finished_at)}</time></p><p>{delivery.evidence_count} evidencias citadas · la vigencia y los derechos se comprueban al abrir el dossier.</p><button onClick={()=>onOpenCase(delivery.case_id,delivery.run_key)}>Abrir entrega y fuentes</button></>:<><p className="person-state">Sin entregas</p><details className="person-explanation"><summary>Acerca de las entregas</summary><p>Aún no consta un resultado de este rol. Aquí aparecerán su fecha, fuentes y acceso al dossier.</p></details></>}</section>
   </div>
   {['fundamental_equity','valuation','value_quality','data_quality'].includes(selected)?<details className="person-models"><summary>Modelos empresariales compartidos</summary><CompanyModelDeliveries/></details>:null}
   <details className="person-diagnostics"><summary>Identidad y permisos</summary><dl><div><dt>Persona</dt><dd>{personId}</dd></div><div><dt>Rol lógico</dt><dd>{role.role_id}</dd></div><div><dt>Permisos</dt><dd>{role.permissions.join(' · ')}</dd></div></dl><p>Esta persona representa {profile.roles.length} {profile.roles.length===1?'especialidad':'especialidades'}. La animación de la oficina no acredita actividad del sistema.</p></details>
  </>}
 </section>;
}
