"""Additive registry; never rewrites legacy instruments, research or ledger."""
from sqlalchemy import Table, Column, String, JSON, ForeignKey, Index


def register(metadata):
    Table('universe_entities', metadata,
          Column('cik', String(10), primary_key=True), Column('name', String(500), nullable=False),
          Column('first_seen_at', String(40), nullable=False), Column('last_seen_at', String(40), nullable=False))
    listings = Table('universe_listings', metadata,
          Column('id', String(64), primary_key=True), Column('provider', String(20), nullable=False),
          Column('provider_key', String(200), nullable=False), Column('cik', ForeignKey('universe_entities.cik')),
          Column('symbol', String(120), nullable=False), Column('venue', String(120), nullable=False),
          Column('name', String(500), nullable=False), Column('state', String(32), nullable=False),
          Column('first_seen_at', String(40), nullable=False), Column('last_seen_at', String(40), nullable=False),
          Column('payload', JSON, nullable=False))
    Index('ix_universe_listing_search', listings.c.provider, listings.c.symbol, listings.c.id)
    Index('ix_universe_listing_cik', listings.c.cik)
    versions = Table('universe_versions', metadata,
          Column('id', String(64), primary_key=True), Column('listing_id', ForeignKey('universe_listings.id'), nullable=False),
          Column('known_from', String(40), nullable=False), Column('known_until', String(40)),
          Column('payload_hash', String(64), nullable=False), Column('source', String(500), nullable=False),
          Column('payload', JSON, nullable=False))
    Index('ix_universe_version_listing_time', versions.c.listing_id, versions.c.known_from)
    Table('universe_imports', metadata,
          Column('id', String(128), primary_key=True), Column('provider', String(20), nullable=False),
          Column('state', String(32), nullable=False), Column('started_at', String(40), nullable=False),
          Column('finished_at', String(40)), Column('payload', JSON, nullable=False))
