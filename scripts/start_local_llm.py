"""Manual, local-only llama.cpp launcher. Never downloads, never calls paid APIs."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / 'output/p4-runtime'
approved = json.loads((ROOT / 'assets/local-ai/manifest.json').read_text(encoding='utf-8'))
manifest = approved['selected_candidate']
model = runtime / manifest['file']['rfilename']
if hashlib.file_digest(model.open('rb'), 'sha256').hexdigest() != manifest['file']['lfs']['sha256']:
    raise SystemExit('MODEL_HASH_MISMATCH')
binary = runtime / 'bin/llama-server.exe'
if not binary.is_file():
    raise SystemExit('NO_LOCAL_MODEL: preparar el runtime local documentado.')
with binary.open('rb') as stream:
    if hashlib.file_digest(stream, 'sha256').hexdigest() != approved['binary_sha256']:
        raise SystemExit('RUNTIME_HASH_MISMATCH')
args = [str(binary), '-m', str(model), '--alias', 'Qwen3-1.7B-Q8_0', '--host', '127.0.0.1', '--port', '8089',
        '-c', '4096', '-t', '3', '-tb', '3', '-np', '1', '--poll', '0', '--prio', '-1', '--no-webui',
        '--cors-origins', 'http://127.0.0.1:8089', '--no-cors-credentials', '--no-agent', '--no-slots', '--jinja', '--reasoning-budget', '0']
environment = {k:v for k,v in os.environ.items() if k.upper() in ('PATH','SYSTEMROOT','WINDIR','TEMP','TMP')}
with (runtime/'manual-server.log').open('ab') as log:
    process = subprocess.Popen(args, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
(runtime/'server.pid').write_text(str(process.pid), encoding='ascii')
print(f'llama.cpp local iniciado, PID {process.pid}; http://127.0.0.1:8089. Comprobar estado en Sistemas.')
