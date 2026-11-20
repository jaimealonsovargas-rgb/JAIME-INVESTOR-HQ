import {useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {readCycles,controlCycles,cycleActive,type CycleState} from '../cyclesApi';

const LABELS:Record<CycleState,string>={QUEUED:'En cola',FETCHING:'Consultando SEC',REVIEWING:'Revisando cuentas',
  SUCCEEDED:'Completado',PARTIAL:'Completado con pendientes',BLOCKED:'Bloqueado',CANCEL_REQUESTED:'Cancelación solicitada',CANCELLED:'Cancelado',TIMED_OUT:'Tiempo agotado'};
const COMPANIES:Record<string,string>={'0000320193':'Apple','0000789019':'Microsoft','0000104169':'Walmart'};
const RISK_LABELS={OBSERVE:'En observación',VETO:'Propuesta bloqueada',ASSESSED:'Evaluación PAPER registrada'};
const RISK_REASONS:Record<string,string>={NO_CANDIDATES:'Ninguna estrategia superó la validación.',
  DOSSIER_MISSING:'Falta el expediente de validación.',DOSSIER_INVALID:'El expediente no supera el control de integridad.',
  EVIDENCE_EXPIRED:'Ha vencido la revisión de la evidencia.',REVIEWED_PAPER_INPUTS_MISSING:'Faltan datos PAPER revisados.',
  VALIDATION_INCOMPLETE:'La validación está incompleta.',ALL_PROPOSALS_VETOED:'Las propuestas exceden los límites o carecen de evidencia.',
  INDEPENDENT_VALIDATION_REQUIRED:'Falta una prueba con datos independientes.',PAPER_RISK_REVIEWED:'El motor ha registrado el resultado de los controles.',
  RISK_INPUTS_INVALID:'Los datos de la propuesta no superan los controles.',CANDIDATE_BUDGET_EXCEEDED:'El lote supera el límite de propuestas.',
  RISK_TIME_BUDGET_EXCEEDED:'Se agotó el tiempo de evaluación.'};
const date=(value:string)=>new Date(value).toLocaleString('es-ES',{timeZone:'Europe/Madrid',dateStyle:'short',timeStyle:'short'})+' · Madrid';

export default function CyclePanel(){
  const client=useQueryClient();
  const [pending,setPending]=useState(false);
  const [error,setError]=useState('');
  const query=useQuery({queryKey:['shadow-cycles'],queryFn:({signal})=>readCycles(signal),retry:false,refetchInterval:10000,refetchIntervalInBackground:false});
  const data=query.isError?undefined:query.data;
  async function act(action:'pause'|'resume'|'cancel',id?:string){
    setPending(true);setError('');
    try{await controlCycles(action,id);await client.invalidateQueries({queryKey:['shadow-cycles']});}
    catch(cause){setError(cause instanceof Error?cause.message:'No se pudo confirmar el cambio.');}
    finally{setPending(false);}
  }
  return <section className="research-autonomy" aria-label="Ciclos SEC con n8n">
    <header><div><h4>Ciclos SEC con n8n</h4><p>Apple · Microsoft · Walmart</p></div>
      {data?.auth_configured?<button disabled={pending} onClick={()=>void act(data.owner==='n8n'?'pause':'resume')}>
        {data.owner==='n8n'?'Pausar nuevos ciclos':'Permitir ciclos de n8n'}</button>:null}</header>
    {error?<p role="alert">{error}</p>:null}
    {query.isError?<p role="status">No se puede verificar la automatización. Comprueba el backend.</p>:!data?<p role="status">Consultando ciclos…</p>:<>
      <p role="status"><strong>{!data.auth_configured?'Conexión pendiente':data.owner==='disabled'?'Nuevos ciclos pausados':!data.worker_running?'Cola detenida':'Solicitudes de n8n habilitadas'}</strong></p>
      <p className="research-note">Cada seis horas · riesgo PAPER y revisión contable SEC.</p>
      {data.owner==='n8n'?<p>Próxima ventana prevista: {date(data.next_window_at)}</p>:null}
      <p className="research-note">Pausar impide nuevos ciclos; los aceptados pueden terminar. La revisión muestra sus carencias y no ejecuta operaciones.</p>
      {data.worker_error?<p role="status">La cola necesita revisión: {data.worker_error}</p>:null}
      {data.cycles.length?<ol className="autonomy-task-list">{data.cycles.slice(0,3).map(c=><li key={c.id}>
        <div className="autonomy-task-heading"><strong>{LABELS[c.state]}</strong><span>{date(c.created_at)}</span></div>
        {c.result.models.length?<p>{c.result.models.map(m=>`${COMPANIES[m.cik]??m.cik}: ${m.version?'v'+m.version+' · ':''}${m.state==='PASSED'?'controles superados':m.state==='PARTIAL'?'con pendientes':'bloqueado'}`).join(' / ')}</p>:null}
        {c.result.risk && <p><strong>{RISK_LABELS[c.result.risk.outcome]}</strong> · {RISK_REASONS[c.result.risk.reason]??c.result.risk.reason}</p>}
        <details><summary>Detalle del ciclo</summary><p>Motivo · {c.result.reason}</p><p>Referencia · <code style={{overflowWrap:'anywhere'}}>{c.id}</code></p>
          {c.result.risk && <><p>Vigencia de riesgo hasta {date(c.result.risk.expires_at)}</p>
            <p>Decisión · <code style={{overflowWrap:'anywhere'}}>{c.result.risk.decision_id}</code></p></>}
        </details>
        {cycleActive(c.state)?<button disabled={pending||c.state==='CANCEL_REQUESTED'} onClick={()=>void act('cancel',c.id)}>Cancelar este ciclo</button>:null}
      </li>)}</ol>:<p>Todavía no hay ciclos registrados.</p>}
    </>}
  </section>;
}
