from hashlib import sha256
import pytest
from app.ibkr_probe_policy import validate_probe_config, matches_paper_account, classify_contracts


def config():
    return dict(host='127.0.0.1', port=7497, client_id=27,
                read_only_confirmed_in_tws=True,
                paper_account_sha256=sha256(b'DU123456').hexdigest())


@pytest.mark.parametrize('change', [dict(host='localhost'), dict(host='192.168.1.1'),
    dict(port=7496), dict(client_id=0), dict(read_only_confirmed_in_tws=False),
    dict(paper_account_sha256=''), dict(paper_account_sha256='x'*64)])
def test_blocks_unapproved_endpoint_or_missing_confirmation(change):
    with pytest.raises(ValueError):
        validate_probe_config(config() | change)


def test_exact_paper_account_not_port_alone():
    cfg = config()
    validate_probe_config(cfg)
    assert matches_paper_account('DU123456', cfg['paper_account_sha256'])
    for value in ('', 'U123456', 'DU999999', 'DU123456,U999', 'DU123456,DU999'):
        assert not matches_paper_account(value, cfg['paper_account_sha256'])


def test_account_hash_alone_does_not_allow_live():
    assert not matches_paper_account('U123456', sha256(b'U123456').hexdigest())


def test_partial_or_ambiguous_contract_never_resolves():
    c = dict(symbol='AAPL', secType='STK', conId=123, currency='USD', primaryExchange='NASDAQ')
    assert classify_contracts('AAPL', [c], True) == 'CURRENT_CONTRACT_CANDIDATE'
    assert classify_contracts('AAPL', [c], False) == 'INCOMPLETE'
    assert classify_contracts('AAPL', [c, c], True) == 'AMBIGUOUS'
    assert classify_contracts('AAPL', [], True) == 'NOT_FOUND'
    assert classify_contracts('AAPL', [c], True, [200]) == 'PROVIDER_ERROR'
    for change in (dict(currency='EUR'), dict(symbol='MSFT'), dict(secType='OPT'),
                   dict(conId=0), dict(primaryExchange='')):
        assert classify_contracts('AAPL', [c | change], True) == 'IDENTITY_MISMATCH'
