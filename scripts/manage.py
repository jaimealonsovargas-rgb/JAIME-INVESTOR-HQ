"""Comandos desde cualquier directorio, sin activar el virtualenv."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="JAIME INVESTOR HQ · herramientas locales P0")
    parser.add_argument("command", choices=["migrate", "backend", "frontend", "check", "audit", "portfolio-snapshot"])
    args = parser.parse_args()
    python = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.exists():
        raise SystemExit("Primero ejecuta: python scripts/setup.py")
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    env = {**os.environ, "PYTHONPATH": str(ROOT / "backend")}

    def run(*command):
        subprocess.run(command, cwd=ROOT, env=env, check=True)

    def frontend(*command):
        if not npm:
            raise SystemExit("npm no está disponible.")
        run(npm, "--prefix", "frontend", *command)

    if args.command == "migrate":
        run(str(python), "-m", "alembic", "upgrade", "head")
    elif args.command == "backend":
        run(str(python), "-m", "uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8000", "--no-access-log")
    elif args.command == "frontend":
        frontend("run", "dev")
    elif args.command == "check":
        run(str(python), "-m", "pytest")
        frontend("test")
        frontend("run", "build")
    elif args.command == "audit":
        run(str(python), "-m", "pip_audit")
        frontend("audit")
    elif args.command == 'portfolio-snapshot':
        run(str(python), str(ROOT / 'scripts' / 'portfolio_snapshot.py'))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None
