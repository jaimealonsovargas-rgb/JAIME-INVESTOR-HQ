"""Manual, local-only llama.cpp launcher. Never downloads, never calls paid APIs."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
import socket

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / 'output/p4-runtime'
approved = json.loads((ROOT / 'assets/local-ai/manifest.json').read_text(encoding='utf-8'))
manifest = approved['selected_candidate']
parser = argparse.ArgumentParser()
parser.add_argument('--candidate', choices=('selected', 'qwen25', 'llama32'), default='selected')
parser.add_argument('--compact-thinking', action='store_true',
                    help='Experimento Qwen3: contexto 2048, reasoning 256, memoria acotada; sin descargas.')
parser.add_argument('--context', choices=(2048,4096), type=int, default=2048,
                    help='Contexto del experimento compact-thinking; no cambia el modelo.')
parser.add_argument('--repack', action='store_true', help='Reorganización CPU de pesos del mismo GGUF; puede aumentar RAM.')
options = parser.parse_args()
candidate = options.candidate
if options.compact_thinking and candidate != 'selected':
    raise SystemExit('COMPACT_THINKING_QWEN3_ONLY')
with socket.socket() as probe:
    probe.settimeout(1)
    if probe.connect_ex(('127.0.0.1', 8089)) == 0:
        raise SystemExit('LOCAL_RUNTIME_ALREADY_RUNNING: no cargar un segundo modelo.')
alias = 'Qwen3-1.7B-Q8_0'
if candidate == 'qwen25':
    # Previously downloaded and licensed Apache-2.0 candidate; no network/download.
    manifest = {'file': {'rfilename': 'qwen2.5-1.5b-instruct-q4_k_m.gguf', 'lfs': {
        'sha256': '6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e'}}}
    alias = 'Qwen2.5-1.5B-Instruct-Q4_K_M'
elif candidate == 'llama32':
    candidate_manifest = json.loads((ROOT/'assets/local-ai/llama32-candidate.json').read_text(encoding='utf-8'))
    manifest = {'file': {'rfilename': candidate_manifest['file'], 'lfs': {'sha256': candidate_manifest['sha256']}}}
    alias = 'Llama-3.2-3B-Instruct-Q4_K_M'
model = runtime / manifest['file']['rfilename']
if hashlib.file_digest(model.open('rb'), 'sha256').hexdigest() != manifest['file']['lfs']['sha256']:
    raise SystemExit('MODEL_HASH_MISMATCH')
binary = runtime / 'bin/llama-server.exe'
if not binary.is_file():
    raise SystemExit('NO_LOCAL_MODEL: preparar el runtime local documentado.')
with binary.open('rb') as stream:
    if hashlib.file_digest(stream, 'sha256').hexdigest() != approved['binary_sha256']:
        raise SystemExit('RUNTIME_HASH_MISMATCH')
args = [str(binary), '-m', str(model), '--alias', alias, '--host', '127.0.0.1', '--port', '8089',
        '-c', '4096', '-t', '3', '-tb', '3', '-np', '1', '--poll', '0', '--prio', '-1', '--no-webui',
        '--cors-origins', 'http://127.0.0.1:8089', '--no-cors-credentials', '--no-agent', '--no-slots', '--jinja', '--reasoning-budget', '0']
if options.compact_thinking:
    args[args.index('-c') + 1] = str(options.context)
    args[args.index('--reasoning-budget') + 1] = '256'
    args.extend(['--batch-size', '256', '--ubatch-size', '64', '--repack' if options.repack else '--no-repack'])
environment = {k:v for k,v in os.environ.items() if k.upper() in ('PATH','SYSTEMROOT','WINDIR','TEMP','TMP')}
with (runtime/'manual-server.log').open('ab') as log:
    process = subprocess.Popen(args, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
(runtime/'server.pid').write_text(str(process.pid), encoding='ascii')
print(f'llama.cpp local iniciado, PID {process.pid}; http://127.0.0.1:8089. Comprobar estado en Sistemas.')
