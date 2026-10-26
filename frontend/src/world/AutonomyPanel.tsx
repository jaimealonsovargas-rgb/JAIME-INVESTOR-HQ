import {useState} from 'react';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {autonomyTaskIsActive, cancelAutonomy, controlAutonomy, readAutonomy, type AutonomyTaskState} from '../autonomyApi';

const STATES: Record<AutonomyTaskState, string> = {
  QUEUED: 'En cola', RUNNING: 'En investigación', SUCCEEDED: 'Completada',
  ABSTAINED: 'Abstención', FAILED: 'Fallida', CANCELLED: 'Cancelada', BLOCKED: 'Bloqueada',
};
const date = (value: string | null) => value ? new Date(value).toLocaleString('es-ES') : 'Sin fecha programada';

export default function AutonomyPanel({onSelectCase}: {onSelectCase: (id: string) => void}) {
  const client = useQueryClient();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const query = useQuery({
    queryKey: ['research-autonomy'], queryFn: ({signal}) => readAutonomy(signal),
    refetchInterval: 10000, refetchIntervalInBackground: false, retry: false,
  });
  const data = query.isError ? undefined : query.data;
  async function act(action: () => Promise<unknown>) {
    setError(''); setPending(true);
    try {
      await action();
      await client.invalidateQueries({predicate: item => String(item.queryKey[0]).startsWith('research-')});
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo confirmar el cambio.'); }
    finally { setPending(false); }
  }
  return <section className="research-autonomy" aria-label="Investigación autónoma">
    <header><div><h4>Investigación autónoma</h4><p>Revisión descriptiva programada · Python · sin LLM</p></div>
      {data?.enabled ? <button disabled={pending} onClick={() => void act(() => controlAutonomy(data.paused ? 'resume' : 'pause'))}>
        {data.paused ? 'Reanudar automatización' : 'Pausar automatización'}
      </button> : null}
    </header>
    {error ? <p role="alert">{error}</p> : null}
    {query.isError ? <p role="status">NO DISPONIBLE: no se puede verificar la automatización. Reconecta el backend para consultar o detener las tareas.</p> : !data ? <p role="status">Consultando automatización…</p> : <>
      <p role="status"><strong>{!data.enabled ? 'Desactivada por configuración' : data.paused ? 'Pausada' : !data.running ? 'Planificador detenido' : 'Programación activa'}</strong>
        {data.enabled && !data.paused && data.running ? ` · Próxima revisión: ${date(data.next_due_at)}` : ''}</p>
      <p className="research-note">Cadencia: {Math.round(data.interval_seconds / 60)} minutos. Solo funciona con el backend encendido. Pausar también cancela las tareas autónomas activas.</p>
      <p className="research-note">Los resultados indican el estado al finalizar la tarea. Abre el dossier para comprobar la vigencia actual de sus datos.</p>
      {data.last_error ? <p role="status">Última incidencia: {data.last_error}</p> : null}
      {data.tasks.length ? <ol className="autonomy-task-list">{data.tasks.slice(0, 6).map(task => <li key={task.id}>
        <div className="autonomy-task-heading"><strong>{task.subject?.symbol ?? 'Sin instrumento elegible'}</strong><span>{STATES[task.state]}</span></div>
        <p>{task.reason_code === 'SCHEDULED_DESCRIPTIVE_REVIEW' ? 'Iniciada por JAIME al vencer la revisión programada.' : `Motivo registrado: ${task.reason_code}`}</p>
        <p>Fuente P2: {task.source_access_id || 'No seleccionada'} · Inicio: {date(task.created_at)}{task.finished_at ? ` · Fin: ${date(task.finished_at)}` : ''}</p>
        {task.result ? <p>{task.result.reason ?? task.result.quality_state ?? 'Sin detalle de resultado'}{task.result.evidence_count !== undefined ? ` · ${task.result.evidence_count} evidencias` : ''}</p> : null}
        <div className="autonomy-task-actions">
          {task.case_id ? <button onClick={() => onSelectCase(task.case_id!)}>Ver dossier</button> : null}
          {autonomyTaskIsActive(task) ? <button disabled={pending} onClick={() => void act(() => cancelAutonomy(task.id))}>Cancelar tarea</button> : null}
        </div>
      </li>)}</ol> : <p>Todavía no hay tareas autónomas registradas.</p>}
    </>}
  </section>;
}
