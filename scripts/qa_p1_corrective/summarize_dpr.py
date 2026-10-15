"""Summarize measured moving frames; synthetic controller tests are not inputs."""
import json
import math
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[2] / 'docs/evidencias/P1_PULIDO_ADAPTATIVO'
data = json.loads((EVIDENCE / 'comparacion-fijo-adaptativo.json').read_text(encoding='utf-8-sig'))


def worst_five_seconds(frames):
    total = 0
    start = 0
    values = []
    for end, frame in enumerate(frames):
        total += frame
        while start < end and total - frames[start] >= 5000:
            total -= frames[start]
            start += 1
        if total >= 5000:
            values.append(1000 * (end - start + 1) / total)
    return min(values) if values else None


rows = []
for row in data['results']:
    frames = row['movingFrames']
    assert len(frames) >= 100 and not row['metrics']['hidden']
    rows.append({
        'profile': row['profile'], 'room': row['id'],
        'moving_fps': 1000 * len(frames) / sum(frames),
        'moving_p95_ms': sorted(frames)[math.ceil(.95 * len(frames)) - 1],
        'worst_moving_5s_fps': worst_five_seconds(frames),
        'moving_samples': len(frames), 'moving_seconds': sum(frames) / 1000,
        'dpr': row['resolution']['dpr'], 'calls': row['metrics']['calls'],
    })
changes = {}
for sample in data['warmup'] + [{'resolution': r['resolution']} for r in data['results'] if r['profile'] == 'adaptive']:
    for change in sample['resolution']['changes']:
        changes[change['at']] = change
summary = {
    'at': data['at'], 'method': data['method'],
    'renderer': data['results'][0]['metrics']['renderer'],
    'viewport': [data['results'][0]['metrics']['width'], data['results'][0]['metrics']['height']],
    'rows': rows, 'changes': list(changes.values()),
    'dom_before': data['domBefore'], 'dom_after': data['domAfter'],
    'paused_dpr': data['paused']['dpr'],
}
(EVIDENCE / 'rendimiento-resumen.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for row in rows:
    print(f"{row['profile']:13} {row['room']:10} {row['moving_fps']:6.2f} FPS; peor 5s {row['worst_moving_5s_fps']:6.2f}; DPR {row['dpr']:.2f}")
print('DPR changes:', len(changes), 'DOM equal:', data['domBefore'] == data['domAfter'])
