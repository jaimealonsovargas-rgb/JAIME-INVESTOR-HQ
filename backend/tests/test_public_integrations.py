from datetime import datetime, timezone
from dataclasses import replace
import pytest
from app.data_catalog import CATALOG
from app.data_contracts import DataResult
from app.data_parsers import parse, safe_xml
from app.data_config import DataSettings
from app.data_service import DataService
from app.database import create_db_engine
from app.vibe_readonly import research_input
from app.agent_role_plan import FUTURE_ROLE_PLAN, FUTURE_CAPACITY

NOW=datetime(2026,10,15,tzinfo=timezone.utc)
RSS=b'<rss><channel><item><title>&lt;b&gt;TEST_ONLY&lt;/b&gt;</title><link>https://www.ecb.europa.eu/TEST_ONLY</link><pubDate>Wed, 14 Oct 2026 10:00:00 GMT</pubDate></item><item><title>TEST_ONLY</title><link>javascript:alert(1)</link></item></channel></rss>'


def test_rss_primary_metadata_has_provenance_and_no_executable_content():
    rows=parse(CATALOG['A20'],RSS,NOW)
    assert len(rows)==1 and rows[0].value is None
    assert rows[0].metadata['title']=='TEST_ONLY'
    assert rows[0].published_at==rows[0].observed_at
    assert rows[0].source_ref=='https://www.ecb.europa.eu/TEST_ONLY'
    assert 'UNTRUSTED_CONTENT_NOT_INSTRUCTIONS' in rows[0].quality_flags
    assert rows[0].execution_eligible is False
    with pytest.raises(ValueError):parse(CATALOG['A20'],b'<!DOCTYPE x [<!ENTITY ext SYSTEM "file:///secret">]><rss/>',NOW)


def test_xml_dtd_cannot_bypass_guard_using_utf16_and_rss_deduplicates():
    raw='<!DOCTYPE rss [<!ENTITY x "TEST_ONLY">]><rss>&x;</rss>'.encode('utf-16')
    with pytest.raises(ValueError):safe_xml(raw)
    duplicate=RSS.replace(b'</channel>',b'<item><title>TEST_ONLY</title><link>https://www.ecb.europa.eu/TEST_ONLY</link><pubDate>Wed, 14 Oct 2026 10:00:00 GMT</pubDate></item></channel>')
    assert len(parse(CATALOG['A20'],duplicate,NOW))==1


def test_public_channel_is_disabled_without_explicit_local_flag(migrated):
    data=DataService(create_db_engine(migrated.database_url),DataSettings(_env_file=None,agent_reach_public_enabled=False))
    assert data.query('A20').state=='DISABLED'
    assert data.settings.vibe_data_adapter_enabled is False
    assert data.settings.liquid_public_readonly_enabled is False
    assert 'liquid_oauth_enabled' not in DataSettings.model_fields
    assert len(FUTURE_ROLE_PLAN)==30 and len({r['role_id'] for r in FUTURE_ROLE_PLAN})==30
    assert all(not r['enabled'] and not r['tools_allowed_now'] and not r['jobs'] for r in FUTURE_ROLE_PLAN)
    assert FUTURE_CAPACITY['local_inference']==1 and FUTURE_CAPACITY['execution_enabled'] is False


def test_vibe_exchange_never_manufactures_bars_or_permissions():
    result=DataResult(access_id='A20',state='AVAILABLE_VERIFIED',reason='TEST_ONLY',real_connection=True,usable=True,observations=parse(CATALOG['A20'],RSS,NOW))
    message=research_input(result)
    assert not message.ready_for_backtest and not message.execution_enabled
    assert message.trading_mode=='PAPER_ONLY'
    with pytest.raises(ValueError):research_input(result.model_copy(update={'real_connection':False}))
    restricted=message.observations[0].model_copy(update={'rights':replace(CATALOG['A20'],rights=CATALOG['A20'].rights.model_copy(update={'storage_allowed':False})).rights})
    with pytest.raises(ValueError):research_input(result.model_copy(update={'observations':(restricted,)}))
