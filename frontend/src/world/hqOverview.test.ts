import {it,expect} from 'vitest';
import {HQ_TITLES,validateOverview} from './HQVideowall';
const fixture=()=>({checked_at:'2026-10-15T00:00:00Z',trading_mode:'PAPER_ONLY',orders_enabled:false,
 sections:Object.keys(HQ_TITLES).map(section_id=>({section_id,phase_required:'TEST_ONLY',status:'NOT_IMPLEMENTED',as_of_utc:null,source:null,value:null,items:[],quality:{},rights:null,reason:'TEST_ONLY'}))});

it('ausencia de cartera conserva null, sin sembrar fondos en el videowall',()=>{
 const result=validateOverview(fixture());expect(result.sections).toHaveLength(9);
 expect(result.sections.every(s=>s.value===null)).toBe(true);
});
it('rechaza importes inventados, jobs futuros y secciones duplicadas',()=>{
 const amount=fixture();(amount.sections[0] as unknown as {value:number}).value=10000;
 expect(()=>validateOverview(amount)).toThrow();
 const jobs=fixture();jobs.sections.find(s=>s.section_id==='agents')!.status='AVAILABLE';
 expect(()=>validateOverview(jobs)).toThrow();
 const duplicate=fixture();duplicate.sections[1]=duplicate.sections[0];expect(()=>validateOverview(duplicate)).toThrow();
});
