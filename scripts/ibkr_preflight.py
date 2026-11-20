"""Local prerequisites only. No imports of broker SDKs, sockets, credentials or account access."""
import argparse
from datetime import datetime, timezone
from importlib import metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def inspect(account_state='unknown'):
    packages = {}
    for name in ('ibapi', 'protobuf'):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None
    candidates = [Path('C:/Jts'), Path('C:/IBJts'), Path.home()/'Jts', Path.home()/'IBJts', ROOT/'tws']
    detected = [str(path) for path in candidates if path.is_dir()]
    reasons = []
    if account_state != 'paper_declared':
        reasons.append('ACCOUNT_ABSENT' if account_state == 'absent' else 'PAPER_ACCESS_UNVERIFIED')
    if not detected:
        reasons.append('APPLICATION_NOT_FOUND_IN_STANDARD_PATHS')
    if packages['ibapi'] is None:
        reasons.append('OFFICIAL_SDK_NOT_INSTALLED')
    reasons += ['SESSION_NOT_VERIFIED', 'READ_ONLY_NOT_VERIFIED', 'DATA_RIGHTS_NOT_VERIFIED',
                'ZERO_COST_COVERAGE_NOT_VERIFIED', 'SDK_COMPATIBILITY_NOT_TESTED']
    return dict(version='ibkr-local-preflight-v1', checked_at=datetime.now(timezone.utc).isoformat(),
        state='NOT_READY', account_state_declared=account_state, account_verified=False,
        python=sys.version.split()[0], packages=packages, standard_paths_present=detected,
        reasons=reasons, connected=False, network_requests=0, orders_enabled=False,
        note='Rutas estándar y metadatos locales solamente. Una carpeta no acredita instalación '
             'operativa; una declaración no acredita cuenta, sesión, derechos ni coste cero.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--account-state', choices=('unknown','absent','paper_declared'), default='unknown',
                        help='Declaración del usuario, nunca validación de cuenta')
    parser.add_argument('--output', help='Informe privado nuevo dentro de output/')
    args = parser.parse_args()
    report = inspect(args.account_state)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        target = Path(args.output).resolve()
        if not target.is_relative_to((ROOT/'output').resolve()):
            parser.error('El informe privado debe quedar en output/.')
        sys.path.insert(0, str(ROOT/'backend'))
        from app.config import Settings
        from app.storage_budget import StorageGovernor, MIB
        from sqlalchemy.engine import make_url
        data_root = Path(make_url(Settings().database_url).database).parent
        with StorageGovernor(data_root, ROOT/'output').admission(
                reserve=len(encoded.encode('utf-8'))+MIB, destination='output'):
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('x', encoding='utf-8') as stream:
                stream.write(encoded)
    print(encoded)


if __name__ == '__main__':
    main()
