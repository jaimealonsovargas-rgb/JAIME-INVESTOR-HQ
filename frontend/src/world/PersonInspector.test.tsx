import {describe,expect,it} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import PersonInspector from './PersonInspector';
import {PERSON_ROLES} from './personRoles';
import {PERSONNEL} from './staffLayout';
import type {Role} from '../researchApi';

const role:Role={role_id:'fundamental_equity',name:'Test',team:'research',mission:'Analizar estados financieros con fuentes.',state:'IDLE',llm_required:true,permissions:['evidence.read'],enabled:true,current_job:null,last_delivery:null};
function render(value:Role){
 const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
 client.setQueryData(['research-roles'],[value]);
 client.setQueryData(['research-status'],{runtime:{state:'NO_LOCAL_MODEL'}});
 const html=renderToStaticMarkup(<QueryClientProvider client={client}><PersonInspector personId="personal-research-1" onOpenCase={()=>{}}/></QueryClientProvider>);
 client.clear();return html;
}
describe('person identity and honest work state',()=>{
 it('binds every existing office person and all thirty roles without duplicating workers',()=>{
  expect(PERSONNEL.map(p=>p.id).sort()).toEqual(Object.keys(PERSON_ROLES).sort());
  const ids=Object.values(PERSON_ROLES).flatMap(p=>p.roles);
  expect(ids.length).toBe(30);expect(new Set(ids).size).toBe(30);
 });
 it('shows empty work and a stopped model independently of an enabled contract',()=>{
  const html=render(role);
  for(const text of ['Fundamentales','Valoración','Sin tarea activa','Sin entregas','NO_LOCAL_MODEL','Contrato: habilitado'])expect(html).toContain(text);
  expect(html).not.toContain('Crear caso');expect(html).not.toContain('En ejecución');
 });
 it('shows actual delivery date and source count without claiming current validity',()=>{
  const html=render({...role,current_job:{id:'job',case_id:'case',run_key:'run',state:'QUEUED',queued_at:'2026-10-27T10:00:00Z',started_at:null},last_delivery:{case_id:'case',job_id:'previous',run_key:'old-run',finished_at:'2026-10-26T12:00:00Z',quality_state:'ABSTAINED',evidence_count:2}});
  for(const text of ['En cola','Abstención','2 evidencias citadas','Abrir entrega y fuentes','2026-10-26T12:00:00Z'])expect(html).toContain(text);
  expect(html).not.toContain('Sin entregas');
 });
});
