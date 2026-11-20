"""Shared Alpaca budget for the market worker and legacy B04 connector.

Local ceiling: 180/minute, with at least one second between requests.
Call reserve/backoff inside BEGIN IMMEDIATE; never wait with the lock held.
"""
from datetime import datetime, timedelta

from app.database import DataQuota


def reserve(session, now):
    quota = session.get(DataQuota, 'ALPACA')
    if quota is None:
        quota = DataQuota(key='ALPACA', used=0, window_start=now.isoformat(), failures=0)
        session.add(quota)
    if quota.blocked_until and now < datetime.fromisoformat(quota.blocked_until):
        return quota.blocked_until
    start = datetime.fromisoformat(quota.window_start)
    if (now - start).total_seconds() >= 60:
        quota.used, quota.window_start = 0, now.isoformat()
        start = now
    if quota.used >= 180:
        return (start + timedelta(seconds=60)).isoformat()
    quota.used += 1
    quota.blocked_until = (now + timedelta(seconds=1)).isoformat()
    return None


def backoff(session, now, seconds):
    quota = session.get(DataQuota, 'ALPACA')
    if quota is None:
        quota = DataQuota(key='ALPACA', used=0, window_start=now.isoformat(), failures=0)
        session.add(quota)
    until = now + timedelta(seconds=max(60, min(seconds, 86400)))
    if not quota.blocked_until or until > datetime.fromisoformat(quota.blocked_until):
        quota.blocked_until = until.isoformat()
