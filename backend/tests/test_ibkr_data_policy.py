from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from app.ibkr_data_policy import (end_time, bar_metadata, classify_history, classify_quote,
                                  safe_error, ALLOWED_MESSAGES, CONTRACT)

END = datetime(2026,11,16,tzinfo=timezone.utc)


def bar(**changes):
    return SimpleNamespace(**(dict(date='20261113',open='10',high='12',low='9',close='11',volume='100')|changes))


def test_end_is_completed_utc_boundary():
    assert end_time(datetime.fromisoformat('2026-11-16T02:30:00+01:00')) == END
    with pytest.raises(ValueError): end_time(datetime(2026,11,16))


@pytest.mark.parametrize('change', [dict(open='nan'), dict(low='-1'), dict(high='8'),dict(volume='-1'),
    dict(close='0'),dict(open='inf'),dict(date='20261113 10:00:00'),dict(date='20261116'),dict(date='20261001')])
def test_rejects_bad_or_out_of_window_bars(change):
    with pytest.raises(ValueError): bar_metadata(bar(**change),END)


def test_only_session_metadata_retained():
    assert bar_metadata(bar(),END) == '20261113'
    assert bar_metadata(bar(date='20261109'),END) == '20261109'
    for previous in ('20261113','20261114'):
        with pytest.raises(ValueError): bar_metadata(bar(),END,previous)


def test_entitlement_and_pacing_not_confused():
    assert safe_error(162,'No market data permissions for PRIVATE') == 'DATA_ENTITLEMENT_REQUIRED'
    assert safe_error(162,'Historical data pacing violation') == 'PACING_LIMIT'
    assert safe_error(162,'query returned no data') == 'NO_DATA'
    assert safe_error(162,'other private message') == 'PROVIDER_ERROR'
    assert safe_error(2106,'anything') == 'SERVICE_NOTICE'
    assert safe_error(2188,'anything') == 'UP_TO_SECOND_SUBSCRIPTION_ADVISORY'


def test_completeness_is_required_for_history():
    assert classify_history(True,['20261113'],[],[]) == 'ACCESS_OBSERVED'
    assert classify_history(False,['20261113'],[],[]) == 'INCOMPLETE_OR_TIMEOUT'
    assert classify_history(True,[],[],[]) == 'EMPTY_RESPONSE'
    assert classify_history(True,['20261113'],['INVALID_BAR'],[]) == 'QUALITY_REJECTED'
    assert classify_history(False,[],[],[dict(reason='DATA_ENTITLEMENT_REQUIRED')]) == 'DATA_ENTITLEMENT_REQUIRED'


def test_requesting_delayed_does_not_certify_returned_feed():
    assert classify_quote(None,[68],True) == 'FEED_UNCONFIRMED'
    assert classify_quote(1,[68],True) == 'NO_VALID_TOP_OF_BOOK'
    assert classify_quote(3,[68],True) == 'ACCESS_OBSERVED'
    assert classify_quote(4,[68],False) == 'PARTIAL_OBSERVATION'
    assert classify_quote(1,[4],True) == 'ACCESS_OBSERVED'
    assert classify_quote(None,[],False,[dict(reason='DATA_ENTITLEMENT_REQUIRED')]) == 'DATA_ENTITLEMENT_REQUIRED'


def test_wire_allowlist_excludes_all_order_and_account_commands():
    assert ALLOWED_MESSAGES == {1,2,20,25,49,59,71}
    assert not {3,4,5,6,7,8,16,17,58}.intersection(ALLOWED_MESSAGES)
    assert CONTRACT['conId'] == 265598 and CONTRACT['currency'] == 'USD'
