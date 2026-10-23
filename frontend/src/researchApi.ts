export type Role={role_id:string;name:string;team:string;mission:string;state:string;llm_required:boolean;permissions:string[]};
export type Job={id:string;role_id:string;state:string;queued_at:string;finished_at:string|null;error:string|null;duration_ms:number|null;input_hash:string|null;output_hash:string|null;model:string|null;run_key:string};
export type RuntimeStatus={checked_at:string;active_jobs:number;queue:number;failures:number;roles:number;department_states?:Record<string,string>;last_completed?:Job|null;capacity:{llm:number;quant:number;fetch:number};runtime:{state:string;model:string|null;runtime:string};orders_enabled:false;trading_mode:'PAPER_ONLY'};
export type ResearchCase={id:string;instrument:{id:string;symbol:string;asset_class:string};question:string;created_at:string};
export type Claim={claim_id:string;text:string;evidence_ids:string[];verified:boolean;grounding:string;claim_type:string};
export type Opinion={overview:string;claims:{text:string;evidence_ids:string[]}[];unknowns:string[];invalidation_conditions:string[];research_view:string;thesis?:string;catalysts?:string[];risks?:string[];key_disagreements?:string[]};
export type Evidence={id:string;provider:string;source:string;url:string;retrieved_at:string;observed_at:string;rights:Record<string,unknown>;freshness:string;hash:string;trust_class:string;scope:string;available:boolean;rights_ok:boolean;content:{excerpt:string}};
export type ResearchQuality={state:string;reason?:string;basis?:string;human_review?:string};
export type StructuredArgument={argument_id?:string;target_bull_argument_id?:string;bull_argument_id?:string;bear_argument_id?:string;thesis?:string;mechanism?:string;assumption?:string;falsification?:string;objection?:string;evidence_gap?:string;change_of_mind?:string;disagreement?:string;limitation?:string;supporting_evidence_ids?:string[];counter_evidence_ids?:string[];evidence_ids?:string[]};
export type Result={quality?:ResearchQuality;structured?:{arguments?:StructuredArgument[];objections?:StructuredArgument[];findings?:StructuredArgument[];synthesis?:string;conclusion?:string}|null;evidence_pack?:{records:{id:string;evidence_id:string}[]};job_id:string;role_id:string;created_at:string;input_hash:string;opinion:Opinion;claims:Claim[];debate:Record<string,Opinion>;metrics:Record<string,unknown>;validation?:{raw_output_hash:string|null;withheld_passages:{field:string;reason:string;text_hash:string}[]};features:null|{state:string;reason?:string;items:{name:string;value:string;evidence_ids:string[]}[]}};
export type Dossier=ResearchCase&{research_goal?:string;analysis_depth?:'ordinary'|'deep'|null;quality?:ResearchQuality;status:string;runs?:string[];active_run_key?:string;thesis_version?:number;jobs:Job[];results:Result[];evidence:Evidence[];orders_enabled:false;advisory_only:true};

export function validateStatus(x:unknown):RuntimeStatus{
 if(!x||typeof x!=='object')throw Error('Estado research inválido');const s=x as RuntimeStatus;
 if(s.orders_enabled!==false||s.trading_mode!=='PAPER_ONLY'||s.roles!==30||s.capacity?.llm!==1||s.capacity?.quant!==2||s.capacity?.fetch!==4||!s.runtime||typeof s.runtime.state!=='string'||![s.active_jobs,s.queue,s.failures].every(n=>Number.isInteger(n)&&n>=0))throw Error('Contrato research inseguro');return s;
}
export function validateDossier(x:unknown):Dossier{
 if(!x||typeof x!=='object')throw Error('Dossier inválido');const d=x as Dossier;
 if(d.orders_enabled!==false||d.advisory_only!==true||!Array.isArray(d.results)||!Array.isArray(d.evidence)||!Array.isArray(d.jobs))throw Error('Dossier inseguro');
 const ids=new Set(d.evidence.map(e=>e.id));for(const r of d.results){if(!r.opinion||!Array.isArray(r.claims)||r.claims.some(c=>typeof c.verified!=='boolean'||!c.evidence_ids.every(id=>ids.has(id))))throw Error('Dossier sin lineage');}return d;
}
export async function researchRead<T>(path:string,signal?:AbortSignal):Promise<T>{
 const r=await fetch(path,{signal:signal?AbortSignal.any([signal,AbortSignal.timeout(8000)]):AbortSignal.timeout(8000),credentials:'omit',cache:'no-store'});if(!r.ok)throw Error('Research no disponible');return r.json() as Promise<T>;
}
export async function researchWrite<T>(path:string,body:unknown,key:string):Promise<T>{
 const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-HQ-Research':'1','Idempotency-Key':key},body:JSON.stringify(body),credentials:'omit',signal:AbortSignal.timeout(10000)});
 if(!r.ok)throw Error(`Solicitud research rechazada (${r.status})`);return r.json() as Promise<T>;
}
