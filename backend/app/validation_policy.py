"""B4 v1. Temporal protocol and statistical rules for a frozen search family."""
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from fractions import Fraction
from math import comb


@dataclass(frozen=True)
class Policy:
    version: str = 'strategy-validation-v1'
    minimum_train_sessions: int = 126
    minimum_validation_sessions: int = 63
    minimum_oos_sessions: int = 126
    block_sessions: int = 10
    minimum_blocks: int = 12
    family_alpha: str = '0.05'
    benchmark_ids: tuple[str, str] = ('cash', 'buy_hold')
    screen: str = 'NET_ABOVE_BOTH_DRAWDOWN_AT_MOST_BUY_HOLD_EVERY_COST'
    test: str = 'ONE_SIDED_PAIRED_BLOCK_SIGN_TIES_AS_NONWINS'
    adjustment: str = 'MAX_P_ACROSS_CONTROLS_AND_COSTS_BONFERRONI_ALL_PLANNED_HYPOTHESES'


POLICY = Policy()


@dataclass(frozen=True, order=True)
class Span:
    first: str
    last: str

    def __post_init__(self):
        if not (date.fromisoformat(self.first).isoformat() == self.first
                and date.fromisoformat(self.last).isoformat() == self.last and self.first <= self.last):
            raise ValueError('INVALID_DATE_SPAN')

    def overlaps(self, other):
        return self.first <= other.last and other.first <= self.last


@dataclass(frozen=True)
class Fold:
    train: Span
    validation: Span


@dataclass(frozen=True)
class Reservation:
    folds: tuple[Fold, ...]
    oos: Span
    # Forward reach of labels/positions plus extra flat sessions at each boundary.
    purge_sessions: int
    embargo_sessions: int
    locked_at: datetime
    first_oos_access_at: datetime
    locked_design_hash: str | None = None


@dataclass(frozen=True)
class Exposure:
    source: str
    instruments: tuple[str, ...]
    period: Span


@dataclass(frozen=True)
class Study:
    sessions: tuple[str, ...]
    instruments: tuple[str, ...]
    ancestor_instruments: tuple[str, ...]
    history: tuple[Exposure, ...]
    evaluation: Span
    reservation: Reservation | None = None
    point_in_time: bool = False
    exposure_inventory_complete: bool = False
    # A reviewed record for the independence/equal-sign null of the chosen blocks.
    # Only a trusted campaign adapter may supply this reference.
    block_assumptions_ref: str | None = None
    search_protocol_ref: str | None = None


def temporal_checks(study):
    days = study.sessions
    if (not days or tuple(sorted(set(days))) != days or not study.instruments
            or any(date.fromisoformat(d).isoformat() != d for d in days)):
        raise ValueError('INVALID_VALIDATION_CALENDAR_OR_UNIVERSE')
    index = {day: i for i, day in enumerate(days)}
    if study.evaluation.first not in index or study.evaluation.last not in index:
        raise ValueError('EVALUATION_OUTSIDE_CALENDAR')
    reasons = []
    if not study.point_in_time:
        reasons.append('POINT_IN_TIME_NOT_ESTABLISHED')
    if not study.exposure_inventory_complete:
        reasons.append('EXPOSURE_INVENTORY_NOT_CERTIFIED')
    if not study.block_assumptions_ref:
        reasons.append('BLOCK_SIGN_ASSUMPTIONS_UNVERIFIED')
    reservation = study.reservation
    if reservation is None:
        return reasons + ['NO_RESERVED_OUT_OF_SAMPLE'], None
    if (type(reservation.purge_sessions) is not int or type(reservation.embargo_sessions) is not int
            or min(reservation.purge_sessions, reservation.embargo_sessions) < 0):
        raise ValueError('INVALID_PURGE_OR_EMBARGO')
    universe = set(study.instruments).union(study.ancestor_instruments)
    protected = [reservation.oos, *(fold.validation for fold in reservation.folds)]
    if any(universe.intersection(e.instruments) and any(p.overlaps(e.period) for p in protected)
           for e in study.history):
        reasons.append('PRIOR_OR_INHERITED_EXPOSURE')
    lock, accessed = reservation.locked_at, reservation.first_oos_access_at
    if lock.utcoffset() is None or accessed.utcoffset() is None:
        raise ValueError('TIMEZONE_REQUIRED')
    if not reservation.folds:
        return reasons + ['MISSING_DEVELOPMENT_FOLDS'], None
    first_validation = reservation.folds[0].validation.first
    # This version accepts prospectively reserved sessions only. Retrospective
    # assertions of blindness do not restore a holdout.
    if (lock >= accessed or lock.astimezone(timezone.utc).date().isoformat() >= first_validation
            or accessed.astimezone(timezone.utc).date().isoformat() <= reservation.oos.last):
        reasons.append('RESERVATION_CHRONOLOGY_INVALID')
    periods = [reservation.oos, *(p for f in reservation.folds for p in (f.train, f.validation))]
    if any(p.first not in index or p.last not in index for p in periods):
        return reasons + ['PARTITION_OUTSIDE_CALENDAR'], None
    gap = reservation.purge_sessions + reservation.embargo_sessions
    previous_end = -1
    for fold in reservation.folds:
        a, b = index[fold.train.first], index[fold.train.last]
        c, d = index[fold.validation.first], index[fold.validation.last]
        if c - b - 1 < gap or (previous_end >= 0 and c - previous_end - 1 < gap):
            reasons.append('TEMPORAL_OVERLAP_OR_EMBARGO')
        if c < index[study.evaluation.first] or d > index[study.evaluation.last]:
            reasons.append('VALIDATION_OUTSIDE_EVALUATION')
        if b - a + 1 < POLICY.minimum_train_sessions or d - c + 1 < POLICY.minimum_validation_sessions:
            reasons.append('DEVELOPMENT_SAMPLE_TOO_SHORT')
        previous_end = d
    start, end = index[reservation.oos.first], index[reservation.oos.last]
    if start - max(index[f.validation.last] for f in reservation.folds) - 1 < gap:
        reasons.append('TEMPORAL_OVERLAP_OR_EMBARGO')
    if start < index[study.evaluation.first] or end > index[study.evaluation.last]:
        reasons.append('OOS_OUTSIDE_EVALUATION')
    if end - start + 1 < max(POLICY.minimum_oos_sessions, POLICY.block_sessions * POLICY.minimum_blocks):
        reasons.append('OOS_SAMPLE_TOO_SHORT')
    return sorted(set(reasons)), (start, end)


def block_sign_test(nav, benchmark, initial, start, end):
    """Exact upper binomial tail. Full non-overlapping blocks, no fitted block length."""
    width = POLICY.block_sessions
    blocks, remainder = divmod(end - start + 1, width)
    if blocks < POLICY.minimum_blocks:
        raise ValueError('OOS_SAMPLE_TOO_SHORT')
    wins = 0
    for left in range(start, start + blocks * width, width):
        right = left + width - 1
        before = nav[left - 1] if left else initial
        control_before = benchmark[left - 1] if left else initial
        # Avoid decimal-context rounding at the boundary between a win and a tie.
        wins += Fraction(nav[right]) * Fraction(control_before) > Fraction(benchmark[right]) * Fraction(before)
    numerator = sum(comb(blocks, k) for k in range(wins, blocks + 1))
    return Fraction(numerator, 2 ** blocks), dict(blocks=blocks, wins=wins, unused_tail_sessions=remainder)


def probability(value):
    return format(Decimal(value.numerator) / Decimal(value.denominator), '.12g')


def export_policy():
    return asdict(POLICY)


def export_reservation(reservation):
    if reservation is None:
        return None
    data = asdict(reservation)
    for field in ('locked_at', 'first_oos_access_at'):
        data[field] = data[field].astimezone(timezone.utc).isoformat()
    return data
