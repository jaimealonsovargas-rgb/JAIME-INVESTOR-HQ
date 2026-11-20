export type CycleState='QUEUED'|'FETCHING'|'REVIEWING'|'SUCCEEDED'|'PARTIAL'|'BLOCKED'|'CANCEL_REQUESTED'|'CANCELLED'|'TIMED_OUT';
export type CycleRisk={outcome:'OBSERVE'|'VETO'|'ASSESSED';reason:string;mode:'PAPER';decision_id:string;dossier_id:string;
  expires_at:string;orders_enabled:false;execution_ready:false};
export type ShadowCycle={id:string;state:CycleState;created_at:string;updated_at:string;result:{reason:string;risk?:CycleRisk;models:{cik:string;id?:string;version?:number;state:string}[]}};
export type CycleStatus={owner:'disabled'|'n8n';mode:'shadow';auth_configured:boolean;worker_running:boolean;worker_error:string|null;next_window_at:string;cycles:ShadowCycle[]};
const STATES=new Set(['QUEUED','FETCHING','REVIEWING','SUCCEEDED','PARTIAL','BLOCKED','CANCEL_REQUESTED','CANCELLED','TIMED_OUT']);
export const cycleActive=(state:CycleState)=>['QUEUED','FETCHING','REVIEWING','CANCEL_REQUESTED'].includes(state);
const hash=(value:unknown)=>typeof value==='string' && /^[a-f0-9]{64}$/.test(value);
function validRisk(risk:CycleRisk){
  return risk && ['OBSERVE','VETO','ASSESSED'].includes(risk.outcome) && risk.mode==='PAPER' && typeof risk.reason==='string'
    && hash(risk.decision_id) && hash(risk.dossier_id) && Number.isFinite(Date.parse(risk.expires_at))
    && risk.orders_enabled===false && risk.execution_ready===false;
}

export function validateCycleStatus(value:unknown):CycleStatus{
  const v=value as CycleStatus;
  if(!v||!['n8n','disabled'].includes(v.owner)||v.mode!=='shadow'||typeof v.auth_configured!=='boolean'||typeof v.worker_running!=='boolean'
    ||!Number.isFinite(Date.parse(v.next_window_at))||!Array.isArray(v.cycles)||v.cycles.length>10||v.cycles.some(c=>
      !/^[a-f0-9]{64}$/.test(c.id)||!STATES.has(c.state)||!Number.isFinite(Date.parse(c.created_at))||!c.result||typeof c.result.reason!=='string'||!Array.isArray(c.result.models)
      ||(c.result.risk!==undefined&&!validRisk(c.result.risk))
      ||c.result.models.length>3||c.result.models.some(m=>!/^\d{10}$/.test(m.cik)||typeof m.state!=='string')))
    throw new Error('No se puede verificar el estado de los ciclos.');
  return v;
}
export async function readCycles(signal?:AbortSignal){
  const response=await fetch('/api/automation/status',{signal});
  if(!response.ok)throw new Error('No se puede consultar la coordinación de n8n.');
  return validateCycleStatus(await response.json());
}
export async function controlCycles(action:'pause'|'resume'|'cancel',id?:string){
  const url=action==='cancel'?`/api/universe/automation/cycles/${encodeURIComponent(id??'')}/cancel`:'/api/universe/automation/control';
  const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-HQ-Universe':'1'},
    body:JSON.stringify(action==='cancel'?{}:{owner:action==='resume'?'n8n':'disabled'})});
  if(!response.ok)throw new Error('No se pudo confirmar el cambio en la automatización.');
}
