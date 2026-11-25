"""Reconcile the isolated simulator's execution journal, OMS and venue in one SQLite snapshot."""
from collections import defaultdict
from decimal import Decimal
import json
from typing import NamedTuple

from app.paper_intents import public_order, utc
from app.paper_venue import PRICE, UNITS, money, opening_account, venue_account
from app.quant_store import digest


class Filled(NamedTuple):
    quantity: int = 0
    value: Decimal = Decimal(0)

    def plus(self, quantity, price):
        return Filled(self.quantity + quantity, self.value + quantity * price)

    def report(self):
        return dict(quantity=self.quantity, value=money(self.value))


def venue_state_agrees(state, filled, ordered):
    if state in (None, 'ACCEPTED', 'REJECTED'):
        return filled == 0
    if state in ('CANCELED', 'EXPIRED'):
        return 0 <= filled < ordered
    if state == 'PARTIALLY_FILLED':
        return 0 < filled < ordered
    return state == 'FILLED' and filled == ordered


def journal(db):
    # Local receipts carry cumulative order state. Only the linked execution carries trade economics.
    fills = defaultdict(dict)
    receipts = defaultdict(set)
    invalid = defaultdict(list)
    rows = db.execute("""SELECT client_id, event_id, action, payload FROM events
                         WHERE action IN ('FILL','FILL_NOTICE','FILL_RECOVERED') ORDER BY rowid""")
    for client, event, action, raw in rows:
        try:
            payload = json.loads(raw)
            if action == 'FILL':
                quantity = UNITS.validate_python(payload['quantity'])
                price = PRICE.validate_python(payload['price'])
                if not quantity:
                    raise ValueError('EMPTY_EXECUTION')
                fills[client][event] = (quantity, price)
            else:
                execution = payload['execution_id']
                if not isinstance(execution, str):
                    raise ValueError('INVALID_EXECUTION_REFERENCE')
                receipts[client].add(execution)
        except (ValueError, KeyError, TypeError):
            invalid[client].append(event)
    return fills, receipts, invalid


def order_view(row, fills, receipts, invalid, differences):
    client = row['client_id']
    order = public_order(row)
    spec = order['spec']
    local = Filled(row['filled'], Decimal(row['filled_value']))
    venue = Filled(row['venue_filled'], Decimal(row['venue_value']))
    known = Filled()
    executed = Filled()
    # Publishing an order always copied a prefix of the venue's executions, even in B6.1.
    prefixes = {executed}
    executions = []

    def difference(code, recoverable, **detail):
        differences.append(dict(client_order_id=client, code=code, recoverable=recoverable, **detail))

    for event in invalid:
        difference('INVALID_JOURNAL_EVENT', False, event_id=event)
    for event in sorted(receipts - fills.keys()):
        difference('UNMATCHED_EXECUTION_RECEIPT', False, execution_id=event)
    limit = Decimal(spec['limit_price'])
    for event, (quantity, price) in fills.items():
        if (spec['side'] == 'BUY' and price > limit) or (spec['side'] == 'SELL' and price < limit):
            difference('EXECUTION_OUTSIDE_LIMIT', False, execution_id=event)
        executed = executed.plus(quantity, price)
        prefixes.add(executed)
        if event in receipts:
            known = known.plus(quantity, price)
        else:
            difference('MISSING_EXECUTION_RECEIPT', True, execution_id=event)
        executions.append(dict(execution_id=event, quantity=quantity, price=money(price), booked=event in receipts))

    if executed != venue:
        difference('VENUE_TOTAL_WITHOUT_MATCHING_EXECUTIONS', False)
    if not venue_state_agrees(row['venue_state'], venue.quantity, spec['quantity']):
        difference('VENUE_STATE_CONFLICT', False)
    if local not in prefixes:
        difference('LOCAL_TOTAL_WITHOUT_MATCHING_EXECUTIONS', False)
    elif local != venue:
        difference('ORDER_TOTAL_DIFFERS', True)
    state, venue_state = order['state'], row['venue_state']
    if state != 'UNKNOWN' and not venue_state_agrees(None if state == 'READY' else state, local.quantity, spec['quantity']):
        difference('LOCAL_STATE_CONFLICT', False)
    elif venue_state is None:
        if state == 'UNKNOWN':
            difference('ORDER_LOOKUP_REQUIRED', True)
        elif state not in ('READY', 'REJECTED', 'EXPIRED', 'CANCELED'):
            difference('LOCAL_ORDER_WITHOUT_VENUE_ORDER', False)
    elif state != venue_state:
        # A stale open order/ambiguous response can catch up. A terminal contradiction needs review.
        if state in ('ACCEPTED', 'PARTIALLY_FILLED', 'UNKNOWN'):
            difference('ORDER_LOOKUP_REQUIRED', True)
        else:
            difference('LOCAL_STATE_CONFLICT', False)
    return dict(client_order_id=client, listing_id=spec['listing_id'], side=spec['side'],
                quantity=spec['quantity'], state=state, venue_state=venue_state, executions=executions,
                local=local.report(), booked=known.report(), venue=venue.report(), executed=executed.report(),
                reserved_cash=money(Decimal(order['reserved_cash'])), reserved_shares=order['reserved_shares'])


def balance(opening, orders, source):
    cash = Decimal(opening['cash'])
    positions = opening['positions'].copy()
    for order in orders:
        sign = 1 if order['side'] == 'BUY' else -1
        amount = order[source]
        positions[order['listing_id']] += sign * amount['quantity']
        cash -= sign * Decimal(amount['value'])
    return dict(cash=money(cash), positions=positions)


def compare_statement(db, opening, expected, differences):
    statement = venue_account(db)
    if statement is None:
        differences.append(dict(code='VENUE_ACCOUNT_MISSING', recoverable=False))
        return None
    if any(statement.get(key) != opening[key] for key in ('account_ref', 'snapshot_ref', 'currency')):
        differences.append(dict(code='VENUE_ACCOUNT_IDENTITY_MISMATCH', recoverable=False))
    positions = statement['positions']
    cash = money(Decimal(statement['cash']))
    if cash != expected['cash']:
        differences.append(dict(code='VENUE_CASH_MISMATCH', recoverable=False, expected=expected['cash'], actual=cash))
    for listing in sorted(expected['positions'].keys() | positions.keys()):
        wanted, actual = expected['positions'].get(listing), positions.get(listing)
        if actual != wanted:
            differences.append(dict(code='VENUE_POSITION_MISMATCH', recoverable=False,
                                    listing_id=listing, expected=wanted, actual=actual))
    return dict(cash=cash, positions=positions)


def inspect(db, opening):
    fills, receipts, invalid = journal(db)
    orders, differences = [], []
    for row in db.execute('SELECT * FROM intents ORDER BY client_id'):
        client = row['client_id']
        orders.append(order_view(row, fills[client], receipts[client], invalid[client], differences))
    clients = {o['client_order_id'] for o in orders}
    for client in sorted((fills.keys() | receipts.keys() | invalid.keys()) - clients):
        differences.append(dict(code='UNMATCHED_CLIENT_ORDER_ID', recoverable=False, client_order_id=client))
    balances = {source: balance(opening, orders, source) for source in ('local', 'booked', 'executed')}
    balances['venue_orders'] = balance(opening, orders, 'venue')
    balances['venue'] = compare_statement(db, opening, balances['venue_orders'], differences)
    return dict(orders=orders, balances=balances, differences=differences)


def has_unexplained_difference(db, basis):
    """Also check inside the admission/dispatch transaction, after any earlier worker poll."""
    state = inspect(db, opening_account(basis))
    return any(not d['recoverable'] for d in state['differences'])


def recovery_id(db, client, action, reference):
    # Legacy callers could choose any event ID. Preserve even an unrelated receipt with our prefix.
    event = 'b63:' + digest([client, action, reference])
    while db.execute("""SELECT event_id FROM events WHERE event_id=?
                        UNION ALL SELECT event_id FROM outbox_attempts WHERE event_id=?""", (event, event)).fetchone():
        event = 'b63:' + digest(event)
    return event


def recover(simulator, db, before):
    now = utc(simulator.clock())
    applied = []
    for order in before['orders']:
        client = order['client_order_id']
        for execution in order['executions']:
            if not execution['booked']:
                ref = execution['execution_id']
                event = recovery_id(db, client, 'FILL_RECOVERED', ref)
                simulator.record_event(db, client, event, 'FILL_RECOVERED', dict(execution_id=ref), now)
                applied.append(dict(client_order_id=client, execution_id=ref))
        # Recording a missing fill may already have published the latest venue state, including a cancel.
        row = simulator.row(db, client)
        local = row['state'], row['filled'], Decimal(row['filled_value'])
        venue = row['venue_state'], row['venue_filled'], Decimal(row['venue_value'])
        if row['state'] == 'UNKNOWN' or (row['venue_state'] is not None and local != venue):
            event = recovery_id(db, client, 'LOOKUP', [row['state'], row['venue_state'], row['venue_filled']])
            simulator.record_event(db, client, event, 'LOOKUP', dict(fault='OK'), now)
    return applied


def reconcile(simulator, *, repair=True):
    """Compare independent venue totals with individual fills and local receipts. Never submit an order."""
    empty = dict(domain='LOCAL_SIMULATOR', status='NO_ACCOUNT', opening=None, before=None, after=None,
                 recovered=[], snapshot_hash=None, external_orders_enabled=False)
    if not simulator.path.exists():
        return empty
    with simulator.transaction() as db:
        basis = db.execute("SELECT value FROM meta WHERE key='basis'").fetchone()
        if basis is None:
            if db.execute('SELECT 1 FROM intents LIMIT 1').fetchone():
                raise ValueError('SIMULATOR_BASIS_MISSING')
            return empty
        opening = opening_account(json.loads(basis[0]))
        before = inspect(db, opening)
        after, recovered = before, []
        differences = before['differences']
        if repair and differences and all(d['recoverable'] for d in differences):
            recovered = recover(simulator, db, before)
            after = inspect(db, opening)
        return dict(domain='LOCAL_SIMULATOR', status='PENDING' if after['differences'] else 'RECONCILED',
                    opening=opening, before=before, after=after, recovered=recovered,
                    snapshot_hash=digest(dict(opening=opening, state=after)), external_orders_enabled=False)
