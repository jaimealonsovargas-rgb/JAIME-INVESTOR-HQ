"""Typed bridge from a reviewed retrospective manifest to the pure engine.

No acquisition, orders or portfolio writes. Every run rechecks trust, the frozen
manifest, the internal review expiry, and the preregistered configuration grid.
"""
from datetime import datetime, timezone
from decimal import localcontext, ROUND_HALF_UP
import json
from types import SimpleNamespace
from typing import Annotated, Literal

from pydantic import Field
from app.admission_contracts import Candidate, fingerprint
from app.b32_review import PROTOCOL, PROTOCOL_PATH, PROTOCOL_SHA256, checked_file
from app.dataset_admission import evaluate
from app.dataset_evidence import registered_evidence
from app.quant_contracts import Contract, Bar, StrategyGenome, ExperimentConfig
from app.quant_engine import ExperimentRejected, _calculate

Hash = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]


class RetrospectiveDataset(Contract):
    version: Literal['retrospective-bars-v1'] = 'retrospective-bars-v1'
    kind: Literal['MARKET_RETROSPECTIVE']
    candidate: Candidate
    manifest_id: Hash
    protocol_sha256: Hash


class RetrospectiveGenome(StrategyGenome):
    protocol: Literal['RETROSPECTIVE_EXPLORATORY'] = 'RETROSPECTIVE_EXPLORATORY'


class RetrospectiveConfig(ExperimentConfig):
    genome: RetrospectiveGenome
    unit: Literal['USD'] = 'USD'
    common_warmup: Literal[60] = 60
    protocol_sha256: Hash


def planned_configs():
    protocol = json.loads(checked_file(PROTOCOL_PATH, PROTOCOL_SHA256))
    result = []
    for variant in protocol['variants']:
        for cost in protocol['cost_scenarios']:
            config = RetrospectiveConfig.model_validate(dict(
                genome=dict(family=variant['family'],lookback=variant['lookback'],
                    mechanism='Persistencia de tendencia diaria; caso retrospectivo de un activo.',
                    falsification='Superar ambos controles con los dos costes sin aumentar drawdown frente a comprar/mantener.'),
                costs={k:v for k,v in cost.items() if k!='id'},
                initial_cash=protocol['calculation']['initial_cash'],protocol_sha256=PROTOCOL_SHA256))
            result.append((variant['id']+'-'+cost['id'],config.model_dump(mode='json')))
    return result


def admitted_replay(dataset,config,manifest_store,now):
    request=RetrospectiveDataset.model_validate(dataset)
    cfg=RetrospectiveConfig.model_validate(config)
    if request.protocol_sha256!=PROTOCOL_SHA256 or cfg.protocol_sha256!=PROTOCOL_SHA256:
        raise ExperimentRejected('PROTOCOL_HASH_MISMATCH')
    if cfg.model_dump(mode='json') not in [v for _,v in planned_configs()]:
        raise ExperimentRejected('CONFIG_OUTSIDE_PREREGISTERED_GRID')
    candidate=request.candidate.model_dump()
    evidence=registered_evidence(candidate)
    manifest=evaluate(candidate,evidence,protocol=PROTOCOL)
    if manifest['readiness']['backtest']!='BACKTEST_READY_EXPLORATORY':
        raise ExperimentRejected('DATASET_ADMISSION_BLOCKED')
    if request.manifest_id!=manifest['manifest_id']:
        raise ExperimentRejected('ADMISSION_MANIFEST_CHANGED')
    try:
        saved=manifest_store.read(request.manifest_id)
    except (OSError,ValueError,KeyError,TypeError):
        raise ExperimentRejected('ADMISSION_MANIFEST_UNAVAILABLE') from None
    if saved!=manifest:
        raise ExperimentRejected('ADMISSION_MANIFEST_CHANGED')
    if now.utcoffset() is None or not datetime.fromisoformat(manifest['as_of'])<=now.astimezone(timezone.utc)<=datetime.fromisoformat(manifest['scope']['review_expires_at']):
        raise ExperimentRejected('DATASET_REVIEW_EXPIRED_OR_CLOCK_INVALID')
    calendar=next(r['payload']['sessions'] for r in evidence['records'] if r['kind']=='calendar')
    # available_at here is a simulation assumption, never historical publication evidence.
    bars=tuple(Bar.model_validate(dict(opens_at=s['open'],closes_at=s['close'],available_at=s['close'],
        open=b['open'],close=b['close'])) for b,s in zip(candidate['bars'],calendar))
    replay=SimpleNamespace(bars=bars,currency=candidate['currency'])
    return replay,cfg,manifest


def run_retrospective(dataset,config,manifest_store,now):
    replay,cfg,manifest=admitted_replay(dataset,config,manifest_store,now)
    with localcontext() as context:
        context.prec=40
        context.rounding=ROUND_HALF_UP
        result=_calculate(replay,cfg,warmup=cfg.common_warmup)
    result.update(kind='MARKET_RETROSPECTIVE',acceptance='EXPLORATORY_ONLY',execution_ready=False,
        manifest_id=manifest['manifest_id'],protocol_sha256=PROTOCOL_SHA256,
        evaluation_start=replay.bars[cfg.common_warmup].opens_at.isoformat(),
        warmup_sessions=cfg.common_warmup,evaluation_sessions=len(replay.bars)-cfg.common_warmup,
        knowledge_time_basis='SIMULATED_PRIOR_SESSION_CLOSE_NOT_PUBLICATION',
        fill_basis='IEX_DAILY_OPEN_PROXY',point_in_time_claim=False,oos_reserved=False,
        limitations=['EX_POST_SINGLE_SURVIVOR','CURRENT_REVISED_HISTORY_NOT_PIT',
            'IEX_SINGLE_VENUE_OPEN_PROXY','NO_LIQUIDITY_OR_MARKET_IMPACT_MODEL',
            'NO_OOS_OR_STATISTICAL_ACCEPTANCE','NO_TAX_FX_OR_CASH_INTEREST',
            'TERMINAL_MARK_WITHOUT_LIQUIDATION'])
    return result
