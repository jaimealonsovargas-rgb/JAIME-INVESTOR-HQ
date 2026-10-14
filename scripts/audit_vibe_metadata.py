"""Audita metadatos YAML del pin Vibe sin importar su runtime ni instalar SDKs.

Ejecutar con .venv-vibe (solo PyYAML). No ejecuta prompts, herramientas, loaders,
Python generado ni brokers. Exporta inventario, nunca presets ejecutables.
"""
import argparse
import hashlib
import json
import subprocess
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path
import yaml

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()


def git(*command):
    return subprocess.check_output(['git','-C',str(args.source),*command],timeout=30)


commit=git('rev-parse','HEAD').decode().strip()
project=tomllib.loads(git('show','HEAD:pyproject.toml').decode())['project']
paths=git('ls-tree','-r','--name-only','HEAD').decode().splitlines()
paths=[p for p in paths if p.startswith('agent/src/swarm/presets/') and p.endswith('.yaml')]
rows=[]
for path in sorted(paths):
    raw=git('show','HEAD:'+path)
    if len(raw)>200000:raise ValueError('Preset fuera del presupuesto')
    preset=yaml.safe_load(raw)
    agents=preset.get('agents',[])
    tools=sorted({t for a in agents for t in a.get('tools',[])})
    rows.append({'id':preset['name'],'title':preset.get('title',preset['name']),
        'upstream_path':path,'sha256':hashlib.sha256(raw).hexdigest(),
        'role_count':len(agents),'upstream_tools':tools,
        'state':'METADATA_ONLY','enabled':False,
        'reason':'Herramientas upstream no autorizadas; requiere adaptación y QA P4/P5.'})
# Benchmark real de parsing, no backtest/rentabilidad ni inferencia IA.
fixture=b'name: TEST_ONLY\nagents: [{id: TEST_ONLY, tools: [read_cached]}]\n'
start=time.perf_counter()
for _ in range(1000):assert yaml.safe_load(fixture)['name']=='TEST_ONLY'
result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'upstream_commit':commit,
    'version':project['version'],'license':project['license'],'dependencies_declared':project['dependencies'],
    'upstream_presets_found':len(rows),'catalogued_presets':rows[:30],
    'runtime_installed':False,'runtime_imported':False,'executed_agents':False,
    'broker_tools_enabled':False,'generated_python_enabled':False,
    'benchmark':{'kind':'TEST_ONLY YAML parse x1000','seconds':time.perf_counter()-start},
    'decision':'METADATA_ONLY; full runtime blocked until dependency/tool/network sandbox audit'}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
