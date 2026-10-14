"""Resumen de intervalos reales existentes; no ejecuta ni simula benchmarks."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/evidencias/P1_SIMS'


def worst_moving_window(intervals, duration_ms=5000):
    left = 0
    total = 0
    worst = None
    for right, interval in enumerate(intervals):
        total += interval
        while total - intervals[left] >= duration_ms:
            total -= intervals[left]
            left += 1
        if total >= duration_ms:
            fps = 1000 * (right - left + 1) / total
            worst = fps if worst is None else min(worst, fps)
    return worst


def main():
    rows = []
    for name in ('controles-fps-entrega80.json', 'controles-fps-combinado80.json'):
        document = json.loads((EVIDENCE / name).read_text(encoding='utf-8-sig'))
        for row in document['rows']:
            metrics = row['metrics']
            rows.append({'id': row['id'], 'evidence': name, 'at': row['at'],
                'moving_fps': metrics['movingFps'],
                'worst_moving_5s_fps': worst_moving_window(row['movingFrames']),
                'moving_p95_ms': metrics['movingFrameMsP95'],
                'moving_samples': metrics['movingSamples'],
                'dpr': metrics['dpr'], 'renderer': metrics['renderer'],
                'viewport': [metrics['width'], metrics['height']],
                'calls': metrics['calls'], 'triangles': metrics['triangles']})
    result = {'method': 'Consecutive moving-frame intervals, window >=5000ms; excludes paused dialogue; not a per-frame minimum.',
        'scenarios': rows,
        'measured_windows_pass_30': all(row['worst_moving_5s_fps'] is not None and row['worst_moving_5s_fps'] >= 30 for row in rows)}
    (EVIDENCE / 'resumen-fps-entrega.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'scenarios': len(rows), 'measured_windows_pass_30': result['measured_windows_pass_30']}))


if __name__ == '__main__':
    main()
