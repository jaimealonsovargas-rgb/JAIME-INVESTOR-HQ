"""Order contract, reservations and durable dispatch within the isolated PAPER lab."""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sqlite3

from pydantic import TypeAdapter

from app.paper_intents import OPEN, basis_of, intent_for, recheck, reviewable, reviewed_packet, utc, verified_receipt
from app.quant_store import canonical, digest
from app.risk_contracts import Name, Positive, Quantity, RiskInputs
from app.risk_engine import POLICY_HASH

APP_ID = 0x4A36534D
FORMAT = 2
MAX_ORDERS = 512
KEY = TypeAdapter(Name)
PRICE = TypeAdapter(Positive)
UNITS = TypeAdapter(Quantity)
DDL = (
    'CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)',
    'CREATE TABLE admissions (decision_id TEXT PRIMARY KEY, receipt TEXT NOT NULL)',
    '''CREATE TABLE intents (client_id TEXT PRIMARY KEY, spec TEXT NOT NULL, proposal TEXT NOT NULL,
       expires_at TEXT NOT NULL, state TEXT NOT NULL, filled INTEGER NOT NULL DEFAULT 0, filled_value TEXT NOT NULL DEFAULT '0',
       venue_state TEXT, venue_filled INTEGER NOT NULL DEFAULT 0, venue_value TEXT NOT NULL DEFAULT '0')''',
    '''CREATE TABLE events (event_id TEXT PRIMARY KEY, client_id TEXT NOT NULL REFERENCES intents(client_id),
       action TEXT NOT NULL, payload TEXT NOT NULL, recorded_at TEXT NOT NULL, response TEXT NOT NULL)''',
)

OUTBOX_DDL = (
    """CREATE TABLE outbox (
        client_order_id TEXT PRIMARY KEY REFERENCES intents(client_id),
        status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','CLAIMED','UNCERTAIN','DONE')),
        attempts INTEGER NOT NULL DEFAULT 0, next_at TEXT NOT NULL DEFAULT '',
        owner TEXT, lease_until TEXT,
        CHECK ((status='CLAIMED') = (owner IS NOT NULL AND lease_until IS NOT NULL))
    )""",
    """CREATE TABLE outbox_attempts (
        event_id TEXT PRIMARY KEY, client_order_id TEXT NOT NULL REFERENCES outbox(client_order_id),
        attempt INTEGER NOT NULL, worker TEXT NOT NULL, action TEXT NOT NULL,
        claimed_at TEXT NOT NULL, lease_until TEXT NOT NULL, delivered_at TEXT, finished_at TEXT,
        disposition TEXT, UNIQUE(client_order_id, attempt)
    )""",
)


def decoded(row):
    return dict(spec=json.loads(row['spec']), state=row['state'], filled=row['filled'], filled_value=row['filled_value'])


def public_order(row):
    order = decoded(row)
    spec = order['spec']
    remaining = spec['quantity'] - order['filled'] if order['state'] in OPEN else 0
    return dict(**order, reserved_cash=str(Decimal(spec['buffered_unit']) * remaining) if spec['side'] == 'BUY' else '0',
                reserved_shares=remaining if spec['side'] == 'SELL' else 0)


def admission(record, reason, ids=(), skipped=()):
    return dict(domain='LOCAL_SIMULATOR', decision_id=record['decision_id'], reason=reason,
                client_order_ids=list(ids), skipped=list(skipped), external_orders_enabled=False)


class PaperSimulator:
    def __init__(self, folder, clock=None):
        self.path = Path(folder).absolute() / 'b6-simulator.sqlite3'
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @contextmanager
    def transaction(self):
        # The database and its parent can first appear concurrently on Windows.
        # Inspect path components instead of resolving a path while SQLite is creating it.
        if ('..' in self.path.parts or str(self.path).startswith(('\\\\', '//'))
                or any(p.is_symlink() or p.is_junction() for p in (self.path, *self.path.parents))):
            raise ValueError('SIMULATOR_PATH_REDIRECTED')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=15)) as db, db:
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            app = db.execute('PRAGMA application_id').fetchone()[0]
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if app == 0 and version == 0 and not db.execute('SELECT 1 FROM sqlite_master LIMIT 1').fetchone():
                for query in (*DDL, *OUTBOX_DDL):
                    db.execute(query)
                db.execute(f'PRAGMA application_id={APP_ID}')
                db.execute(f'PRAGMA user_version={FORMAT}')
            elif (app, version) == (APP_ID, 1):
                for query in OUTBOX_DDL:
                    db.execute(query)
                db.execute("""INSERT INTO outbox(client_order_id,status)
                              SELECT client_id, CASE state WHEN 'READY' THEN 'PENDING'
                                WHEN 'UNKNOWN' THEN 'UNCERTAIN' ELSE 'DONE' END FROM intents""")
                db.execute(f'PRAGMA user_version={FORMAT}')
            elif (app, version) != (APP_ID, FORMAT):
                raise ValueError('NOT_A_B6_SIMULATOR_DATABASE')
            with localcontext() as ctx:
                ctx.prec = 64
                yield db

    @staticmethod
    def advance(db, now):
        stamp = now.isoformat(timespec='microseconds')
        last = db.execute("SELECT value FROM meta WHERE key='last_clock'").fetchone()
        if last and stamp < last[0]:
            raise ValueError('SIMULATOR_CLOCK_REVERSED')
        db.execute("INSERT OR REPLACE INTO meta VALUES ('last_clock',?)", (stamp,))
        # Only unsent intentions can release their reservation by local TTL.
        db.execute("UPDATE intents SET state='EXPIRED' WHERE state='READY' AND expires_at<=?", (stamp,))

    @staticmethod
    def row(db, client_id):
        row = db.execute('SELECT * FROM intents WHERE client_id=?', (client_id,)).fetchone()
        if row is None:
            raise ValueError('UNKNOWN_CLIENT_ORDER_ID')
        return row

    @staticmethod
    def existing(db, exclude=''):
        return [decoded(row) for row in db.execute('SELECT * FROM intents WHERE client_id!=? ORDER BY rowid', (exclude,))]

    def consume(self, cycle_id, record, review):
        verified_receipt(cycle_id, record)
        if record['outcome'] in ('OBSERVE', 'VETO'):
            return admission(record, record['reason'])
        with self.transaction() as db:
            prior = db.execute('SELECT receipt FROM admissions WHERE decision_id=?', (record['decision_id'],)).fetchone()
            if prior:
                return json.loads(prior[0])
            reason = reviewable(record, utc(self.clock()))
            if reason:
                return admission(record, reason)
            packet = reviewed_packet(record, review)
            basis = canonical(basis_of(packet))
            saved = db.execute("SELECT value FROM meta WHERE key='basis'").fetchone()
            if saved and saved[0] != basis:
                return admission(record, 'DIFFERENT_SIMULATION_SNAPSHOT')
            now = utc(self.clock())   # The disk verification may outlast the quote.
            self.advance(db, now)
            reason = reviewable(record, now)
            if reason:
                return admission(record, reason)
            existing = self.existing(db)
            if any(o['state'] == 'UNKNOWN' for o in existing):
                return admission(record, 'RECONCILIATION_REQUIRED')
            allowed = {(c['candidate_id'], c['listing_id']): c for c in record['cases']
                       if not c['veto'] and c['decision'] in ('BUY', 'SELL') and c['decision'] == c['requested']}
            consumed = {}
            for order in existing:
                spec = order['spec']
                approval_key = (spec['dossier_id'], spec['candidate_id'], spec['listing_id'], spec['committee_ref'])
                consumed[approval_key] = spec
            proposals, skipped = [], []
            for p in packet.proposals:
                case = allowed.get((p.candidate_id, p.listing_id))
                if case:
                    prior_order = consumed.get((record['dossier_id'], p.candidate_id, p.listing_id, p.committee_ref))
                    if prior_order:
                        if (p.side, p.quantity) != (prior_order['side'], prior_order['quantity']):
                            raise ValueError('CONFLICTING_COMMITTEE_APPROVAL')
                        skipped.append(dict(candidate_id=p.candidate_id, listing_id=p.listing_id,
                                           reasons=['APPROVAL_ALREADY_CONSUMED'], prior_order_id=prior_order['client_order_id']))
                        continue
                    if p.downside and p.side == 'BUY':
                        p = p.model_copy(update={'downside': p.downside.model_copy(
                            update={'stressed_exit': Decimal(case['downside']['stressed_exit'])})})
                    proposals.append(p)
            if not proposals:
                return admission(record, 'APPROVAL_ALREADY_CONSUMED' if skipped else 'NO_ACTIONABLE_CASES', skipped=skipped)
            if len(existing) + len(proposals) > MAX_ORDERS:
                raise ValueError('SIMULATOR_ORDER_BUDGET')
            cases = recheck(packet, existing, proposals, now, utc(datetime.fromisoformat(record['expires_at'])))
            by_listing = {asset.listing_id: asset for asset in packet.instruments}
            ids = []
            for proposal, case in zip(proposals, cases, strict=True):
                if case['veto']:
                    skipped.append(dict(candidate_id=proposal.candidate_id, listing_id=proposal.listing_id, reasons=case['reasons']))
                    continue
                spec = intent_for(record, case, proposal, by_listing[proposal.listing_id], packet.account.account_ref)
                expiry = utc(datetime.fromisoformat(spec['expires_at'])).isoformat(timespec='microseconds')
                db.execute('INSERT INTO intents(client_id,spec,proposal,expires_at,state) VALUES (?,?,?,?,?)',
                           (spec['client_order_id'], canonical(spec), proposal.model_dump_json(), expiry, 'READY'))
                db.execute('INSERT INTO outbox(client_order_id) VALUES (?)', (spec['client_order_id'],))
                ids.append(spec['client_order_id'])
            result = admission(record, 'INTENTS_RESERVED' if ids else 'RESERVATIONS_VETO', ids, skipped)
            # A transient reservation veto may be checked again; a successful batch has one immutable receipt.
            if ids:
                if not saved:
                    db.execute("INSERT INTO meta VALUES ('basis',?)", (basis,))
                db.execute('INSERT INTO admissions VALUES (?,?)', (record['decision_id'], canonical(result)))
            return result

    def get(self, client_id):
        with self.transaction() as db:
            self.advance(db, utc(self.clock()))
            return public_order(self.row(db, client_id))

    def history(self, client_id):
        with self.transaction() as db:
            self.row(db, client_id)
            return [dict(event_id=r[0], action=r[1], recorded_at=r[2], payload=json.loads(r[3]), result=json.loads(r[4]))
                    for r in db.execute('SELECT event_id,action,recorded_at,payload,response FROM events WHERE client_id=? ORDER BY rowid',
                                        (client_id,))]

    def _event(self, client_id, event_id, action, payload):
        with self.transaction() as db:
            if db.execute('SELECT 1 FROM outbox_attempts WHERE event_id=?', (event_id,)).fetchone():
                raise ValueError('SIMULATOR_EVENT_RESERVED_FOR_DISPATCH')
            return self.record_event(db, client_id, event_id, action, payload, utc(self.clock()))

    def record_event(self, db, client_id, event_id, action, payload, now):
        """Apply a venue operation and its receipt inside the caller's transaction."""
        KEY.validate_python(event_id, strict=True)
        body = canonical(payload)
        previous = db.execute('SELECT * FROM events WHERE event_id=?', (event_id,)).fetchone()
        if previous:
            if (previous['client_id'], previous['action'], previous['payload']) != (client_id, action, body):
                raise ValueError('SIMULATOR_EVENT_ID_CONFLICT')
            return json.loads(previous['response'])
        self.advance(db, now)
        row = self.row(db, client_id)
        if action == 'FILL':
            reason = self._fill(db, row, payload)
        elif action == 'FILL_NOTICE':
            linked = db.execute("SELECT 1 FROM events WHERE event_id=? AND client_id=? AND action='FILL'",
                                (payload['execution_id'], client_id)).fetchone()
            if not linked:
                raise ValueError('UNKNOWN_EXECUTION_ID')
            # A late notification reconciles to the current venue state, including any later cancel.
            self._publish(db, client_id)
            reason = 'FILL_REPORTED'
        elif action == 'SUBMIT':
            reason = self._submit(db, row, payload['fault'], now)
        elif action == 'LOOKUP':
            reason = self._lookup(db, row, payload['fault'], now)
        else:
            reason = self._end(db, row, action, payload['fault'])
        current = public_order(self.row(db, client_id))
        result = dict(event_id=event_id, action=action, reason=reason, state=current['state'],
                      filled=current['filled'], filled_value=current['filled_value'], client_order_id=client_id)
        db.execute('INSERT INTO events VALUES (?,?,?,?,?,?)',
                   (event_id, client_id, action, body, now.isoformat(), canonical(result)))
        return result

    def submit(self, client_id, attempt_id, fault='OK'):
        if fault not in ('OK', 'REJECT', 'DROP_BEFORE', 'DROP_AFTER'):
            raise ValueError('INVALID_SUBMIT_SCENARIO')
        return self._event(client_id, attempt_id, 'SUBMIT', {'fault': fault})

    def lookup(self, client_id, attempt_id, fault='OK'):
        if fault not in ('OK', 'UNAVAILABLE', 'NOT_VISIBLE'):
            raise ValueError('INVALID_LOOKUP_SCENARIO')
        return self._event(client_id, attempt_id, 'LOOKUP', {'fault': fault})

    def cancel(self, client_id, attempt_id, fault='OK'):
        if fault not in ('OK', 'DROP_BEFORE', 'DROP_AFTER'):
            raise ValueError('INVALID_CANCEL_SCENARIO')
        return self._event(client_id, attempt_id, 'CANCEL', {'fault': fault})

    def end_session(self, client_id, event_id):
        return self._event(client_id, event_id, 'SESSION_END', {'fault': 'OK'})

    def fill(self, client_id, execution_id, quantity, price, *, deliver=True):
        units = UNITS.validate_python(quantity)
        amount = PRICE.validate_python(price)
        if not units or type(deliver) is not bool:
            raise ValueError('INVALID_SIMULATED_FILL')
        result = self._event(client_id, execution_id, 'FILL', dict(quantity=units, price=format(amount.normalize(), 'f')))
        return self.deliver_fill(client_id, execution_id) if deliver else result

    def deliver_fill(self, client_id, execution_id):
        notice_id = 'notice:' + digest([client_id, execution_id])
        return self._event(client_id, notice_id, 'FILL_NOTICE', dict(execution_id=execution_id))

    @staticmethod
    def _publish(db, client_id):
        db.execute('UPDATE intents SET state=venue_state, filled=venue_filled, filled_value=venue_value WHERE client_id=?',
                   (client_id,))

    def _submit(self, db, row, fault, now):
        key, state = row['client_id'], row['state']
        if state != 'READY':
            return 'LOOKUP_REQUIRED' if state == 'UNKNOWN' else 'ALREADY_' + state
        other = self.existing(db, key)
        if any(o['state'] == 'UNKNOWN' for o in other):
            return 'RECONCILIATION_REQUIRED'
        spec = json.loads(row['spec'])
        if spec.get('policy_hash') != POLICY_HASH:
            db.execute("UPDATE intents SET state='REJECTED' WHERE client_id=?", (key,))
            return 'RISK_POLICY_CHANGED'
        basis = json.loads(db.execute("SELECT value FROM meta WHERE key='basis'").fetchone()[0])
        packet = RiskInputs.model_validate(dict(version='paper-risk-inputs-v1', dossier_id=spec['dossier_id'],
                                                **basis, proposals=[json.loads(row['proposal'])]))
        proposal, = packet.proposals
        if proposal.side == 'BUY':
            proposal = proposal.model_copy(update={'downside': proposal.downside.model_copy(
                update={'stressed_exit': Decimal(spec['stressed_exit'])})})
        case, = recheck(packet, other, [proposal], now, utc(datetime.fromisoformat(row['expires_at'])))
        if case['veto']:
            db.execute("UPDATE intents SET state='REJECTED' WHERE client_id=?", (key,))
            return 'RISK_VETO:' + ','.join(case['reasons'])
        if fault != 'DROP_BEFORE':
            venue_state = 'REJECTED' if fault == 'REJECT' else 'ACCEPTED'
            db.execute('UPDATE intents SET venue_state=? WHERE client_id=?', (venue_state, key))
        if fault.startswith('DROP_'):
            db.execute("UPDATE intents SET state='UNKNOWN' WHERE client_id=?", (key,))
            return 'SUBMIT_RESPONSE_MISSING'
        self._publish(db, key)
        return 'BROKER_' + venue_state

    def _lookup(self, db, row, fault, now):
        if fault != 'OK':
            return 'LOOKUP_' + fault
        if row['venue_state'] is not None:
            self._publish(db, row['client_id'])
            return 'RECONCILED'
        if row['state'] == 'UNKNOWN':
            # The fixture can prove absence. An unavailable or lagged query never releases a reservation.
            state = 'READY' if now < utc(datetime.fromisoformat(row['expires_at'])) else 'EXPIRED'
            db.execute('UPDATE intents SET state=? WHERE client_id=?', (state, row['client_id']))
        return 'SIMULATOR_CONFIRMED_ABSENT'

    def _end(self, db, row, action, fault):
        key = row['client_id']
        if action == 'CANCEL' and row['state'] == 'UNKNOWN':
            return 'LOOKUP_REQUIRED'
        if row['state'] not in OPEN:
            return 'ALREADY_' + row['state']
        target = 'CANCELED' if action == 'CANCEL' else 'EXPIRED'
        if row['venue_state'] is None:
            if row['state'] == 'UNKNOWN':
                return 'LOOKUP_REQUIRED'
            db.execute('UPDATE intents SET state=? WHERE client_id=?', (target, key))
            return 'LOCAL_' + target
        if fault != 'DROP_BEFORE' and row['venue_state'] in ('ACCEPTED', 'PARTIALLY_FILLED'):
            db.execute('UPDATE intents SET venue_state=? WHERE client_id=?', (target, key))
        if fault.startswith('DROP_'):
            db.execute("UPDATE intents SET state='UNKNOWN' WHERE client_id=?", (key,))
            return 'CANCEL_RESPONSE_MISSING'
        self._publish(db, key)
        return 'BROKER_' + self.row(db, key)['state']

    def _fill(self, db, row, payload):
        if row['venue_state'] not in ('ACCEPTED', 'PARTIALLY_FILLED'):
            raise ValueError('VENUE_NOT_FILLABLE')
        spec = json.loads(row['spec'])
        price, limit = Decimal(payload['price']), Decimal(spec['limit_price'])
        if (spec['side'] == 'BUY' and price > limit) or (spec['side'] == 'SELL' and price < limit):
            raise ValueError('FILL_OUTSIDE_LIMIT')
        total = row['venue_filled'] + payload['quantity']
        if total > spec['quantity']:
            raise ValueError('FILL_EXCEEDS_ORDER_QUANTITY')
        state = 'FILLED' if total == spec['quantity'] else 'PARTIALLY_FILLED'
        value = Decimal(row['venue_value']) + payload['quantity'] * price
        db.execute('UPDATE intents SET venue_state=?, venue_filled=?, venue_value=? WHERE client_id=?',
                   (state, total, str(value), row['client_id']))
        return 'FILL_RECORDED_AT_VENUE'
