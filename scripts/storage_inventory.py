"""Read-only inventory and preservation manifest; no deletion or data downloads."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app.config import Settings
from app.storage_budget import StorageGovernor, scan_tree, MIB
from sqlalchemy.engine import make_url


def inventory(governor, *, project_root=ROOT, runtimes=False):
    status = governor.status()
    files, domains = [], {}
    for label, root in [('data', governor.data_root), ('output', governor.output_root)]:
        scan = scan_tree(root, exclude=(governor.output_root,) if label=='data' else (), entries=True,
                         runtime_roots=governor.runtime_roots)
        for row in scan.pop('entries'):
            path = Path(row['path'])
            group = ('backups' if label=='output' and path.suffix in ('.db','.sqlite','.sqlite3') else
                     label+'/'+(path.parts[0] if len(path.parts)>1 else 'root'))
            domain = domains.setdefault(group, dict(bytes=0, files=0))
            domain['bytes'] += row['bytes']; domain['files'] += 1
            files.append(dict(**row, root=label, retention='PRESERVE', automatic_deletion=False))
    runtime = {}
    if runtimes:
        for name in ('.tools','.venv','.venv-agent-reach','.venv-vibe','frontend/node_modules'):
            runtime[name] = scan_tree(project_root/name)
    return dict(version='storage-inventory-v1', measured_at=datetime.now(timezone.utc).isoformat(),
        status=status, domains=domains, runtimes=runtime, files=files,
        note='Inventario de conservación, no lista de borrado. Sin contenidos de archivos ni secretos. '
             'Los tamaños son lógicos; enlaces desconocidos impiden admitir captación. '
             'Entornos fuera del presupuesto de datos, incluidos en el margen libre del disco.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='Informe privado nuevo dentro de output/')
    parser.add_argument('--include-runtimes', action='store_true')
    args = parser.parse_args()
    target = Path(args.output).resolve()
    if not target.is_relative_to((ROOT/'output').resolve()):
        parser.error('El inventario privado debe quedar dentro de output/.')
    data = Path(make_url(Settings().database_url).database).parent
    guard = StorageGovernor(data, ROOT/'output')
    report = inventory(guard, runtimes=args.include_runtimes)
    encoded = json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8')
    # A blocked acquisition must still allow a small diagnostic export if that file itself fits.
    with guard.admission(reserve=len(encoded)+MIB, destination='output'):
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(encoded)
    print(json.dumps({k:report[k] for k in ('version','measured_at','status','domains','runtimes')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
