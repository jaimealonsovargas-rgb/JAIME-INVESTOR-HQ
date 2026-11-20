"""Valida la campaña local revisada o consulta su expediente por hash."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import sys
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.b4_campaign import validate_archived_campaign
from app.config import Settings
from app.proposer_view import proposer_view
from app.storage_budget import StorageGovernor
from app.validation_store import ValidationStore


def markdown_report(report, dossier_id):
    def percent(value):
        return f'{Decimal(value) * 100:.2f} %'.replace('.', ',')

    names = {'cash': 'Efectivo', 'buy_hold': 'Comprar y mantener'}
    for hypothesis in report['hypotheses']:
        names[hypothesis['id']] = hypothesis['id'].upper()
    lines = ['# Validación de estrategias · ' + report['source']['symbol'], '',
             f"**{report['decision']['status']}** · {report['search']['recorded_trials']} ensayos · "
             f"{len(report['decision']['candidate_ids'])} candidatas para revisión.", '',
             f"Evaluación de {report['evaluation']['first']} a {report['evaluation']['last']}. "
             f"{report['evaluated_sessions']} sesiones evaluadas y {report['reserved_oos_sessions']} reservadas.", '',
             '| Variante | Costes | Resultado neto | Caída máxima | Operaciones simuladas |',
             '|---|---|---:|---:|---:|']
    indexed = {trial['trial_id'][len(report['run_id']) + 1:]: trial for trial in report['trials']}
    variants = [h['id'] for h in report['hypotheses']] + report['search']['benchmarks']
    for key, scenario in ((key, cost) for key in variants for cost in report['search']['scenarios']):
        trial = indexed[key + '-' + scenario]
        m = trial['metrics']
        row = [names[key], {'base': 'Base', 'adverse': 'Adversos'}[scenario]]
        row.extend([percent(m['return_fraction']), percent(m['max_drawdown_fraction']), str(m['fill_count'])]
                   if trial['state'] == 'COMPLETED' else [trial['state'], '—', '—'])
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.extend(['', '## Criterios de selección', ''])
    explanations = {'NET_RETURN_NOT_ABOVE_CASH': 'la rentabilidad neta no supera al efectivo',
                    'NET_RETURN_NOT_ABOVE_BUY_HOLD': 'la rentabilidad neta no supera a comprar y mantener',
                    'DRAWDOWN_ABOVE_BUY_HOLD': 'la caída máxima supera a la de comprar y mantener'}
    for h in report['hypotheses']:
        for cost, stages in h['comparisons'].items():
            for stage, check in stages.items():
                reasons = [explanations[r] for r in check['reasons']]
                outcome = ', '.join(reasons) if reasons else 'cumple los criterios económicos'
                lines.append(f"- **{names[h['id']]}** ({'base' if cost == 'base' else 'adversos'}, "
                             f"{'exploración' if stage == 'exploration' else stage}) · {outcome}.")
    if not report['reserved_oos_sessions']:
        lines.extend(['', 'Las sesiones de calentamiento y evaluación ya se habían examinado. '
                      'La evidencia independiente es insuficiente para estimar significación.'])
    lines.extend(['', f'Expediente `{dossier_id}`.', f"Manifiesto `{report['source']['manifest_id']}`."])
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--show', metavar='SHA256', help='Leer la decisión archivada y verificar su integridad')
    parser.add_argument('--format', choices=('json', 'markdown', 'proposer'), default='json',
                        help='Resumen, informe privado o contexto de diseño para el generador')
    args = parser.parse_args(argv)
    db = Path(make_url(Settings().database_url).database)
    storage = StorageGovernor(db.parent, ROOT / 'output' if db.parent == ROOT / 'data' else db.parent / 'storage-output')
    store = ValidationStore(storage)
    try:
        if args.show:
            dossier_id = args.show
            report = store.read(dossier_id)
        else:
            report = validate_archived_campaign(db, storage)
            dossier_id = store.publish(report)
        if args.format == 'proposer':
            print(json.dumps(proposer_view(report), indent=2))
            return 0
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error, ArithmeticError) as error:
        # No source data, SQL values, invalid inputs or provider secrets on stdout.
        reason = str(error) if isinstance(error, ValueError) and str(error).replace('_', '').isupper() else type(error).__name__
        print(json.dumps(dict(status='VALIDATION_UNAVAILABLE', reason=reason, orders_enabled=False)), file=sys.stderr)
        return 2
    if args.format == 'markdown':
        if not sys.stdout.isatty() and hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        print(markdown_report(report, dossier_id), end='')
        return 0
    print(json.dumps(dict(dossier_id=dossier_id, file=str(store.path(dossier_id)), run=report['run_id'],
                          trials=report['search']['recorded_trials'], hypotheses=report['search']['hypotheses'],
                          economic_support=sum(h['economic_screen_passed'] for h in report['hypotheses']),
                          reserved_oos_sessions=report['reserved_oos_sessions'],
                          statistical_evidence=sorted({h['statistical_evidence'] for h in report['hypotheses']}),
                          decision=report['decision']), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
