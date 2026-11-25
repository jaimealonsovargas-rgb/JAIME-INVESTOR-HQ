"""Settled cash and holdings maintained by the local venue at execution, independent of OMS receipts."""
from decimal import Decimal
import json

from pydantic import TypeAdapter

from app.quant_store import canonical
from app.risk_contracts import Positive, Quantity

PRICE = TypeAdapter(Positive)
UNITS = TypeAdapter(Quantity)


def money(value):
    return format(value.normalize(), 'f')


def opening_account(basis):
    account = basis['account']
    return dict(account_ref=account['account_ref'], snapshot_ref=account['snapshot_ref'],
                currency=account['currency'], cash=money(Decimal(account['cash'])),
                positions={i['listing_id']: i['shares'] for i in basis['instruments']})


def settle(account, spec, quantity, value):
    shares = account['positions'][spec['listing_id']]
    cash = Decimal(account['cash'])
    if spec['side'] == 'BUY':
        shares += quantity
        cash -= value
    else:
        shares -= quantity
        cash += value
    account['positions'][spec['listing_id']] = shares
    account['cash'] = money(cash)


def initialize_venue(db, basis):
    # Formats 1/2 retained per-order venue counters but had no separate account statement.
    account = opening_account(basis)
    for row in db.execute('SELECT spec,venue_filled,venue_value FROM intents WHERE venue_filled!=0 OR venue_value!=?', ('0',)):
        settle(account, json.loads(row['spec']), row['venue_filled'], Decimal(row['venue_value']))
    db.execute("INSERT INTO meta VALUES ('venue_account',?)", (canonical(account),))


def venue_account(db):
    row = db.execute("SELECT value FROM meta WHERE key='venue_account'").fetchone()
    return json.loads(row[0]) if row else None


def settle_fill(db, spec, quantity, value):
    account = venue_account(db)
    if account is None:
        raise ValueError('VENUE_ACCOUNT_MISSING')
    settle(account, spec, quantity, value)
    db.execute("UPDATE meta SET value=? WHERE key='venue_account'", (canonical(account),))
