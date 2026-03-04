from __future__ import annotations

from dataclasses import dataclass

from .config import ExecutionConfig


@dataclass
class Fill:
    side: str
    quantity: int
    fill_price: float
    fees: float
    slippage: float


class SimulatedExecutor:
    def __init__(self, cfg: ExecutionConfig):
        self.cfg = cfg

    def execute(self, side: str, quantity: int, mid_price: float) -> Fill:
        slip = mid_price * (self.cfg.slippage_bps / 10000)
        if side == "BUY":
            fill_price = mid_price + slip
        else:
            fill_price = mid_price - slip
        filled_qty = max(1, int(quantity * self.cfg.partial_fill_ratio))
        fees = filled_qty * self.cfg.commission_per_share
        return Fill(side=side, quantity=filled_qty, fill_price=fill_price, fees=fees, slippage=slip * filled_qty)
