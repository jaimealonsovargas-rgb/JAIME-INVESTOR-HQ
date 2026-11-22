"""Comprueba un recibo de B5 en solo lectura o reproduce los escenarios sintéticos de B6."""
import argparse
from contextlib import closing, nullcontext
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from tempfile import TemporaryDirectory

from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app.config import Settings
from app.cycle_contracts import window
from app.dataset_manifests import canonical
from app.paper_simulator import PaperSimulator
from app.quant_store import digest
from app.risk_review import Binding, RiskReview
from app.storage_budget import MIB, StorageGovernor, StorageSettings


def check_cycle(cycle='latest', settings=None):
    if cycle != 'latest' and not re.fullmatch('[a-f0-9]{64}', cycle):
        raise ValueError('INVALID_CYCLE_ID')
    path = Path(make_url((settings or Settings()).database_url).database).resolve()
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        query = 'SELECT id, result FROM automation_cycles '
        if cycle == 'latest':
            row = db.execute(query + 'ORDER BY created_at DESC, id LIMIT 1').fetchone()
        else:
            row = db.execute(query + 'WHERE id=?', (cycle,)).fetchone()
    if row is None:
        raise ValueError('CYCLE_NOT_FOUND')
    risk = json.loads(row[1]).get('risk')
    if not risk:
        raise ValueError('CYCLE_PREDATES_RISK_RECEIPTS')
    data = path.parent
    output = ROOT / 'output' if data == ROOT / 'data' else data / 'storage-output'
    storage = StorageGovernor(data, output)
    simulator = PaperSimulator(output / 'paper-simulator' / 'reviewed')
    guard = storage.admission(reserve=MIB, destination='output') if risk.get('outcome') == 'ASSESSED' else nullcontext()
    with guard:
        result = simulator.consume(row[0], risk, RiskReview(storage))
    return dict(source='STORED_B5_CYCLE', cycle_id=row[0], **result)


def fixture_review(folder):
    fixture = json.loads((ROOT / 'integrations/paper_simulator/fixture.json').read_text(encoding='utf-8'))
    if fixture['provenance'] != 'SYNTHETIC_TEST':
        raise ValueError('SYNTHETIC_FIXTURE_REQUIRED')
    now = datetime.fromisoformat(fixture['clock'])
    storage = StorageGovernor(folder / 'data', folder / 'output', StorageSettings(_env_file=None))
    store = RiskReview(storage)
    dossier = fixture['dossier']
    dossier['policy_hash'] = digest(dossier['policy'])
    ident = store.store.publish(dossier)
    payload = canonical(dict(fixture['packet'], dossier_id=ident))
    packet_ref = hashlib.sha256(payload).hexdigest()
    store.root.mkdir(parents=True, exist_ok=True)
    (store.root / (packet_ref + '.json')).write_bytes(payload)
    review = RiskReview(storage, Binding(ident, packet_ref))
    cycle = digest(['B6', 'SYNTHETIC_TEST', now.isoformat()])
    return now, review, review.run(cycle, now, window(now)[1])


# Every action uses a stable command/execution ID. Each case starts with independent fixture capital.
SCENARIOS = {
    'aceptacion_y_ejecucion': [
        ('submit', ('envio',), {}, 'ACCEPTED'), ('fill', ('ejecucion', 10, '9.99'), {}, 'FILLED')],
    'rechazo': [('submit', ('envio', 'REJECT'), {}, 'REJECTED')],
    'respuesta_perdida_tras_aceptar': [
        ('submit', ('envio', 'DROP_AFTER'), {}, 'UNKNOWN'), ('submit', ('otro-envio',), {}, 'UNKNOWN'),
        ('lookup', ('consulta-sin-visibilidad', 'NOT_VISIBLE'), {}, 'UNKNOWN'),
        ('lookup', ('consulta',), {}, 'ACCEPTED'), ('cancel', ('cancelar',), {}, 'CANCELED')],
    'perdida_antes_de_llegar': [
        ('submit', ('envio', 'DROP_BEFORE'), {}, 'UNKNOWN'),
        ('lookup', ('consulta',), {}, 'READY'), ('submit', ('reintento',), {}, 'ACCEPTED')],
    'parcial_y_cancelacion': [
        ('submit', ('envio',), {}, 'ACCEPTED'), ('fill', ('ejecucion', 4, '9.99'), {}, 'PARTIALLY_FILLED'),
        ('cancel', ('cancelar', 'DROP_AFTER'), {}, 'UNKNOWN'), ('lookup', ('consulta',), {}, 'CANCELED')],
    'ejecucion_antes_de_cancelar': [
        ('submit', ('envio',), {}, 'ACCEPTED'), ('fill', ('ejecucion', 10, '10'), {'deliver': False}, 'ACCEPTED'),
        ('cancel', ('cancelar',), {}, 'FILLED'), ('deliver_fill', ('ejecucion',), {}, 'FILLED')],
    'fin_de_sesion': [
        ('submit', ('envio',), {}, 'ACCEPTED'), ('fill', ('ejecucion', 3, '10'), {}, 'PARTIALLY_FILLED'),
        ('end_session', ('cierre',), {}, 'EXPIRED')],
}


def demo():
    results = []
    with TemporaryDirectory(prefix='jaime-b6-') as temp:
        root = Path(temp)
        at, review, risk = fixture_review(root)
        if risk['outcome'] != 'ASSESSED':
            raise ValueError('FIXTURE_RISK_FAILED')
        for name, steps in SCENARIOS.items():
            folder = root / name
            def reopen():
                return PaperSimulator(folder, clock=lambda: at)
            sim = reopen()
            receipt = sim.consume(risk['cycle_id'], risk, review)
            key, = receipt['client_order_ids']
            for method, args, kwargs, expected in steps:
                event = getattr(sim, method)(key, *args, **kwargs)
                sim = reopen()
                replay = getattr(sim, method)(key, *args, **kwargs)
                if event != replay or event['state'] != expected:
                    raise ValueError('SCENARIO_REPLAY_FAILED')
            order = sim.get(key)
            history = sim.history(key)
            if reopen().consume(risk['cycle_id'], risk, review) != receipt or reopen().get(key) != order:
                raise ValueError('SCENARIO_RESTART_FAILED')
            results.append(dict(scenario=name, client_order_id=key, state=order['state'], filled=order['filled'],
                                filled_value=order['filled_value'], journal_events=len(history)))
    return dict(domain='LOCAL_SIMULATOR', source='SYNTHETIC_TEST', decision_id=risk['decision_id'],
                external_orders_enabled=False, scenarios=results, evidence_hash=digest(results))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group()
    choices.add_argument('--cycle', metavar='ID', default='latest', help='Ciclo local o latest (por defecto)')
    choices.add_argument('--demo', action='store_true', help='Ensayar los fallos del bróker ficticio')
    args = parser.parse_args(argv)
    try:
        report = demo() if args.demo else check_cycle(args.cycle)
    except (ValueError, KeyError, OSError, sqlite3.Error) as error:
        reason = str(error)
        print(json.dumps(dict(state='BLOCKED', reason=reason if re.fullmatch('[A-Z0-9_]+', reason) else 'SIMULATION_UNAVAILABLE',
                              external_orders_enabled=False)))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
