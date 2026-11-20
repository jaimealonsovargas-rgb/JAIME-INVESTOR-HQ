import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {validateCycleStatus,type CycleStatus} from '../cyclesApi';
import CyclePanel from './CyclePanel';

const status:CycleStatus={owner:'n8n',mode:'shadow',auth_configured:true,worker_running:true,worker_error:null,
  next_window_at:'2026-11-06T18:00:00Z',cycles:[{id:'a'.repeat(64),state:'PARTIAL',created_at:'2026-11-06T12:00:00Z',
    updated_at:'2026-11-06T12:01:00Z',result:{reason:'ACCOUNTING_REVIEW_COMPLETE',models:[{cik:'0000104169',version:4,state:'PARTIAL'}]}}]};
function render(data:CycleStatus){
  const client=new QueryClient();client.setQueryData(['shadow-cycles'],data);
  const html=renderToStaticMarkup(<QueryClientProvider client={client}><CyclePanel/></QueryClientProvider>);client.clear();return html;
}
describe('shadow cycle status',()=>{
  it('distinguishes permission to submit from a verified n8n process and preserves partial results',()=>{
    const html=render(status);
    expect(html).toContain('Solicitudes de n8n habilitadas');expect(html).toContain('Walmart: v4 · con pendientes');
    expect(html).toContain('Próxima ventana prevista');expect(html).toContain('Madrid');expect(html).not.toContain('Cancelar este ciclo');
  });
  it('shows cancellation only for pending work and hides permission controls until authenticated setup',()=>{
    expect(render({...status,cycles:[{...status.cycles[0],state:'FETCHING'}]})).toContain('Cancelar este ciclo');
    expect(render({...status,auth_configured:false})).not.toContain('Pausar nuevos ciclos');
    expect(render({...status,owner:'disabled'})).not.toContain('Próxima ventana prevista');
  });
  it('rejects malformed or non-shadow status rather than showing success',()=>{
    expect(validateCycleStatus(status)).toBe(status);
    expect(()=>validateCycleStatus({...status,mode:'live'})).toThrow();
    expect(()=>validateCycleStatus({...status,cycles:[{...status.cycles[0],state:'UNKNOWN'}]})).toThrow();
  });
  it('shows the risk receipt for a reviewed window and verifies its paper-only contract',()=>{
    const risk={outcome:'OBSERVE' as const,mode:'PAPER' as const,reason:'NO_CANDIDATES',decision_id:'b'.repeat(64),
      dossier_id:'c'.repeat(64),expires_at:status.next_window_at,orders_enabled:false as const,execution_ready:false as const};
    const cycle=status.cycles[0];
    const withRisk=(receipt:unknown)=>({...status,cycles:[{...cycle,result:{...cycle.result,risk:receipt}}]});
    const html=render(validateCycleStatus(withRisk(risk)));
    expect(html).toContain('En observación');expect(html).toContain('Ninguna estrategia superó la validación');
    expect(html).toContain(risk.decision_id);expect(html).toContain('Vigencia de riesgo');
    for(const changes of [{mode:'LIVE'},{orders_enabled:true},{execution_ready:true},{outcome:'BUY'},{decision_id:'bad'},{expires_at:'bad'}]){
      expect(()=>validateCycleStatus(withRisk({...risk,...changes}))).toThrow();
    }
  });
});
