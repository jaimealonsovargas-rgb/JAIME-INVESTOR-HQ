"""Local pinned n8n runner. Secrets stay in .env and encrypted n8n credentials."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
VERSION = '2.46.6'
WORKFLOW = 'JAIMESecShadowV1'
PACKAGE = ROOT/'.tools/n8n/node_modules/n8n'


def configuration(prepare=False,node=None):
    path = ROOT/'.env'
    values = dotenv_values(path)
    additions = {}
    if prepare:
        for key in ('JAIME_CYCLE_TOKEN','N8N_ENCRYPTION_KEY'):
            if not values.get(key):
                additions[key] = secrets.token_urlsafe(48)
        if node:
            executable = Path(node).resolve(strict=True)
            # An explicit private copy avoids a dependency on the Codex runtime cache lifecycle.
            target = ROOT/'.tools/n8n-node/node.exe'
            target.parent.mkdir(parents=True,exist_ok=True)
            if target!=executable:
                shutil.copy2(executable,target)
            additions['N8N_NODE_PATH'] = target.as_posix()
        if additions:
            with path.open('a',encoding='utf-8') as stream:
                stream.write('\n# Coordinación local B2.5\n')
                for key,value in additions.items():
                    stream.write(key+'='+value+'\n')
            values.update(additions)
    if any(len(values.get(k) or '')<32 for k in ('JAIME_CYCLE_TOKEN','N8N_ENCRYPTION_KEY')):
        raise SystemExit('Falta preparar la autenticación local: ejecutar prepare.')
    executable = values.get('N8N_NODE_PATH') or shutil.which('node')
    if not executable or not PACKAGE.exists():
        raise SystemExit('Falta Node o n8n local. Ver integrations/n8n/README.md.')
    if json.loads((PACKAGE/'package.json').read_text())['version']!=VERSION:
        raise SystemExit('Versión n8n distinta del pin revisado.')
    return values,executable


def environment(values,node):
    # Do not inherit provider keys, prompts, proxy configuration or the rest of .env.
    keep = {'SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','USERPROFILE','HOMEDRIVE','HOMEPATH','APPDATA','LOCALAPPDATA','PROGRAMFILES','PATHEXT','PATH'}
    env = {k:v for k,v in os.environ.items() if k.upper() in keep}
    folder = ROOT/'data/n8n'
    folder.mkdir(parents=True,exist_ok=True)
    env.update(N8N_USER_FOLDER=str(folder),N8N_ENCRYPTION_KEY=values['N8N_ENCRYPTION_KEY'],
        N8N_HOST='127.0.0.1',N8N_LISTEN_ADDRESS='127.0.0.1',N8N_PORT='5678',
        N8N_EDITOR_BASE_URL='http://127.0.0.1:5678',N8N_PROTOCOL='http',N8N_SECURE_COOKIE='false',
        GENERIC_TIMEZONE='UTC',TZ='UTC',N8N_DIAGNOSTICS_ENABLED='false',N8N_VERSION_NOTIFICATIONS_ENABLED='false',
        N8N_TEMPLATES_ENABLED='false',N8N_COMMUNITY_PACKAGES_ENABLED='false',N8N_PUBLIC_API_DISABLED='true',
        N8N_DISABLED_MODULES='mcp-registry',
        N8N_PERSONALIZATION_ENABLED='false',N8N_BLOCK_ENV_ACCESS_IN_NODE='true',N8N_BLOCK_FILE_ACCESS_TO_N8N_FILES='true',N8N_PYTHON_ENABLED='false',
        NODES_INCLUDE=json.dumps(['n8n-nodes-base.'+n for n in ('manualTrigger','scheduleTrigger','httpRequest','wait','if')]),
        EXECUTIONS_MODE='regular',N8N_CONCURRENCY_PRODUCTION_LIMIT='1',
        EXECUTIONS_DATA_SAVE_ON_SUCCESS='none',EXECUTIONS_DATA_SAVE_ON_ERROR='none',
        EXECUTIONS_DATA_SAVE_ON_PROGRESS='false',EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS='false',
        EXECUTIONS_DATA_PRUNE='true',EXECUTIONS_DATA_MAX_AGE='168',EXECUTIONS_DATA_PRUNE_MAX_COUNT='1000',
        EXECUTIONS_TIMEOUT='1500',EXECUTIONS_TIMEOUT_MAX='1500')
    env['PATH'] = str(Path(node).parent)+os.pathsep+env.get('PATH','')
    return env


def main():
    parser = argparse.ArgumentParser(description='n8n Community local para JAIME B2.5')
    parser.add_argument('command',choices=['prepare','publish','unpublish','run','start'])
    parser.add_argument('--node',help='Ejecutable Node compatible, solo al preparar')
    args = parser.parse_args()
    values,node = configuration(args.command=='prepare',args.node)
    env = environment(values,node)
    def run(*command):
        subprocess.run([node,str(PACKAGE/'bin/n8n'),*command],cwd=ROOT,env=env,check=True)
    if args.command=='prepare':
        subprocess.run([node,str(ROOT/'integrations/n8n/check.cjs')],cwd=ROOT,env=env,check=True)
        credential = [dict(id='JAIMECycleCredentialV1',name='JAIME · ciclos locales',type='httpHeaderAuth',
            data=dict(name='Authorization',value='Bearer '+values['JAIME_CYCLE_TOKEN']))]
        # One temporary import file; never print the token or pass it as a CLI argument.
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',suffix='.json',dir=ROOT/'.tools',delete=False) as f:
            json.dump(credential,f);temp = Path(f.name)
        try:
            run('import:credentials','--input='+str(temp))
        finally:
            temp.unlink(missing_ok=True)
        run('import:workflow','--input='+str(ROOT/'integrations/n8n/sec-company-review.json'))
    elif args.command in ('publish','unpublish'):
        run(args.command+':workflow','--id='+WORKFLOW)
    elif args.command=='run':
        run('execute','--id='+WORKFLOW)
    else:
        run('start')


if __name__=='__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None
