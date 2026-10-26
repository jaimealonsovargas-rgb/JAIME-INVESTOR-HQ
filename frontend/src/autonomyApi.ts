import {researchRead, researchWrite} from './researchApi';

export const AUTONOMY_TASK_STATES = ['QUEUED', 'RUNNING', 'SUCCEEDED', 'ABSTAINED', 'FAILED', 'CANCELLED', 'BLOCKED'] as const;
export type AutonomyTaskState = typeof AUTONOMY_TASK_STATES[number];
export type AutonomyTask = {
  id: string;
  state: AutonomyTaskState;
  reason_code: string;
  created_at: string;
  finished_at: string | null;
  case_id: string | null;
  source_access_id: string;
  subject: {symbol?: string; id?: string} | null;
  result: {quality_state?: string; reason?: string; evidence_count?: number} | null;
};
export type AutonomyStatus = {
  enabled: boolean;
  paused: boolean;
  running: boolean;
  interval_seconds: number;
  next_due_at: string | null;
  last_error: string | null;
  tasks: AutonomyTask[];
  llm_calls_max: 0;
};

function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function timestamp(value: unknown): value is string {
  return typeof value === 'string' && Number.isFinite(Date.parse(value));
}
function optionalString(value: unknown) { return value === undefined || typeof value === 'string'; }

export function validateAutonomyTask(value: unknown): AutonomyTask {
  if (!record(value) || typeof value.id !== 'string' || !value.id ||
      !AUTONOMY_TASK_STATES.includes(value.state as AutonomyTaskState) ||
      typeof value.reason_code !== 'string' || !timestamp(value.created_at) ||
      !(value.finished_at === null || timestamp(value.finished_at)) ||
      !(value.case_id === null || typeof value.case_id === 'string') ||
      typeof value.source_access_id !== 'string') throw Error('Tarea autónoma no verificable');
  if (value.subject !== null && (!record(value.subject) || !optionalString(value.subject.symbol) || !optionalString(value.subject.id))) throw Error('Instrumento autónomo no verificable');
  if (value.result !== null && (!record(value.result) || !optionalString(value.result.quality_state) ||
      !optionalString(value.result.reason) || (value.result.evidence_count !== undefined &&
      (!Number.isInteger(value.result.evidence_count) || (value.result.evidence_count as number) < 0)))) throw Error('Resultado autónomo no verificable');
  return value as AutonomyTask;
}

export function validateAutonomyStatus(value: unknown): AutonomyStatus {
  if (!record(value) || typeof value.enabled !== 'boolean' || typeof value.paused !== 'boolean' ||
      typeof value.running !== 'boolean' || value.llm_calls_max !== 0 ||
      typeof value.interval_seconds !== 'number' || !Number.isInteger(value.interval_seconds) || value.interval_seconds <= 0 ||
      !(value.next_due_at === null || timestamp(value.next_due_at)) ||
      !(value.last_error === null || typeof value.last_error === 'string') || !Array.isArray(value.tasks)) throw Error('Estado autónomo no verificable');
  value.tasks.forEach(validateAutonomyTask);
  if (new Set(value.tasks.map(task => (task as AutonomyTask).id)).size !== value.tasks.length) throw Error('Tareas autónomas duplicadas');
  return value as AutonomyStatus;
}

export function autonomyTaskIsActive(task: AutonomyTask) {
  return task.state === 'QUEUED' || task.state === 'RUNNING';
}
export async function readAutonomy(signal?: AbortSignal) {
  return validateAutonomyStatus(await researchRead('/api/research/autonomy', signal));
}
export async function controlAutonomy(action: 'pause' | 'resume') {
  return validateAutonomyStatus(await researchWrite('/api/research/autonomy/control', {action}, crypto.randomUUID()));
}
export async function cancelAutonomy(taskId: string) {
  return validateAutonomyTask(await researchWrite(`/api/research/autonomy/tasks/${encodeURIComponent(taskId)}/cancel`, {}, crypto.randomUUID()));
}
