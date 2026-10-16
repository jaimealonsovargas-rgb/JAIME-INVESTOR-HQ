"""Resumen local de solo lectura. No consulta proveedores ni crea cartera/jobs."""
from typing import Literal

from pydantic import AwareDatetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts import Contract
from app.data_catalog import CATALOG
from app.data_contracts import DataResult, Observation
from app.database import DataRecord
from app.data_service import cache_key


class HQSection(Contract):
    section_id: str
    phase_required: str
    status: Literal['AVAILABLE', 'NOT_IMPLEMENTED', 'STALE', 'OFFLINE']
    as_of_utc: AwareDatetime | None = None
    source: str | None = None
    currency: str | None = None
    value: dict | None = None
    items: tuple[Observation, ...] = ()
    quality: dict[str, int | str] = {}
    rights: str | None = None
    reason: str


class HQOverview(Contract):
    checked_at: AwareDatetime
    trading_mode: Literal['PAPER_ONLY'] = 'PAPER_ONLY'
    orders_enabled: Literal[False] = False
    sections: tuple[HQSection, ...]


def overview(data, portfolio=None) -> HQOverview:
    now = data.clock()
    groups: dict[str, list[Observation]] = {'markets': [], 'news': []}
    # Solo caches verificadas; la mera existencia de registros/mock no prueba conexión.
    with Session(data.engine) as session:
        for row in session.scalars(select(DataRecord).where(DataRecord.key.startswith('cache:'))):
            result = DataResult.model_validate(row.payload)
            source = CATALOG.get(result.access_id)
            if not source or data.initial(source).state != 'NOT_VERIFIED':
                continue
            if row.key!=cache_key(source):
                continue
            if not result.real_connection or not all((source.rights.access_allowed, source.rights.display_allowed, source.rights.storage_allowed, source.rights.redistribution_allowed)):
                continue
            for item in result.observations:
                if not item.rights.display_allowed or not item.rights.storage_allowed or not item.rights.redistribution_allowed:
                    continue
                group = 'news' if item.data_kind == 'news_metadata' else 'markets'
                if item.data_kind in ('news_metadata', 'market_quote', 'fx_reference', 'yield_curve'):
                    groups[group].append(item)
    sections = []
    for name, phase in [('portfolio', 'P3'), ('positions', 'P3'), ('operations', 'P6'), ('markets', 'P2'), ('news', 'P2'), ('risk', 'P5'), ('committee', 'P5'), ('agents', 'P4'), ('systems', 'P2')]:
        if name in ('portfolio', 'positions') and portfolio:
            value = ({key: portfolio[key] for key in ('nav_eur', 'cash_eur', 'cumulative_return_pct', 'valuation_status', 'performance')}
                if name == 'portfolio' else {key: portfolio[key] for key in ('positions_count', 'market_value_eur', 'invested_pct', 'positions')})
            sections.append(HQSection(section_id=name, phase_required='P3', status='AVAILABLE' if portfolio['valuation_status']=='FRESH' else 'STALE',
                as_of_utc=portfolio['as_of'], source='Ledger MASTER local · '+portfolio['ledger_hash'], currency='EUR', value=value,
                rights='Contabilidad propia de simulación; sin saldos de bróker.',
                reason='Capital virtual; ledger verificado. Órdenes y fills bloqueados — P6.'))
            continue
        # Una observación por serie, conservando fuente/feed; ningún cálculo financiero.
        unique = {}
        for item in sorted(groups.get(name, []), key=lambda o: o.observed_at, reverse=True):
            unique.setdefault((item.access_id, item.series_id), item)
        items = tuple(list(unique.values())[:5])
        status = 'AVAILABLE' if items else 'NOT_IMPLEMENTED'
        if items and any(item.stale(now) for item in items):
            status = 'STALE'
        if name=='systems':
            sections.append(HQSection(section_id=name,phase_required=phase,status='AVAILABLE',as_of_utc=now,
                source='GET /api/data/quality · SQLite local',quality=data.quality()['counts'],
                rights='Metadatos propios de conexión; no valores financieros.',reason='Estado local de conectores; una conexión histórica no garantiza frescura actual.'))
            continue
        sections.append(HQSection(section_id=name, phase_required=phase, status=status,
            as_of_utc=max((o.received_at for o in items), default=None),
            source='Cache local P2 verificada' if items else None, items=items,
            rights='Solo feeds con visualización y redistribución autorizadas.' if items else None,
            reason=('Contiene datos caducados; consultar fechas por registro. No ejecutables.' if status=='STALE' else 'Datos de referencia/históricos; no ejecutables.') if items else f'NO DISPONIBLE — {phase}: sin registros autorizados.'))
    return HQOverview(checked_at=now, sections=tuple(sections))
