"""Pure reference backtest: long/cash, whole shares, explicit next-open fills.

This module has no database, provider, broker or LLM dependency. Terminal inventory
is marked at the last close; no fictitious liquidation or statistical approval.
"""
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, localcontext
from time import monotonic

from app.quant_contracts import ExperimentConfig, SyntheticDataset

ENGINE_VERSION = 'reference-daily-v2'
D = Decimal


class ExperimentRejected(ValueError):
    pass


def amount(value):
    return format(value, 'f')


def run_reference(dataset: SyntheticDataset, config: ExperimentConfig):
    if config.genome.lookback and len(dataset.bars) <= config.genome.lookback:
        raise ExperimentRejected('INSUFFICIENT_SYNTHETIC_BARS')
    with localcontext() as context:
        context.prec = 40
        context.rounding = ROUND_HALF_UP
        return _calculate(dataset, config)


def _calculate(dataset, config, *, warmup=0):
    start = monotonic()
    cash, shares = config.initial_cash, 0
    commission = D(0)
    slippage = D(0)
    fills, curve, decisions = [], [], []
    peak = cash
    max_drawdown = D(0)
    costs, genome = config.costs, config.genome

    def fee(notional):
        return (costs.fixed_per_fill + notional * costs.commission_bps / 10000).quantize(D('.01'))

    for i, bar in enumerate(dataset.bars):
        if monotonic() - start > 30:
            raise TimeoutError('REFERENCE_DEADLINE')
        # Only earlier closes are allowed to influence today's order.
        known_at, target, signal = None, 0, 'WARMUP'
        if i < warmup:
            pass  # Common flat warmup, including buy/hold and shorter SMA windows.
        elif genome.family == 'BUY_HOLD':
            target, signal = 1, 'PRECOMMITTED_BUY_HOLD'
        elif genome.family == 'CASH':
            signal = 'CASH_CONTROL'
        elif i >= genome.lookback:
            window = dataset.bars[i-genome.lookback:i]
            known_at = window[-1].available_at.isoformat()
            target = int(window[-1].close > sum(b.close for b in window) / genome.lookback)
            signal = 'ABOVE_SMA' if target else 'AT_OR_BELOW_SMA'
        decision = dict(execution_at=bar.opens_at.isoformat(), known_at=known_at,
                        target=target, signal=signal, outcome='HOLD')
        side = 'BUY' if target and not shares else 'SELL' if not target and shares else None
        if side:
            direction = D(1) if side == 'BUY' else D(-1)
            price = bar.open * (1 + direction * costs.slippage_bps / 10000)
            if side == 'BUY':
                # Monotone integer search includes fee rounding, never overdraws cash.
                low, high = 0, int((cash / price).to_integral_value(rounding=ROUND_FLOOR))
                while low < high:
                    middle = (low + high + 1) // 2
                    if middle * price + fee(middle * price) <= cash:
                        low = middle
                    else:
                        high = middle - 1
                quantity = low
            else:
                quantity = shares
            if quantity:
                notional = quantity * price
                charged = fee(notional)
                next_cash = cash - notional - charged if side == 'BUY' else cash + notional - charged
                if next_cash < 0:
                    raise ExperimentRejected('EXIT_COST_EXCEEDS_CASH')
                cash = next_cash
                shares += quantity if side == 'BUY' else -quantity
                commission += charged
                slippage += abs(price - bar.open) * quantity
                fills.append(dict(at=bar.opens_at.isoformat(), known_at=known_at, side=side,
                                  quantity=quantity, reference_open=amount(bar.open), price=amount(price),
                                  commission=amount(charged), cash_after=amount(cash), shares_after=shares))
                decision['outcome'] = side
            else:
                decision['outcome'] = 'INSUFFICIENT_CASH_FOR_ONE_SHARE'
        decisions.append(decision)
        equity = cash + shares * bar.close
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak)
        curve.append(dict(at=bar.closes_at.isoformat(), cash=amount(cash), shares=shares, equity=amount(equity)))
    final = cash + shares * dataset.bars[-1].close
    return dict(engine_version=ENGINE_VERSION, kind='SYNTHETIC_TEST', unit=dataset.currency,
                acceptance='ENGINEERING_ONLY', execution_ready=False, family=genome.family,
                terminal_valuation='LAST_CLOSE_MARK_NO_LIQUIDATION', initial_cash=amount(config.initial_cash),
                final_cash=amount(cash), final_shares=shares, final_equity=amount(final),
                net_pnl=amount(final-config.initial_cash), return_fraction=amount(final/config.initial_cash-1),
                max_drawdown_fraction=amount(max_drawdown), commission=amount(commission),
                slippage_cost=amount(slippage), fills=fills, curve=curve, decisions=decisions,
                limitations=['SYNTHETIC_ONLY', 'NO_LIQUIDITY_MODEL', 'NO_FX_OR_CORPORATE_ACTIONS',
                             'NO_OOS_OR_STATISTICAL_ACCEPTANCE'])
