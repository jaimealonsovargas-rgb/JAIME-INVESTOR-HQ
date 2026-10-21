"""Read-only chart history; no fabricated bars or daily returns."""
from app.data_rights import readable
FIELDS = ('provider','feed','series_id','venue','currency','unit','period_precision','data_kind')


def market_status(observation, now):
    """Display freshness; deliberately separate from valuation eligibility in P3."""
    if not readable(observation.rights, local_research=True) or observation.value is None:
        return 'NO_DATA'
    if observation.stale(now):
        return 'STALE'
    if any('ESTIMAT' in flag or 'PROJECTION' in flag for flag in observation.quality_flags):
        return 'ESTIMATED'
    return 'FRESH'


def comparable_history(latest, observations, now):
    identity = tuple(getattr(latest,k) for k in FIELDS)
    rows = [o for o in observations if tuple(getattr(o,k) for k in FIELDS)==identity and o.value is not None
            and readable(o.rights, local_research=True)]
    # The input may contain revisions; keep the latest received observation per timestamp.
    by_time = {}
    for row in sorted(rows,key=lambda o:o.received_at): by_time[row.observed_at]=row
    rows = sorted(by_time.values(),key=lambda o:o.observed_at)[-60:]
    enough = len(rows)>=3
    return {'state': ('STALE' if latest.stale(now) else 'AVAILABLE') if enough else 'NO_DATA',
            'reason': 'Historia comparable de un único feed; no implica retorno diario.' if enough else 'Sin histórico comparable suficiente.',
            'identity': dict(zip(FIELDS,identity)),
            'points': [{'observed_at':o.observed_at.isoformat(),'value':str(o.value),'observation_id':o.id} for o in rows] if enough else []}
