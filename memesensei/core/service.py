from __future__ import annotations

import asyncio
import logging
import time
from typing import List

from memesensei.core.config.models import Config
from memesensei.core.execution.executor import ExecutionClient
from memesensei.core.portfolio.state import PortfolioStore
from memesensei.core.risk.manager import RiskManager
from memesensei.core.safety.rugcheck import RugCheckGate, RugCheckReport
from memesensei.core.scanners.dexscreener import DexScreenerClient
from memesensei.core.strategies.momentum import MarketSnapshot, MomentumBreakoutStrategy
from memesensei.core.strategies.mean_reversion import MeanReversionStrategy, MeanReversionWindow

logger = logging.getLogger(__name__)


class CoreService:
    def __init__(self, config: Config):
        self.config = config
        self.store = PortfolioStore()
        self.risk = RiskManager(config.risk_limits)
        self.scanner = DexScreenerClient()
        self.rug_gate = RugCheckGate(config.risk_limits.rugcheck_threshold)
        self.executor = ExecutionClient(config.risk_limits, self.store, dry_run=config.dry_run)
        self.kill_switch = config.kill_switch
        self.paused = False
        self.last_scan_time: float | None = None
        self.last_decision: str = "idle"

    async def run_once(self) -> None:
        self.last_scan_time = time.time()
        candidates = []
        try:
            candidates = await self.scanner.fetch_latest()
        except Exception as exc:  # pragma: no cover
            logger.error("scanner failed: %s", exc)
            return
        for pair in candidates:
            if self.kill_switch or self.paused:
                self.last_decision = "paused"
                return
            report = RugCheckReport(address=pair.token_address, risk_score=0.1, trust_score=0.9)
            ok, reason = self.rug_gate.evaluate(report)
            if not ok:
                self.last_decision = reason or "rugcheck blocked"
                continue
            decision = self.risk.can_open_position(pair.liquidity_usd, pair.volume_5m_usd, pair.volume_1h_usd, pair.age_seconds)
            if not decision.allowed:
                self.last_decision = decision.reason or "risk block"
                continue
            signal = "hold"
            if self.config.enable_strategy_s1:
                signal = MomentumBreakoutStrategy(
                    self.config.risk_limits.min_vol_5m_usd, self.config.risk_limits.min_liquidity_usd
                ).generate_signal(
                    MarketSnapshot(price=1.0, volume_5m=pair.volume_5m_usd, liquidity=pair.liquidity_usd)
                )
            if signal == "hold" and self.config.enable_strategy_s2:
                signal = MeanReversionStrategy().generate_signal(
                    MeanReversionWindow(price=1.0, average=1.0, std=0.01)
                )
            if signal != "buy":
                self.last_decision = "no signal"
                continue
            await self._open_trade(pair.token_address)
            self.last_decision = "trade opened"
            break

    async def _open_trade(self, token: str) -> None:
        amount = self.config.risk_limits.max_position_usd
        await self.executor.execute_swap(token, amount=amount, price=1.0, reason="strategy signal")
        self.risk.update_open_positions(len(self.store.list_positions()))

    async def run(self, run_seconds: int = 60):
        start = time.time()
        while time.time() - start < run_seconds:
            await self.run_once()
            await asyncio.sleep(1)

    def status(self) -> dict:
        return {
            "kill_switch": self.kill_switch,
            "paused": self.paused,
            "dry_run": self.config.dry_run,
            "last_scan": self.last_scan_time,
            "last_decision": self.last_decision,
        }

    def toggle_kill(self, state: bool) -> None:
        self.kill_switch = state
        if state:
            self.paused = True

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
