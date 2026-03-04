from __future__ import annotations

from dataclasses import dataclass

from .config import BotConfig
from .strategy import Signal


@dataclass
class RiskDecision:
    approved: bool
    reason: str
    quantity: int = 0


class PropRiskManager:
    def __init__(self, cfg: BotConfig):
        self.cfg = cfg
        self.day_start_equity = cfg.starting_equity
        self.high_watermark = cfg.starting_equity
        self.equity = cfg.starting_equity
        self.trades_today = 0
        self.consecutive_losses = 0
        self.trading_halted = False

    def reset_day(self, equity: float) -> None:
        self.day_start_equity = equity
        self.trades_today = 0
        self.consecutive_losses = 0

    def register_pnl(self, pnl: float) -> None:
        self.equity += pnl
        self.high_watermark = max(self.high_watermark, self.equity)
        self.consecutive_losses = self.consecutive_losses + 1 if pnl < 0 else 0
        if self._daily_loss_exceeded() or self._drawdown_exceeded() or self.consecutive_losses >= self.cfg.limits.max_consecutive_losses:
            self.trading_halted = True

    def check(self, signal: Signal, price: float) -> RiskDecision:
        if self.trading_halted:
            return RiskDecision(False, "kill_switch_active")
        if self.trades_today >= self.cfg.limits.max_trades_per_day:
            return RiskDecision(False, "max_trades_per_day")
        max_position_value = self.equity * self.cfg.limits.max_position_pct
        risk_budget = self.equity * self.cfg.risk.risk_per_trade_pct
        stop_dist = abs(price - signal.stop_price)
        if stop_dist <= 0:
            return RiskDecision(False, "invalid_stop_distance")
        qty_from_risk = int(risk_budget / stop_dist)
        qty_from_position = int(max_position_value / max(price, 0.01))
        qty = min(qty_from_risk, qty_from_position)
        if self.cfg.broker.account_type == "cash":
            qty = min(qty, int(self.equity / max(price, 0.01)))
        if qty <= 0:
            return RiskDecision(False, "size_below_min")
        self.trades_today += 1
        return RiskDecision(True, "approved", quantity=qty)

    def _daily_loss_exceeded(self) -> bool:
        return (self.day_start_equity - self.equity) / self.day_start_equity >= self.cfg.limits.daily_max_loss_pct

    def _drawdown_exceeded(self) -> bool:
        return (self.high_watermark - self.equity) / self.high_watermark >= self.cfg.limits.max_drawdown_pct
