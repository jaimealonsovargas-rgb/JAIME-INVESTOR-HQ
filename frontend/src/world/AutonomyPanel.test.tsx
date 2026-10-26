import {describe, expect, it} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {type AutonomyStatus} from '../autonomyApi';
import AutonomyPanel from './AutonomyPanel';

const status: AutonomyStatus = {
  enabled: true, paused: false, running: true, interval_seconds: 86400,
  next_due_at: '2026-10-26T12:00:00Z', last_error: null, llm_calls_max: 0,
  tasks: [{id: 'task-1', state: 'ABSTAINED', reason_code: 'SCHEDULED_DESCRIPTIVE_REVIEW',
    created_at: '2026-10-25T12:00:00Z', finished_at: '2026-10-25T12:00:01Z',
    case_id: 'case-1', source_access_id: 'public-source', subject: {symbol: 'BTC'},
    result: {quality_state: 'ABSTAINED', reason: 'NO_DATA', evidence_count: 0}}],
};
function render(value: AutonomyStatus) {
  const client = new QueryClient({defaultOptions: {queries: {retry: false}}});
  client.setQueryData(['research-autonomy'], value);
  const html = renderToStaticMarkup(<QueryClientProvider client={client}><AutonomyPanel onSelectCase={() => {}}/></QueryClientProvider>);
  client.clear();
  return html;
}
describe('autonomy UI truthful states', () => {
  it('shows scheduled reason, provenance, abstention and dossier access without inventing findings', () => {
    const html = render(status);
    for (const text of ['Investigación autónoma', 'sin LLM', 'Programación activa', 'Iniciada por JAIME', 'public-source', 'Abstención', 'NO_DATA', '0 evidencias', 'Ver dossier']) expect(html).toContain(text);
    expect(html).not.toContain('Cancelar tarea');
  });
  it('distinguishes paused and environment-disabled automation', () => {
    expect(render({...status, paused: true})).toContain('Reanudar automatización');
    const disabled = render({...status, enabled: false});
    expect(disabled).toContain('Desactivada por configuración');
    expect(disabled).not.toContain('Reanudar automatización');
    expect(disabled).not.toContain('Pausar automatización');
  });
  it('exposes cancellation for genuine running work and escapes external text', () => {
    const html = render({...status, tasks: [{...status.tasks[0], state: 'RUNNING', result: {reason: '<script>alert(1)</script>'}}]});
    expect(html).toContain('Cancelar tarea');
    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;script&gt;');
  });
});
