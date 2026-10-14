"""Contrato de intercambio P2 para evaluación aislada; no importa ni ejecuta Vibe."""
from typing import Literal
from app.contracts import Contract
from app.data_contracts import DataResult, Observation


class VibeResearchInput(Contract):
    schema_version: Literal['hq.p2.research.v1'] = 'hq.p2.research.v1'
    trading_mode: Literal['PAPER_ONLY'] = 'PAPER_ONLY'
    execution_enabled: Literal[False] = False
    ready_for_backtest: Literal[False] = False
    observations: tuple[Observation, ...]


def research_input(result: DataResult) -> VibeResearchInput:
    if not result.real_connection or not result.usable:
        raise ValueError('No hay datos reales utilizables.')
    if not result.observations or any(not o.rights.display_allowed or not o.rights.storage_allowed for o in result.observations):
        raise ValueError('Derechos insuficientes para exportación local.')
    # Referencias y quotes no se rellenan para fabricar barras OHLCV.
    return VibeResearchInput(observations=result.observations)
