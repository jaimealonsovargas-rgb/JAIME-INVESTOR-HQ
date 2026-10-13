"""Inventario reproducible desde METADATA instalado y package-lock, sin credenciales."""
from importlib.metadata import distributions
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Normalizaciones verificadas contra los textos LICENSE de los paquetes instalados.
NORMALIZED = {"colorama": "BSD-3-Clause", "pip_api": "Apache-2.0", "pip_audit": "Apache-2.0", "sortedcontainers": "Apache-2.0"}
lines = [
    "# Licencias y dependencias P0", "",
    "Verificación: 2026-10-13. Inventario generado por `scripts/license_inventory.py` desde los paquetes instalados y el lockfile npm. Incluye herramientas de desarrollo/auditoría y dependencias transitivas; no implica haber conectado proveedores financieros.", "",
    "## Entorno y uso local", "",
    "- Node 26.3.0: [MIT y avisos de terceros](https://github.com/nodejs/node/blob/v26.3.0/LICENSE).",
    "- Python 3.14.4: [PSF-2.0 y licencias incorporadas](https://docs.python.org/3.14/license.html).",
    "- SQLite: [dominio público](https://sqlite.org/copyright.html). Versión efectiva registrada en STATUS.md.",
    "- uv 0.13.0 (bootstrap en .tools): [MIT o Apache-2.0](https://pypi.org/project/uv/0.13.0/).",
    "- Playwright CLI: herramienta de verificación externa al producto, [Apache-2.0](https://github.com/microsoft/playwright-cli). No es dependencia de ejecución.",
    "- Fuentes: pila del sistema; no se redistribuyen archivos tipográficos. Icono J: SVG propio. Sin assets 3D ni imágenes externas en P0.",
    "- Uso local de las dependencias sin suscripción ni licencia de pago obligatoria. Mantener los avisos de terceros si se redistribuyen sus binarios. MPL-2.0 de certifi se conserva en su paquete; no se ha modificado.", "",
    "## Python", "", "Fuente: METADATA/LICENSE de cada wheel descargado de PyPI. Versiones y hashes fijados en uv.lock.", "",
    "| Paquete | Versión | Licencia declarada/verificada |", "|---|---|---|",
]
for dist in sorted(distributions(), key=lambda item: item.metadata["Name"].lower()):
    meta = dist.metadata
    name, version = meta["Name"], meta["Version"]
    license = NORMALIZED.get(name.lower()) or meta.get("License-Expression") or meta.get("License")
    if not license:
        license = "; ".join(c.split(" :: ")[-1] for c in meta.get_all("Classifier", []) if c.startswith("License ::"))
    if not license or len(license) > 150:
        raise RuntimeError(f"Revisión manual de licencia pendiente: {name}")
    lines.append(f"| [{name}](https://pypi.org/project/{name}/{version}/) | {version} | {license} |")
lines += ["", "## npm", "", "Fuente: campos license/resolved/integrity de package-lock.json publicados por los paquetes. Incluye variantes opcionales por plataforma, aunque no se instalen en Windows.", "", "| Paquete | Versión | Licencia declarada |", "|---|---|---|"]
lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
for path, meta in sorted(lock["packages"].items()):
    if not path:
        continue
    name = path.split("node_modules/")[-1]
    if not meta.get("license"):
        raise RuntimeError(f"Revisión manual de licencia pendiente: {name}")
    lines.append(f"| [{name}](https://www.npmjs.com/package/{name}/v/{meta['version']}) | {meta['version']} | {meta['license']} |")
lines += ["", "## Fuentes técnicas consultadas", "",
    "- [Requisitos de Vite](https://vite.dev/guide/): runtime compatible; probado en el Node instalado.",
    "- [FastAPI local](https://fastapi.tiangolo.com/deployment/manually/), [SQLite/SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html), [lock y sincronización uv](https://docs.astral.sh/uv/concepts/projects/sync/).",
    "- [Alpaca Paper](https://docs.alpaca.markets/us/docs/paper-trading) y [Trading 212](https://docs.trading212.com/api): solo validación documental de hosts. Acceso, cuotas, cobertura y derechos de datos NO comprobados; proveedores NO DISPONIBLES en P0.", "",
]
(ROOT / "docs/LICENCIAS_P0.md").write_text("\n".join(lines), encoding="utf-8")
print("Inventario de licencias generado.")
