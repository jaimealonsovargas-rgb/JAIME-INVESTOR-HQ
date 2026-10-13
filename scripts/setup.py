"""Instalación local reproducible; no modifica la política de PowerShell."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    if sys.version_info[:2] != (3, 14):
        raise SystemExit("P0 requiere Python 3.14.x. No se descargan intérpretes automáticamente.")
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    if not npm:
        raise SystemExit("Instala Node.js y npm antes de continuar.")
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    python_name = "python.exe" if sys.platform == "win32" else "python"
    tool_python = ROOT / ".tools" / bin_dir / python_name
    if not tool_python.exists():
        run(sys.executable, "-m", "venv", str(ROOT / ".tools"))
    run(str(tool_python), "-m", "pip", "install", "uv==0.13.0")
    run(str(tool_python), "-m", "uv", "sync", "--locked", "--no-python-downloads")
    run(npm, "--prefix", "frontend", "ci", "--no-fund")
    env = ROOT / ".env"
    if not env.exists():
        env.write_bytes((ROOT / ".env.example").read_bytes())
    run(str(ROOT / ".venv" / bin_dir / python_name), "scripts/manage.py", "migrate")
    print("Base instalada. Ejecuta python scripts/manage.py check antes de arrancar.")


if __name__ == "__main__":
    main()
