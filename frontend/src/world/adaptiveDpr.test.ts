import { describe, expect, it } from 'vitest';
import { AdaptiveDprController, DPR_POLICY, type DprChange } from './adaptiveDpr';

// TEST_ONLY: relojes sintéticos para los límites del controlador, no FPS del hardware.
function feed(control: AdaptiveDprController, fps: number, seconds: number, eligible = true) {
  const changes: DprChange[] = [];
  for (let i = 0; i < fps * seconds; i++) {
    const change = control.observe(1000 / fps, eligible);
    if (change) changes.push(change);
  }
  return changes;
}
describe('resolución adaptativa', () => {
  it('parte de 0,8 y baja con carga sostenida sin superar pasos de 0,02 ni bajar de 0,7', () => {
    const control = new AdaptiveDprController();
    expect(control.value).toBe(.8);
    const changes = feed(control, 30, 45);
    expect(control.value).toBe(.7);
    expect(changes.length).toBe(5);
    expect(changes.every(c => c.from - c.to <= .020001 && c.to >= .7)).toBe(true);
    expect(control.reason).toBe('minimum');
  });
  it('recupera resolución lentamente con margen real hasta 1,0', () => {
    const control = new AdaptiveDprController();
    expect(feed(control, 60, 8)).toHaveLength(0);
    const changes = feed(control, 60, 220);
    expect(control.value).toBe(1);
    expect(changes.every(c => c.reason === 'headroom' && c.to - c.from <= .010001)).toBe(true);
  });
  it('mantiene resolución en el rango objetivo y evita oscilación cerca del umbral', () => {
    const control = new AdaptiveDprController();
    expect(feed(control, 46, 30)).toHaveLength(0);
    for (let i = 0; i < 10; i++) { feed(control, 43, 2.05); feed(control, 48, 2.05); }
    expect(control.value).toBe(.8);
  });
  it('no interpreta reposo, paneles o visibilidad suspendida como una GPU lenta', () => {
    const control = new AdaptiveDprController();
    feed(control, 20, 300, false);
    expect(control.value).toBe(.8);
    expect(control.fps).toBeNull();
    expect(feed(control, 30, 1)).toHaveLength(0);
    expect(control.value).toBe(.8);
  });
  it('exige margen continuado y descarta ventanas incompletas al suspender', () => {
    const control = new AdaptiveDprController();
    for (let i = 0; i < 12; i++) { feed(control, 60, 5); control.suspend(); }
    expect(control.value).toBe(.8);
    control.observe(NaN, true); control.observe(-1, true);
    expect(Number.isFinite(control.value)).toBe(true);
    expect(control.fps).toBeNull();
    expect(DPR_POLICY.targetFps).toBe(45);
  });
});
