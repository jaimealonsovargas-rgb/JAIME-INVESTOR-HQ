"""Evaluación limitada del pin inspeccionado: solo canal RSS, sin cookies ni red.

Ejecutar con .venv-agent-reach, no el entorno de la aplicación. La ingesta HTTP
real utiliza exclusivamente el cliente allowlisted de JAIME, no doctor.
"""
import argparse
import io
import json
import socket
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.source.resolve()))

from agent_reach import cli, doctor
from agent_reach.config import Config
from agent_reach.channels.rss import RSSChannel

config_path = args.output.resolve().parent / 'agent-reach-empty-config.yaml'
config = Config(config_path=config_path, read_only=True)


def deny(*_a, **_k):
    raise RuntimeError('Red/subprocesos prohibidos durante la auditoría RSS.')


text = io.StringIO()
# Limitar el doctor, no autorizar todas las redes por existir en el registry.
with patch.object(socket.socket, 'connect', deny), patch('subprocess.run', deny), \
     patch.object(doctor, 'get_all_channels', lambda: [RSSChannel()]), \
     patch('agent_reach.config.Config', lambda *a, **k: config), redirect_stdout(text):
    cli._cmd_install(argparse.Namespace(env='local', safe=True, dry_run=True, channels='', proxy=None))
    cli._cmd_install(argparse.Namespace(env='local', safe=True, dry_run=False, channels='', proxy=None))
    result = doctor.check_all(config)

args.output.write_text(json.dumps({'restricted_to': ['rss'], 'network_allowed': False,
    'browser_cookies': False, 'config_created': config_path.exists(),
    'doctor': result, 'safe_dry_run_output': text.getvalue()}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
assert not config_path.exists() and result['rss']['status'] == 'ok'
