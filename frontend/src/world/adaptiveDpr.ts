/** Control de resolución: usa intervalos reales de marcha, nunca el reposo a 20 Hz. */
export const DPR_POLICY = {
  initial: .8, min: .7, max: 1, targetFps: 45,
  lowFps: 44, urgentFps: 40, headroomFps: 54,
  windowMs: 2000, warmupMs: 1500, resizeWarmupMs: 500,
  downCooldownMs: 2500, upDwellMs: 8000, downStep: .02, upStep: .01,
} as const;

export type DprReason = 'warming' | 'idle' | 'stable' | 'load' | 'headroom' | 'minimum';
export interface DprChange { from: number; to: number; fps: number; reason: 'load' | 'headroom' }

export class AdaptiveDprController {
  value: number = DPR_POLICY.initial;
  fps: number | null = null;
  reason: DprReason = 'warming';
  private warmup: number = DPR_POLICY.warmupMs;
  private windowMs = 0;
  private frames = 0;
  private clock = 0;
  private changedAt = -Infinity;
  private slowWindows = 0;
  private headroomMs = 0;

  suspend() {
    this.windowMs = this.frames = this.slowWindows = this.headroomMs = 0;
    this.warmup = DPR_POLICY.warmupMs;
    this.fps = null;
    this.reason = 'idle';
  }

  observe(frameMs: number, eligible: boolean): DprChange | undefined {
    if (!eligible || !Number.isFinite(frameMs) || frameMs <= 0) {
      this.suspend();
      return;
    }
    this.clock += frameMs;
    if (this.warmup > 0) {
      this.warmup -= frameMs;
      this.reason = 'warming';
      return;
    }
    this.windowMs += frameMs;
    this.frames++;
    if (this.windowMs < DPR_POLICY.windowMs || this.frames < 20) return;
    const elapsed = this.windowMs;
    const fps = this.fps = 1000 * this.frames / elapsed;
    this.windowMs = this.frames = 0;
    this.slowWindows = fps < DPR_POLICY.lowFps ? this.slowWindows + 1 : 0;
    this.headroomMs = fps > DPR_POLICY.headroomFps ? this.headroomMs + elapsed : 0;
    const sinceChange = this.clock - this.changedAt;
    let next = this.value;
    let reason: DprChange['reason'] | undefined;
    if ((fps < DPR_POLICY.urgentFps || this.slowWindows >= 2) && sinceChange >= DPR_POLICY.downCooldownMs) {
      next = Math.max(DPR_POLICY.min, this.value - DPR_POLICY.downStep);
      reason = 'load';
    } else if (this.headroomMs >= DPR_POLICY.upDwellMs && sinceChange >= DPR_POLICY.upDwellMs) {
      next = Math.min(DPR_POLICY.max, this.value + DPR_POLICY.upStep);
      reason = 'headroom';
    }
    next = Math.round(next * 100) / 100;
    this.reason = this.value === DPR_POLICY.min && fps < DPR_POLICY.lowFps ? 'minimum' : 'stable';
    if (reason && next !== this.value) {
      const change = { from: this.value, to: next, fps, reason };
      this.value = next;
      this.reason = reason;
      this.changedAt = this.clock;
      this.slowWindows = this.headroomMs = 0;
      this.warmup = DPR_POLICY.resizeWarmupMs;
      return change;
    }
  }
}
