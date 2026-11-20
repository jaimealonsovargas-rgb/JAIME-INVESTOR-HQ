"""Pinned, local-only contract review. No SDK, network, symbol auto-join or DB writes."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import zlib

from app.data_identity import fingerprint

REVIEW_PATH = Path(__file__).with_name('pilot_ibkr_review.json')
MAX_REPORT_BYTES = 65536
DOCUMENTATION = 'https://www.interactivebrokers.com/docs/tws-api/doc/contracts/object'


def aware(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('CONTRACT_TIME_WITHOUT_ZONE')
    return result.astimezone(timezone.utc)


def validate_report(raw, review, pilot):
    """Only the explicitly reviewed bundle and its exact class/catalogue bindings."""
    if (len(raw) > MAX_REPORT_BYTES or review['version'] != 'pilot-ibkr-review-v1'
            or not re.fullmatch('[a-f0-9]{64}', review['report_sha256'])
            or hashlib.sha256(raw).hexdigest() != review['report_sha256']
            or review['pilot_sha256'] != fingerprint(pilot)):
        raise ValueError('CONTRACT_REVIEW_MISMATCH')
    report = json.loads(raw)
    if (report['version'] != 'ibkr-readonly-probe-v1' or report['state'] != 'CONNECTED_READ_ONLY_PROBE'
            or any(report[k] is not True for k in ('connected', 'paper_account_matched', 'disconnected_after_probe'))
            or any(report[k] is not False for k in ('orders_enabled', 'market_data_requested'))
            or report['read_only_basis'] != 'TWS_UI_CONFIRMED_BY_USER'
            or report['sent_message_ids'] != [71, 49, 9, 9, 9]
            or any(e['code'] not in (2104, 2106, 2158) for e in report['errors'])
            or not aware(report['checked_at']) <= aware(report['server_time_utc']) <= aware(review['reviewed_at'])):
        raise ValueError('CONTRACT_PROBE_NOT_ACCEPTED')
    symbols = [p['symbol'] for p in pilot['items']]
    if (len(symbols) != 3 or len(set(symbols)) != 3
            or sorted(p['symbol'] for p in report['contracts']) != sorted(symbols)
            or sorted(p['symbol'] for p in review['bindings']) != sorted(symbols)):
        raise ValueError('CONTRACT_BUNDLE_AMBIGUOUS')
    result, con_ids = {}, set()
    for spec in pilot['items']:
        symbol = spec['symbol']
        binding = next(p for p in review['bindings'] if p['symbol'] == symbol)
        item = next(p for p in report['contracts'] if p['symbol'] == symbol)
        if (binding['identity_spec_sha256'] != fingerprint(spec) or item['completed'] is not True
                or item['state'] != 'CURRENT_CONTRACT_CANDIDATE' or item['error_codes'] != []
                or len(item['candidates']) != 1):
            raise ValueError('CONTRACT_BINDING_MISMATCH')
        contract = item['candidates'][0]
        if (fingerprint(contract) != binding['contract_sha256'] or contract['conId'] != binding['con_id']
                or type(contract['conId']) is not int or contract['conId'] <= 0 or contract['conId'] in con_ids
                or contract['symbol'] != symbol or contract['localSymbol'] != symbol
                or contract['secType'] != 'STK' or contract['currency'] != 'USD'
                or contract['primaryExchange'] != 'NASDAQ' or contract['exchange'] != 'SMART'
                or contract['tradingClass'] != 'NMS' or not contract['longName']):
            raise ValueError('CONTRACT_FIELDS_MISMATCH')
        con_ids.add(contract['conId'])
        result[symbol] = (binding, contract)
    return report, result


def read_report(root, digest):
    if not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('INVALID_CONTRACT_ARCHIVE')
    with gzip.open(root / (digest + '.json.gz'), 'rb') as stream:
        raw = stream.read(MAX_REPORT_BYTES + 1)
    if len(raw) > MAX_REPORT_BYTES or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('CONTRACT_ARCHIVE_CHANGED')
    return raw


def contract_evidence(root, identity, spec, pilot, cutoff, review=None):
    result = dict(native_currency=None, native_currency_state='UNVERIFIED', current_contract=None,
        native_currency_reason='Divisa del contrato sin evidencia IBKR revisada y verificable. No se infiere de los precios solicitados ni de las cuentas.')
    if identity['state'] != 'DOCUMENTED':
        return result
    try:
        review = json.loads(REVIEW_PATH.read_text(encoding='utf-8')) if review is None else review
        if aware(review['reviewed_at']) > cutoff:
            return result
        raw = read_report(root, review['report_sha256'])
        report, contracts = validate_report(raw, review, pilot)
        binding, contract = contracts[spec['symbol']]
        if binding['instrument_id'] != identity['instrument_id']:
            raise ValueError('CONTRACT_CLASS_LINK_CHANGED')
        known = max(aware(identity['known_from']), aware(review['reviewed_at']))
        result.update(native_currency=contract['currency'], native_currency_state='DOCUMENTED_OBSERVATION',
            native_currency_reason='USD documentado para el contrato IBKR observado en la captación del '
                + report['checked_at'][:10] + '. Revisión ligada a la clase SEC y al catálogo Alpaca; no acredita continuidad histórica ni seguimiento actual.',
            current_contract=dict(source='IBKR_TWS', con_id=contract['conId'], symbol=contract['symbol'],
                currency=contract['currency'], primary_exchange=contract['primaryExchange'],
                routing_exchange=contract['exchange'], observed_at=report['checked_at'], known_from=known.isoformat(),
                report_sha256=review['report_sha256'], documentation_url=DOCUMENTATION,
                scope='OBSERVED_CONTRACT_ONLY', historical_identity=False))
    except (OSError, EOFError, ValueError, KeyError, TypeError, StopIteration, AttributeError, zlib.error):
        result['native_currency_reason'] = 'Falta la evidencia IBKR fijada o no coincide con la revisión. La divisa del contrato requiere nueva revisión.'
    return result
