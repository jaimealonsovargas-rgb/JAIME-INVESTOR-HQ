"""Pure checks for the optional, isolated IBKR contract probe; no SDK or network."""
from hashlib import sha256
import re


PILOT = ('AAPL', 'MSFT', 'WMT')


def validate_probe_config(config):
    if config.get('host') != '127.0.0.1' or config.get('port') != 7497:
        raise ValueError('LOCAL_PAPER_ENDPOINT_REQUIRED')
    if config.get('client_id') != 27:
        raise ValueError('ISOLATED_CLIENT_REQUIRED')
    if config.get('read_only_confirmed_in_tws') is not True:
        raise ValueError('TWS_READ_ONLY_CONFIRMATION_REQUIRED')
    if not re.fullmatch(r'[0-9a-f]{64}', config.get('paper_account_sha256', '')):
        raise ValueError('EXACT_PAPER_ACCOUNT_REQUIRED')


def matches_paper_account(accounts, expected_hash):
    """Fail closed on missing, unexpected or additional accounts. Never emit IDs."""
    parsed = [part.strip() for part in accounts.split(',') if part.strip()]
    return (len(parsed) == 1 and bool(re.fullmatch(r'DU[A-Z0-9]+', parsed[0]))
            and sha256(parsed[0].encode('ascii')).hexdigest() == expected_hash)


def classify_contracts(symbol, contracts, completed, error_codes=()):
    """A result is a current contract candidate, never a historical/CIK identity."""
    if error_codes:
        return 'PROVIDER_ERROR'
    if not completed:
        return 'INCOMPLETE'
    if not contracts:
        return 'NOT_FOUND'
    if len(contracts) != 1:
        return 'AMBIGUOUS'
    c = contracts[0]
    if (c.get('symbol') != symbol or c.get('secType') != 'STK'
            or not isinstance(c.get('conId'), int) or c['conId'] <= 0
            or c.get('currency') != 'USD' or not c.get('primaryExchange')):
        return 'IDENTITY_MISMATCH'
    return 'CURRENT_CONTRACT_CANDIDATE'
