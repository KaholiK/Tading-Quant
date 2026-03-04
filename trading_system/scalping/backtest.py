from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
import pandas as pd

from .config import BotConfig
from .data_adapter import Bar, DataAdapter
from .execution import SimulatedExecutor
from .risk import PropRiskManager
from .strategy import CompositeScalpingStrategy


@dataclass
class Trade:
    symbol: str
    side: str
    qty: int
    entry_price: float
    exit_price: float
    pnl: float
    module: str


class BacktestEngine:
    def __init__(self, cfg: BotConfig, adapter: DataAdapter):
        self.cfg = cfg
        self.adapter = adapter
        self.strategy = CompositeScalpingStrategy(cfg.strategy)
        self.risk = PropRiskManager(cfg)
        self.executor = SimulatedExecutor(cfg.execution)
        self.windows: dict[str, list[Bar]] = {s: [] for s in cfg.universe.symbols}
        self.positions: dict[str, dict] = {}
        self.trades: list[Trade] = []
        self.equity_curve: list[float] = [cfg.starting_equity]

    def run(self) -> dict:
        for bar in self.adapter.stream():
            self._on_bar(bar)
        self._force_close_last()
        return self._report()

    def _on_bar(self, bar: Bar) -> None:
        rows = self.windows.setdefault(bar.symbol, [])
        rows.append(bar)
        if len(rows) > 200:
            rows.pop(0)
        frame = pd.DataFrame([r.__dict__ for r in rows])

        if bar.symbol in self.positions:
            self._manage_position(bar, frame)
            return

        sig = self.strategy.evaluate(bar.symbol, frame)
        if not sig:
            return
        decision = self.risk.check(sig, bar.close)
        if not decision.approved:
            return
        fill = self.executor.execute(sig.side, decision.quantity, bar.close)
        self.positions[bar.symbol] = {
            "side": sig.side,
            "qty": fill.quantity,
            "entry": fill.fill_price,
            "stop": sig.stop_price,
            "module": sig.module,
            "bars": 0,
        }

    def _manage_position(self, bar: Bar, frame: pd.DataFrame) -> None:
        pos = self.positions[bar.symbol]
        pos["bars"] += 1
        stop_hit = bar.low <= pos["stop"] if pos["side"] == "BUY" else bar.high >= pos["stop"]
        rr = self.cfg.risk.take_profit_r_mult
        risk_dist = abs(pos["entry"] - pos["stop"])
        tp = pos["entry"] + rr * risk_dist if pos["side"] == "BUY" else pos["entry"] - rr * risk_dist
        tp_hit = bar.high >= tp if pos["side"] == "BUY" else bar.low <= tp
        time_exit = pos["bars"] >= self.cfg.risk.time_stop_bars
        if stop_hit or tp_hit or time_exit:
            side = "SELL" if pos["side"] == "BUY" else "BUY"
            fill = self.executor.execute(side, pos["qty"], bar.close)
            pnl_per_share = (fill.fill_price - pos["entry"]) if pos["side"] == "BUY" else (pos["entry"] - fill.fill_price)
            pnl = pnl_per_share * pos["qty"] - fill.fees
            self.risk.register_pnl(pnl)
            self.equity_curve.append(self.risk.equity)
            self.trades.append(Trade(bar.symbol, pos["side"], pos["qty"], pos["entry"], fill.fill_price, pnl, pos["module"]))
            del self.positions[bar.symbol]

    def _force_close_last(self) -> None:
        for symbol, pos in list(self.positions.items()):
            pnl = -pos["qty"] * self.cfg.execution.commission_per_share
            self.risk.register_pnl(pnl)
            self.equity_curve.append(self.risk.equity)
            self.trades.append(Trade(symbol, pos["side"], pos["qty"], pos["entry"], pos["entry"], pnl, pos["module"]))
            del self.positions[symbol]

    def _report(self) -> dict:
        if not self.trades:
            return {"trades": 0, "ending_equity": self.risk.equity}
        pnls = np.array([t.pnl for t in self.trades])
        wins = pnls[pnls > 0]
        losses = pnls[pnls < 0]
        daily_returns = pd.Series(self.equity_curve).pct_change().dropna()
        sharpe = (daily_returns.mean() / daily_returns.std()) * sqrt(252) if len(daily_returns) > 2 and daily_returns.std() else 0.0
        profit_factor = float(wins.sum() / abs(losses.sum())) if losses.size else 0.0
        max_dd = self._max_drawdown(np.array(self.equity_curve))
        return {
            "trades": len(self.trades),
            "ending_equity": self.risk.equity,
            "win_rate": float((pnls > 0).mean()),
            "avg_win": float(wins.mean()) if wins.size else 0.0,
            "avg_loss": float(losses.mean()) if losses.size else 0.0,
            "expectancy": float(pnls.mean()),
            "profit_factor": profit_factor,
            "sharpe": float(sharpe),
            "max_drawdown": float(max_dd),
            "time_in_market": len(self.trades),
            "prop_rule_breaches": int(self.risk.trading_halted),
        }

    @staticmethod
    def _max_drawdown(curve: np.ndarray) -> float:
        roll_max = np.maximum.accumulate(curve)
        drawdowns = (roll_max - curve) / roll_max
        return float(np.max(drawdowns))


def walk_forward_validate(cfg: BotConfig, frame: pd.DataFrame) -> list[dict]:
    windows = cfg.validation.walk_forward_windows
    step = len(frame) // (windows + 1)
    reports = []
    for i in range(windows):
        train_end = step * (i + 1)
        test_end = step * (i + 2)
        test = frame.iloc[train_end:test_end].copy()
        if test.empty:
            continue
        csv_path = f"/tmp/wf_{i}.csv"
        test.to_csv(csv_path, index=False)
        from .data_adapter import CSVDataAdapter

        bt = BacktestEngine(cfg, CSVDataAdapter(csv_path, cfg.universe.symbols))
        reports.append(bt.run())
    return reports


def monte_carlo_trade_shuffle(trades: list[Trade], runs: int = 500) -> dict:
    if not trades:
        return {"runs": runs, "p5": 0.0, "p50": 0.0, "p95": 0.0}
    pnls = np.array([t.pnl for t in trades])
    outcomes = []
    for _ in range(runs):
        shuffled = np.random.permutation(pnls)
        outcomes.append(float(shuffled.sum()))
    return {
        "runs": runs,
        "p5": float(np.percentile(outcomes, 5)),
        "p50": float(np.percentile(outcomes, 50)),
        "p95": float(np.percentile(outcomes, 95)),
    }
