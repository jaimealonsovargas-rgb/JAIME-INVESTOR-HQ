"""Orquestación local de auditoría estática. No importa runtimes de trading."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/evidencias/P2/integraciones'
OUT.mkdir(parents=True,exist_ok=True)
env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','COMSPEC','PATHEXT','USERPROFILE'}}


def run(command,name):
    with (OUT/name).open('w',encoding='utf-8') as log:
        result=subprocess.run([str(x) for x in command],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    if result.returncode:raise RuntimeError(f'{name}: exit {result.returncode}')


vibe=ROOT/'.venv-vibe/Scripts/python.exe'
if not vibe.exists():run([sys.executable,'-m','venv','--without-pip',ROOT/'.venv-vibe'],'vibe-create.txt')
uv=ROOT/'.tools/Scripts/uv.exe'
run([uv,'pip','install','--python',vibe,'PyYAML==6.0.3'],'vibe-install.txt')
run([vibe,'-I','scripts/audit_vibe_metadata.py','--source','output/audit-vibe-trading','--output',OUT/'vibe-metadata.json'],'vibe-evaluation.txt')
ar=ROOT/'.venv-agent-reach/Scripts/python.exe'
run([uv,'pip','install','--python',ar,'pip==26.2.1'],'agent-reach-pip-update.txt')
run([ar,'-I','scripts/audit_agent_reach.py','--source','output/audit-agent-reach','--output',OUT/'agent-reach-rss-doctor.json'],'agent-reach-evaluation.txt')
for tool,python in [('agent-reach',ar),('vibe',vibe)]:
    run([uv,'pip','list','--python',python,'--format','json'],tool+'-installed-sbom.txt')
    # Audit del subconjunto instalado, no del grafo completo sin instalar.
    run([sys.executable,'-m','pip_audit','--path',python.parent.parent/'Lib/site-packages'],tool+'-dependency-audit.txt')
manifest=[]
notices=ROOT/'assets/integrations';notices.mkdir(parents=True,exist_ok=True)
for name in ['agent-reach','vibe-trading']:
    repo=ROOT/'output'/('audit-'+name)
    sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],env=env).decode().strip()
    for file in ['LICENSE',*(['NOTICE'] if name=='vibe-trading' else [])]:
        raw=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+file],env=env)
        target=notices/(name+'-'+file+'.txt');target.write_bytes(raw)
        manifest.append({'project':name,'commit':sha,'path':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()})
(notices/'licenses.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Auditorías limitadas terminadas; runtimes de brokers/modelos no habilitados.')
