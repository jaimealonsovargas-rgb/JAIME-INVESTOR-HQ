import {afterEach, describe, expect, it, vi} from 'vitest';
import {autonomyTaskIsActive, cancelAutonomy, controlAutonomy, readAutonomy, validateAutonomyStatus, validateAutonomyTask, type AutonomyStatus, type AutonomyTask} from './autonomyApi';

const task: AutonomyTask = {
  id: 'task-1', state: 'ABSTAINED', reason_code: 'SCHEDULED_DESCRIPTIVE_REVIEW',
  created_at: '2026-10-25T12:00:00Z', finished_at: '2026-10-25T12:00:01Z', case_id: 'case-1',
  source_access_id: 'public-source', subject: {symbol: 'BTC'},
  result: {quality_state: 'ABSTAINED', reason: 'NO_DATA', evidence_count: 0},
};
const status: AutonomyStatus = {
  enabled: true, paused: false, running: true, interval_seconds: 86400,
  next_due_at: '2026-10-26T12:00:00Z', last_error: null, tasks: [task], llm_calls_max: 0,
};
afterEach(() => vi.unstubAllGlobals());

describe('autonomy contracts and controls', () => {
  it('preserves explicit abstention and supports no eligible instrument', () => {
    expect(validateAutonomyStatus(status).tasks[0].result?.reason).toBe('NO_DATA');
    expect(validateAutonomyTask({...task, subject: null, case_id: null}).subject).toBeNull();
  });
  it('rejects unbounded synthesis, malformed state and duplicated tasks', () => {
    for (const value of [
      {...status, llm_calls_max: 1}, {...status, interval_seconds: 0},
      {...status, next_due_at: 'not a date'}, {...status, tasks: [task, task]},
      {...status, tasks: [{...task, state: 'BUY'}]},
      {...status, tasks: [{...task, result: {evidence_count: -1}}]},
    ]) expect(() => validateAutonomyStatus(value)).toThrow();
  });
  it('offers cancellation only for queued or running tasks', () => {
    expect(autonomyTaskIsActive({...task, state: 'QUEUED'})).toBe(true);
    expect(autonomyTaskIsActive({...task, state: 'RUNNING'})).toBe(true);
    for (const state of ['SUCCEEDED', 'ABSTAINED', 'FAILED', 'CANCELLED', 'BLOCKED'] as const) {
      expect(autonomyTaskIsActive({...task, state})).toBe(false);
    }
  });
  it('reads without side effects, credentials or cached status', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(status)));
    vi.stubGlobal('fetch', fetchMock);
    expect((await readAutonomy()).llm_calls_max).toBe(0);
    expect(fetchMock).toHaveBeenCalledWith('/api/research/autonomy', expect.objectContaining({credentials: 'omit', cache: 'no-store'}));
    expect(fetchMock.mock.calls[0][1].method).toBeUndefined();
  });
  it('uses protected research POSTs for pause and cancellation', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({...status, paused: true})))
      .mockResolvedValueOnce(new Response(JSON.stringify({...task, state: 'CANCELLED'})));
    vi.stubGlobal('fetch', fetchMock);
    expect((await controlAutonomy('pause')).paused).toBe(true);
    expect((await cancelAutonomy('task-1')).state).toBe('CANCELLED');
    expect(fetchMock.mock.calls.map(call => call[0])).toEqual(['/api/research/autonomy/control', '/api/research/autonomy/tasks/task-1/cancel']);
    for (const [, init] of fetchMock.mock.calls) {
      expect(init).toMatchObject({method: 'POST', credentials: 'omit', headers: {'X-HQ-Research': '1'}});
      expect(init.headers['Idempotency-Key']).toMatch(/^[a-f0-9-]{36}$/);
    }
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({action: 'pause'});
  });
  it('does not pretend a rejected control succeeded', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', {status: 403})));
    await expect(controlAutonomy('resume')).rejects.toThrow('403');
  });
});
