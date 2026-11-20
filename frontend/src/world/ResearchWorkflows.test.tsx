import {expect,it} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {ResearchWorkflowSummary} from './ResearchPanel';
import {validateDossier} from '../researchApi';

it('shows unavailable thesis and events without fabricating recommendations',()=>{
 const data=validateDossier({id:'test',orders_enabled:false,advisory_only:true,jobs:[],results:[],evidence:[],workflows:{advisory_only:true,evaluated_at:'2026-11-04T12:00:00Z',morning_note:{headline:'Sin evidencia suficiente',coverage:'Solo evidencia del ciclo',observations:[]},thesis_tracker:{reason:'No se ha formulado una tesis',version:1},catalyst_calendar:{reason:'No hay fechas confirmadas por P2',events:[]}}});
 const html=renderToStaticMarkup(<ResearchWorkflowSummary data={data}/>);
 expect(html).toContain('Nota del ciclo, tesis y próximos eventos');
 expect(html).toContain('No se ha formulado una tesis');expect(html).toContain('No hay fechas confirmadas por P2');
 expect(html).not.toContain('Comprar');
});
