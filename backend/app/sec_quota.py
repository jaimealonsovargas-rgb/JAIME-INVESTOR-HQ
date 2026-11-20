"""One shared SEC budget for directory, legacy connector and issuer jobs.

Local policy: <= 60/minute, spaced by >= 1 second, below SEC's 10/s cap.
Call reserve in a BEGIN IMMEDIATE transaction; never sleep holding a DB lock.
"""
from datetime import datetime, timedelta
from app.database import DataQuota


def reserve(session, now):
    quota = session.get(DataQuota, 'SEC')
    if quota is None:
        quota = DataQuota(key='SEC', used=0, window_start=now.isoformat(), failures=0)
        session.add(quota)
    if quota.blocked_until and now < datetime.fromisoformat(quota.blocked_until):
        return quota.blocked_until
    start = datetime.fromisoformat(quota.window_start)
    if (now - start).total_seconds() >= 60:
        quota.used, quota.window_start = 0, now.isoformat()
        start = now
    if quota.used >= 60:
        return (start + timedelta(seconds=60)).isoformat()
    quota.used += 1
    quota.blocked_until = (now + timedelta(seconds=1)).isoformat()
    return None


def backoff(session, now, seconds):
    quota = session.get(DataQuota, 'SEC')
    if quota:
        until = now + timedelta(seconds=max(60, min(seconds, 86400)))
        if not quota.blocked_until or until > datetime.fromisoformat(quota.blocked_until):
            quota.blocked_until = until.isoformat()
