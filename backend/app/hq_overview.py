"""Resumen local de solo lectura. No consulta proveedores ni crea cartera/jobs."""
from typing import Literal

from pydantic import AwareDatetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts import Contract
from app.data_catalog import CATALOG
from app.data_contracts import DataResult, Observation
from app.database import DataRecord


class HQSection(Contract):
    section_id: str
    phase_required: str
    status: Literal['AVAILABLE', 'NOT_IMPLEMENTED', 'STALE', 'OFFLINE']
    as_of_utc: AwareDatetime | None = None
    source: str | None = None
    currency: str | None = None
    value: None = None
    items: tuple[Observation, ...] = ()
    reason: str


class HQOverview(Contract):
    checked_at: AwareDatetime
    trading_mode: Literal['PAPER_ONLY'] = 'PAPER_ONLY'
    orders_enabled: Literal[False] = False
    sections: tuple[HQSection, ...]


def overview(data) -> HQOverview:
    now = data.clock()
    groups: dict[str, list[Observation]] = {'markets': [], 'news': []}
    # Solo caches verificadas; la mera existencia de registros/mock no prueba conexión.
    with Session(data.engine) as session:
        for row in session.scalars(select(DataRecord).where(DataRecord.key.startswith('cache:'))):
            result = DataResult.model_validate(row.payload)
            source = CATALOG.get(result.access_id)
            if not source or data.initial(source).state != 'NOT_VERIFIED':
                continue
            if not result.real_connection or not source.rights.display_allowed:
                continue
            for item in result.observations:
                if not item.rights.display_allowed or not item.rights.storage_allowed:
                    continue
                group = 'news' if item.data_kind == 'news_metadata' else 'markets'
                if item.data_kind in ('news_metadata', 'market_quote', 'fx_reference', 'yield_curve'):
                    groups[group].append(item)
    sections = []
    for name, phase in [('portfolio', 'P3'), ('positions', 'P3'), ('operations', 'P6'), ('markets', 'P2'), ('news', 'P2'), ('risk', 'P5'), ('agents', 'P4')]:
        # Una observación por serie, conservando fuente/feed; ningún cálculo financiero.
        unique = {}
        for item in sorted(groups.get(name, []), key=lambda o: o.observed_at, reverse=True):
            unique.setdefault((item.access_id, item.series_id), item)
        items = tuple(list(unique.values())[:5])
        status = 'AVAILABLE' if items else 'NOT_IMPLEMENTED'
        if items and all(item.stale(now) for item in items):
            status = 'STALE'
        sections.append(HQSection(section_id=name, phase_required=phase, status=status,
            as_of_utc=max((o.received_at for o in items), default=None),
            source='Cache local P2 verificada' if items else None, items=items,
            reason='Datos de referencia/históricos; no ejecutables.' if items else f'NO DISPONIBLE — {phase}: sin registros autorizados.'))
    return HQOverview(checked_at=now, sections=tuple(sections))
