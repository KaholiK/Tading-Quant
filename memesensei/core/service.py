from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import List, Optional

from .clients.dexscreener import DexScreenerClient, PairData
from .clients.rugcheck import RugCheckClient
from .clients.birdeye import BirdeyeClient
from .clients.jupiter import JupiterClient
from .config import CoreConfig
from .execution.executor import Executor
from .portfolio.store import PortfolioStore
from .risk.manager import RiskManager
from .safety.gates import SafetyGates
from .strategies.momentum import MomentumStrategy
from .strategies.mean_reversion import MeanReversionStrategy
from .utils.logging import configure_logging
from .utils import metrics

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Decision:
    pair: PairData
    allowed: bool
    reason: str
    signal: Optional[str] = None


class CoreService:
    def __init__(
        self,
        config: CoreConfig,
        store: Optional[PortfolioStore] = None,
        dex: Optional[DexScreenerClient] = None,
        rugcheck: Optional[RugCheckClient] = None,
        birdeye: Optional[BirdeyeClient] = None,
        jupiter: Optional[JupiterClient] = None,
    ):
        configure_logging()
        self.config = config
        db_path = os.getenv("MEMESENSEI_DB_PATH")
        self.store = store or PortfolioStore(db_path or "data/memesensei.db")
        self.dex = dex or DexScreenerClient(retry_limit=config.dex_retry_limit)
        self.rugcheck = rugcheck or RugCheckClient()
        self.birdeye = birdeye or (BirdeyeClient(config.birdeye_api_key) if config.birdeye_api_key else None)
        self.jupiter = jupiter or JupiterClient()
        self.executor = Executor(config, self.jupiter)
        self.risk = RiskManager(config)
        self.safety = SafetyGates(config, self.rugcheck, self.birdeye)
        self.strategy1 = MomentumStrategy(config)
        self.strategy2 = MeanReversionStrategy(config)
        self.paused = False
        self.kill_switch = config.kill_switch
        self.last_scan_time: Optional[float] = None
        self.last_decision: Optional[Decision] = None

    async def tick(self) -> Optional[Decision]:
        self.last_scan_time = time.time()
        pairs = await self.dex.fetch_latest_boosts()
        for pair in pairs:
            decision = await self._evaluate_pair(pair)
            if decision:
                self.last_decision = decision
                return decision
        return None

    async def _evaluate_pair(self, pair: PairData) -> Decision:
        if self.kill_switch or self.paused:
            decision = Decision(pair=pair, allowed=False, reason="paused_or_killed")
            self.store.record_decision(pair.address, "skip", False, decision.reason)
            return decision

        safety = await self.safety.evaluate(pair)
        if not safety.allowed:
            self.store.record_decision(pair.address, "blocked", False, safety.reason)
            return Decision(pair=pair, allowed=False, reason=safety.reason)

        signal = None
        if self.config.enable_strategy_s1:
            sig = self.strategy1.generate(pair)
            if sig:
                signal = sig.action
        if not signal and self.config.enable_strategy_s2:
            sig = self.strategy2.generate(pair)
            if sig:
                signal = sig.action
        if not signal:
            self.store.record_decision(pair.address, "no_signal", False, "no_signal")
            return Decision(pair=pair, allowed=False, reason="no_signal")

        risk_decision = self.risk.can_open(self.config.max_position_usd, self.config.slippage_bps, pair.liquidity_usd)
        if not risk_decision.allowed:
            self.store.record_decision(pair.address, "risk_block", False, risk_decision.reason)
            return Decision(pair=pair, allowed=False, reason=risk_decision.reason, signal=signal)

        await self._execute_trade(pair, signal)
        self.store.record_decision(pair.address, signal, True, "executed")
        return Decision(pair=pair, allowed=True, reason="executed", signal=signal)

    async def _execute_trade(self, pair: PairData, signal: str) -> None:
        # simplified: buy using max_position_usd
        result = await self.executor.execute_swap(self.config.max_position_usd, pair.quote_token, pair.base_token)
        self.store.record_position(pair.address, self.config.max_position_usd, pair.price_usd)
        self.store.record_trade(pair.address, signal, self.config.max_position_usd, pair.price_usd)
        self.risk.record_open(self.config.max_position_usd)
        logger.info("trade executed", extra={"pair": pair.address, "txid": result.txid})

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def toggle_kill_switch(self, state: bool) -> None:
        self.kill_switch = state
        self.config.kill_switch = state

    async def run(self, duration_seconds: int = 0, loop_sleep: float = 5.0) -> None:
        start = time.time()
        while True:
            await self.tick()
            if duration_seconds and time.time() - start >= duration_seconds:
                break
            await asyncio.sleep(loop_sleep)

    def status(self) -> dict:
        return {
            "chain": self.config.chain,
            "dry_run": self.config.dry_run,
            "kill_switch": self.kill_switch,
            "paused": self.paused,
            "last_scan_time": self.last_scan_time,
            "last_decision": self.last_decision.reason if self.last_decision else None,
        }

