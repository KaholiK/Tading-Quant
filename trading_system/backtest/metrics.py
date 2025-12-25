import math
from typing import Iterable, List


def _max_drawdown(equity_curve: List[float]) -> float:
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        drawdown = (peak - value)
        max_dd = max(max_dd, drawdown)
    return max_dd


def performance_report(returns: Iterable[float], equity_curve: Iterable[float]):
    returns = list(returns)
    equity_curve = list(equity_curve)
    if len(returns) == 0 or len(equity_curve) == 0:
        return {}
    mean = sum(returns) / len(returns)
    std = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns)) if returns else 0
    sharpe = mean / (std + 1e-9)
    downside = [r for r in returns if r < 0]
    down_mean = sum(downside) / len(downside) if downside else 0
    down_std = math.sqrt(sum((r - down_mean) ** 2 for r in downside) / len(downside)) if downside else 0
    sortino = mean / (down_std + 1e-9)
    max_drawdown = _max_drawdown(equity_curve)
    calmar = mean / (max_drawdown / (equity_curve[0] if equity_curve else 1) + 1e-9)
    win_rate = float(sum(1 for r in returns if r > 0) / len(returns))
    expectancy = mean
    return {
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "calmar": float(calmar),
        "max_drawdown": float(max_drawdown),
        "win_rate": win_rate,
        "expectancy": expectancy,
    }
