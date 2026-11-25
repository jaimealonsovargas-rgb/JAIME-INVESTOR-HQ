"""B5 handoff and conservative reservations for the local B6 simulation."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
import re

from app.cycle_contracts import window
from app.quant_store import digest
from app.risk_engine import POLICY, POLICY_HASH, assess


OPEN = {'READY', 'UNKNOWN', 'ACCEPTED', 'PARTIALLY_FILLED'}


def decoded(row):
    return dict(spec=json.loads(row['spec']), state=row['state'], filled=row['filled'], filled_value=row['filled_value'])


def public_order(row):
    order = decoded(row)
    spec = order['spec']
    remaining = spec['quantity'] - order['filled'] if order['state'] in OPEN else 0
    return dict(**order, reserved_cash=str(Decimal(spec['buffered_unit']) * remaining) if spec['side'] == 'BUY' else '0',
                reserved_shares=remaining if spec['side'] == 'SELL' else 0)


def utc(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError('AWARE_CLOCK_REQUIRED')
    return value.astimezone(timezone.utc)


def verified_receipt(cycle_id, record):
    if not isinstance(cycle_id, str) or not re.fullmatch('[a-f0-9]{64}', cycle_id):
        raise ValueError('INVALID_CYCLE_ID')
    if not isinstance(record, dict) or record.get('version') != 'b5-risk-decision-v1':
        raise ValueError('RISK_RECEIPT_UNAVAILABLE')
    if (record.get('cycle_id') != cycle_id or record.get('mode') != 'PAPER'
            or record.get('execution_ready') is not False or record.get('orders_enabled') is not False
            or record.get('decision_id') != digest({k: v for k, v in record.items() if k != 'decision_id'})):
        raise ValueError('RISK_RECEIPT_INTEGRITY')


def reviewable(record, now):
    """Historical abstentions can be inspected after expiry; only fresh buys/sells can proceed."""
    if record['outcome'] in ('OBSERVE', 'VETO'):
        return record['reason']
    if (record['outcome'] != 'ASSESSED' or record['validation'] != 'CANDIDATES_FOR_REVIEW'
            or record['policy_id'] != POLICY.version or record['policy_hash'] != POLICY_HASH):
        return 'UNSUPPORTED_RISK_DECISION'
    if not utc(datetime.fromisoformat(record['decided_at'])) <= now < utc(datetime.fromisoformat(record['expires_at'])):
        return 'RISK_OUTSIDE_VALIDITY'
    return None


def reviewed_packet(record, review):
    decided = utc(datetime.fromisoformat(record['decided_at']))
    if (review.binding.dossier != record['dossier_id'] or not review.binding.packet_sha256
            or review.binding.packet_sha256 != record['input_ref']
            or review.run(record['cycle_id'], decided, window(decided)[1]) != record):
        raise ValueError('REVIEWED_HANDOFF_MISMATCH')
    return review.packet()


def basis_of(packet):
    return dict(account=packet.account.model_dump(mode='json'),
                instruments=[i.model_dump(mode='json') for i in sorted(packet.instruments, key=lambda i: i.listing_id)])


def available_packet(packet, orders, proposals):
    """Project the confirmed quantities and still-reserved capital onto the same reviewed snapshot.

    A buy is charged at its buffered cap and a sale credited at the reviewed bid.
    Favourable fixture fills cannot inflate available buying power for later proposals.
    """
    assets = {i.listing_id: i for i in packet.instruments}
    cash, turnover, count = packet.account.cash, packet.account.turnover_today, packet.account.open_orders
    worst_exits = {}
    with localcontext() as ctx:
        ctx.prec = 64
        for order in orders:
            spec, filled = order['spec'], order['filled']
            reserved = spec['quantity'] - filled if order['state'] in OPEN else 0
            if not (filled or reserved):
                continue
            asset = assets[spec['listing_id']]
            cap = Decimal(spec['buffered_unit'])
            if spec['side'] == 'BUY':
                cash -= cap * filled
                updates = dict(shares=asset.shares + filled, pending_buy_shares=asset.pending_buy_shares + reserved,
                               pending_buy_cash=asset.pending_buy_cash + reserved * cap)
                stress = Decimal(spec['stressed_exit'])
                worst_exits[asset.listing_id] = min(worst_exits.get(asset.listing_id, stress), stress)
            else:
                cash += Decimal(spec['limit_price']) * filled
                updates = dict(shares=asset.shares - filled, pending_sell_shares=asset.pending_sell_shares + reserved)
                # B5 already books an outstanding sale at ask. Carry its remaining cost buffer too.
                turnover += max(Decimal(0), cap - asset.ask) * reserved
            assets[asset.listing_id] = asset.model_copy(update=updates)
            turnover += max(cap * filled, Decimal(order['filled_value']))
            count += bool(reserved)
    if cash < 0 or any(i.shares < i.pending_sell_shares for i in assets.values()):
        raise ValueError('SIMULATED_RESERVATION_MISMATCH')
    checked = []
    for p in proposals:
        if p.side == 'BUY' and p.downside and p.listing_id in worst_exits:
            downside = p.downside.model_copy(update={'stressed_exit': min(p.downside.stressed_exit, worst_exits[p.listing_id])})
            p = p.model_copy(update={'downside': downside})
        checked.append(p)
    account = packet.account.model_copy(update=dict(cash=cash, turnover_today=turnover, open_orders=count))
    return packet.model_copy(update=dict(account=account, instruments=tuple(assets.values()), proposals=tuple(checked)))


def recheck(packet, orders, proposals, now, expiry):
    effective = available_packet(packet, orders, proposals)
    return assess(effective, now, expiry)


def intent_for(record, case, proposal, asset, account_ref):
    with localcontext() as ctx:
        ctx.prec = 64
        cap = Decimal(case['notional_with_buffer']) / proposal.quantity
    spec = dict(version='b6-local-intent-v1', domain='LOCAL_SIMULATOR', decision_id=record['decision_id'],
                cycle_id=record['cycle_id'], dossier_id=record['dossier_id'], packet_ref=record['input_ref'],
                policy_id=record['policy_id'], policy_hash=record['policy_hash'], decided_at=record['decided_at'],
                account_ref=account_ref, snapshot_ref=record['account']['snapshot_ref'],
                candidate_id=proposal.candidate_id, listing_id=asset.listing_id, side=proposal.side,
                quote_ref=case['quote_ref'], liquidity_ref=case['liquidity_ref'],
                quantity=proposal.quantity, currency=asset.currency, kind='LIMIT', time_in_force='DAY',
                limit_price=str(asset.ask if proposal.side == 'BUY' else asset.bid), buffered_unit=str(cap),
                stressed_exit=case['downside']['stressed_exit'] if case['downside'] else None,
                expires_at=case['expires_at'], committee_ref=proposal.committee_ref)
    ident = digest([spec['version'], record['decision_id'], account_ref, proposal.candidate_id,
                    asset.listing_id, proposal.side, proposal.quantity])
    return dict(spec, intent_id=ident, client_order_id='j6s-' + ident[:40])
