import {describe,it,expect} from 'vitest';
import {validateStatus,validateDossier} from './researchApi';
const status={checked_at:'2026-10-16T00:00:00Z',active_jobs:0,queue:0,failures:0,roles:30,capacity:{llm:1,quant:2,fetch:4},runtime:{state:'NO_LOCAL_MODEL',model:null,runtime:'llama.cpp'},orders_enabled:false,trading_mode:'PAPER_ONLY'};
describe('P4 contracts',()=>{
 it('accepts explicit absence of model without invented jobs',()=>expect(validateStatus(status).runtime.state).toBe('NO_LOCAL_MODEL'));
 it('rejects live, unbounded concurrency and fake counters',()=>{for(const x of [{...status,orders_enabled:true},{...status,capacity:{llm:30,quant:2,fetch:4}},{...status,active_jobs:-1}])expect(()=>validateStatus(x)).toThrow();});
 it('rejects nonexistent evidence even when marked verified',()=>expect(()=>validateDossier({orders_enabled:false,advisory_only:true,jobs:[],evidence:[],results:[{opinion:{},claims:[{verified:true,evidence_ids:['fake']}]}]})).toThrow());
 it('allows empty truthful dossier',()=>expect(validateDossier({orders_enabled:false,advisory_only:true,jobs:[],evidence:[],results:[]}).results).toEqual([]));
 it('rejects workflow claims without evidence and unsafe event dates',()=>{
  const workflows={evaluated_at:'2026-11-04T12:00:00Z',advisory_only:true,morning_note:{headline:'Sin datos',coverage:'Solo ciclo',observations:[] as {text:string;evidence_ids:string[]}[]},thesis_tracker:{reason:'Sin tesis',version:1},catalyst_calendar:{reason:'Sin eventos',events:[] as {title:string;at:string;evidence_ids:string[]}[]}};
  const d={orders_enabled:false,advisory_only:true,jobs:[],evidence:[],results:[],workflows};
  expect(validateDossier(d).workflows).toEqual(workflows);
  workflows.morning_note.observations.push({text:'Inventado',evidence_ids:['missing']});expect(()=>validateDossier(d)).toThrow();
  workflows.morning_note.observations=[];workflows.catalyst_calendar.events.push({title:'Evento',at:'mañana',evidence_ids:[]});expect(()=>validateDossier(d)).toThrow();
 });
});
