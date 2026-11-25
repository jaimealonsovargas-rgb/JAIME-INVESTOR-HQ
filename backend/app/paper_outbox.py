"""Durable dispatch to JAIME's local PAPER venue. All fencing uses the lab database."""
from datetime import timedelta

from app.paper_intents import utc
from app.paper_simulator import KEY, PaperSimulator
from app.quant_store import digest


LEASE_SECONDS = 10
SUBMIT_FAULTS = ('OK', 'REJECT', 'DROP_BEFORE', 'DROP_AFTER')
LOOKUP_FAULTS = ('OK', 'UNAVAILABLE', 'NOT_VISIBLE')


def stamp(now):
    return now.isoformat(timespec='microseconds')


class PaperOutbox:
    def __init__(self, folder, clock=None):
        self.sim = PaperSimulator(folder, clock=clock)

    def entries(self):
        if not self.sim.path.exists():
            return []
        with self.sim.transaction() as db:
            return [dict(row) for row in db.execute('SELECT * FROM outbox ORDER BY rowid')]

    def history(self, client_order_id):
        if not self.sim.path.exists():
            return []
        with self.sim.transaction() as db:
            rows = db.execute('SELECT * FROM outbox_attempts WHERE client_order_id=? ORDER BY attempt',
                              (client_order_id,))
            return [dict(row) for row in rows]

    def _claim(self, worker):
        if not self.sim.path.exists():
            return None
        with self.sim.transaction() as db:
            now = utc(self.sim.clock())
            at = stamp(now)
            row = db.execute("""
                SELECT q.*, i.state FROM outbox q JOIN intents i ON i.client_id=q.client_order_id
                WHERE (q.status IN ('PENDING','UNCERTAIN') AND q.next_at<=?)
                   OR (q.status='CLAIMED' AND q.lease_until<=?)
                ORDER BY CASE q.status WHEN 'PENDING' THEN 1 ELSE 0 END, q.next_at, q.rowid LIMIT 1
            """, (at, at)).fetchone()
            if row is None:
                return None
            self.sim.advance(db, now)
            client = row['client_order_id']
            number = row['attempts'] + 1
            # Even the same worker name might now belong to a restarted process.
            event_id = 'outbox:' + digest([client, number])
            # v1 allowed callers to choose any event ID, including this prefix.
            while db.execute('SELECT 1 FROM events WHERE event_id=?', (event_id,)).fetchone():
                event_id = 'outbox:' + digest([event_id, client, number])
            action = 'LOOKUP' if row['status'] != 'PENDING' or row['state'] == 'UNKNOWN' else 'SUBMIT'
            until = stamp(now + timedelta(seconds=LEASE_SECONDS))
            if row['status'] == 'CLAIMED':
                db.execute("""UPDATE outbox_attempts SET disposition='LEASE_EXPIRED', finished_at=?
                              WHERE client_order_id=? AND attempt=?""", (at, client, row['attempts']))
            db.execute("""UPDATE outbox SET status='CLAIMED', attempts=?, owner=?, lease_until=?
                          WHERE client_order_id=?""", (number, worker, until, client))
            db.execute("""INSERT INTO outbox_attempts
                       (event_id,client_order_id,attempt,worker,action,claimed_at,lease_until)
                       VALUES (?,?,?,?,?,?,?)""", (event_id, client, number, worker, action, at, until))
            return dict(client_order_id=client, attempt=number, event_id=event_id, worker=worker, action=action)

    @staticmethod
    def _owns(db, claim, now):
        return db.execute("""SELECT 1 FROM outbox WHERE client_order_id=? AND status='CLAIMED'
                             AND owner=? AND attempts=? AND lease_until>?""",
                          (claim['client_order_id'], claim['worker'], claim['attempt'], stamp(now))).fetchone() is not None

    @staticmethod
    def _superseded(db, claim):
        row = db.execute("""SELECT q.status,i.state FROM outbox q JOIN intents i ON q.client_order_id=i.client_id
                            WHERE q.client_order_id=?""", (claim['client_order_id'],)).fetchone()
        return dict(**claim, **dict(row), reason='LEASE_LOST')

    def run_once(self, worker, *, submit_fault='OK', lookup_fault='OK', after_claim=None, after_delivery=None):
        """Process one eligible item. The hooks inject a process failure at either commit boundary."""
        KEY.validate_python(worker, strict=True)
        if submit_fault not in SUBMIT_FAULTS or lookup_fault not in LOOKUP_FAULTS:
            raise ValueError('INVALID_OUTBOX_SCENARIO')
        claim = self._claim(worker)
        if claim is None:
            return None
        if after_claim is not None:
            after_claim()

        with self.sim.transaction() as db:
            now = utc(self.sim.clock())
            if not self._owns(db, claim, now):
                return self._superseded(db, claim)
            # Here the venue is SQLite. Fence the simulated delivery itself as well as its acknowledgement.
            fault = submit_fault if claim['action'] == 'SUBMIT' else lookup_fault
            result = self.sim.record_event(db, claim['client_order_id'], claim['event_id'],
                                           claim['action'], {'fault': fault}, now)
            db.execute('UPDATE outbox_attempts SET delivered_at=? WHERE event_id=?',
                       (stamp(now), claim['event_id']))
        if after_delivery is not None:
            after_delivery()

        with self.sim.transaction() as db:
            now = utc(self.sim.clock())
            if not self._owns(db, claim, now):
                return self._superseded(db, claim)
            self.sim.advance(db, now)
            state = self.sim.row(db, claim['client_order_id'])['state']
            inconclusive = result['reason'] in ('LOOKUP_UNAVAILABLE', 'LOOKUP_NOT_VISIBLE')
            if state == 'UNKNOWN' or inconclusive:
                status = 'UNCERTAIN'
            elif state == 'READY':
                status = 'PENDING'
            else:
                status = 'DONE'
            # Space out repeated outages. The first retries take one second, capped at five minutes.
            delay = min(300, 2 ** min(9, max(0, claim['attempt'] - 3))) if status == 'UNCERTAIN' else 1
            next_at = '' if status == 'DONE' else stamp(now + timedelta(seconds=delay))
            db.execute("""UPDATE outbox SET status=?,next_at=?,owner=NULL,lease_until=NULL
                          WHERE client_order_id=?""", (status, next_at, claim['client_order_id']))
            db.execute('UPDATE outbox_attempts SET finished_at=?,disposition=? WHERE event_id=?',
                       (stamp(now), status, claim['event_id']))
            return dict(result, state=state, status=status, attempt=claim['attempt'])
