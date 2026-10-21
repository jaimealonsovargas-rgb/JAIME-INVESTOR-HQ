"""Local P3 reads. No provider queries, broker balances, or financial mutation API."""
import json
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.data_catalog import CATALOG
from app.data_contracts import DataResult
from app.data_service import cache_key
from app.database import DataRecord, InstrumentAlias, InstrumentRegistry
from app.portfolio_store import canonical, digest, read_journal
from app.portfolio_valuation import value_portfolio, permitted, freshness
from app.portfolio_performance import performance
from app.market_history import comparable_history, market_status
from app.data_history import read_source


def authorized_observations(data, *, local_research=False):
    observations = []
    with Session(data.engine) as session:
        for source in CATALOG.values():
            observations.extend(read_source(session, data, source, local_research=local_research))
    return sorted(observations, key=lambda o: (o.observed_at, o.received_at), reverse=True)


class PortfolioService:
    def __init__(self, engine, data):
        self.engine, self.data = engine, data

    def inputs(self, now):
        observations = authorized_observations(self.data)
        quotes, fx, labels = {}, {}, {}
        with Session(self.engine) as session:
            instruments = {str(i.id): i for i in InstrumentRegistry(session).list()}
            aliases = list(session.scalars(select(InstrumentAlias)))
            for alias in aliases:
                instrument = instruments.get(alias.instrument_id)
                if not instrument:
                    continue
                labels[alias.instrument_id] = instrument.symbol
                if datetime.fromisoformat(alias.verified_at) > now:
                    continue
                if alias.expires_at and datetime.fromisoformat(alias.expires_at) <= now:
                    continue
                for o in observations:
                    if o.data_kind != 'market_quote' or (o.provider, o.series_id, o.venue, o.currency) != (alias.provider, alias.symbol, alias.venue, alias.currency):
                        continue
                    if any(c.valuation and c.active(now) and c.provider == o.provider and c.feed == o.feed for c in instrument.provider_capabilities):
                        quotes.setdefault(alias.instrument_id, o)
        for o in observations:
            # Existing P2 BCE adapter normalizes this exact quote direction.
            if o.data_kind == 'fx_reference' and o.access_id == 'A01' and o.unit == 'USD/EUR':
                fx.setdefault('USD', o)
        return quotes, fx, labels

    def summary(self):
        now = self.data.clock()
        with self.engine.connect() as connection:
            events, state, head = read_journal(connection)
        if not events:
            raise ValueError('MASTER not initialized.')
        quotes, fx, labels = self.inputs(now)
        result = value_portfolio(state, quotes, fx, now, labels)
        result['ledger_hash'] = head
        result['events_count'] = len(events)
        result['seeded_at'] = events[0].occurred_at.isoformat()
        result['performance'] = performance(result, self.history(1000)['items'], events)
        return result

    def ledger(self, offset=0, limit=50):
        with self.engine.connect() as connection:
            events, state, head = read_journal(connection)
        rows = [dict(**e.model_dump(mode='json'), entries=state.postings[e.source_ref]) for e in reversed(events)]
        return dict(portfolio_id='MASTER', total=len(rows), offset=offset, limit=limit, ledger_hash=head, items=rows[offset:offset+limit])

    def history(self, limit=100, offset=0):
        with self.engine.connect() as connection:
            total = connection.execute(text("SELECT count(*) FROM valuation_snapshots WHERE portfolio_id='MASTER'")).scalar_one()
            rows = connection.execute(text("SELECT payload FROM valuation_snapshots WHERE portfolio_id='MASTER' ORDER BY as_of DESC,id DESC LIMIT :limit OFFSET :offset"), dict(limit=limit, offset=offset)).scalars().all()
        return dict(total=total, limit=limit, offset=offset, items=[json.loads(row) for row in reversed(rows)])

    def snapshot(self):
        summary = self.summary()
        summary.pop('performance')
        # One identical valuation per UTC day, ledger head and input provenance.
        fingerprint = digest(canonical({**summary, 'as_of': summary['as_of'][:10]}))
        with self.engine.begin() as connection:
            connection.execute(text("INSERT OR IGNORE INTO valuation_snapshots(portfolio_id,as_of,ledger_hash,fingerprint,payload) VALUES('MASTER',:as_of,:head,:fingerprint,:payload)"),
                dict(as_of=summary['as_of'], head=summary['ledger_hash'], fingerprint=fingerprint, payload=canonical(summary)))
        return summary

    def markets(self):
        now, observations = self.data.clock(), authorized_observations(self.data, local_research=True)
        unique = {}
        for o in observations:
            if o.data_kind not in ('market_quote', 'fx_reference', 'yield_curve', 'macro_series'):
                continue
            unique.setdefault((o.provider, o.feed, o.series_id, o.currency, o.unit, o.venue, o.period_precision), o)
        rows = [dict(symbol=o.series_id, name=o.series_id, value=str(o.value) if o.value is not None else None,
            daily_change_pct=None, daily_change_reason='Sin cierre anterior comparable verificado; no equivale a 0%.',
            status=market_status(o, now), observation=o.model_dump(mode='json'), history=comparable_history(o,observations,now)) for o in unique.values()]
        quotes = [r for r in rows if r['observation']['data_kind'] == 'market_quote'][:10]
        pulse = [r for r in rows if r['observation']['data_kind'] != 'market_quote'][:4]
        return dict(checked_at=now.isoformat(), watchlists=['CORE', 'OPPORTUNITIES', 'PORTFOLIO'], selected='CORE',
            items=quotes, pulse=pulse, reason='Cache P2 autorizada; sin consultas externas ni gestión de agentes. Variaciones no disponibles sin cierre diario comparable.')
