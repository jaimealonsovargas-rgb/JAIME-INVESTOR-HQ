"""Observation identity is independent from revision content and download bytes."""
import hashlib
import json
from datetime import datetime, timedelta, timezone


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def observation_key(obs):
    fields = ('access_id', 'provider', 'feed', 'series_id', 'data_kind', 'venue',
              'currency', 'unit', 'period', 'period_precision')
    return fingerprint([*[getattr(obs, key) for key in fields], obs.metadata.get('start')])


def revision_id(obs, scope=None):
    def decimal(value):
        if value is None:return None
        if value == 0:return '0'
        text=format(value,'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text
    return fingerprint(['observation.v2', scope, observation_key(obs), decimal(obs.value),
                        decimal(obs.bid), decimal(obs.ask), obs.metadata])


def publication_bound(obs):
    if obs.published_at:
        return obs.published_at
    if obs.provider == 'SEC' and obs.metadata.get('filed'):
        # Companyfacts supplies a filing date, not an acceptance time. 05:00 UTC
        # next day bounds the end of the US Eastern day in winter and summer.
        # Local as-of also requires actual receipt; this is not full market PIT.
        return datetime.fromisoformat(obs.metadata['filed']).replace(tzinfo=timezone.utc) + timedelta(days=1, hours=5)
    return None
