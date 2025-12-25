from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict

from ..clients.jupiter import JupiterClient, Quote
from ..utils import metrics

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExecutionResult:
    txid: str
    received: float
    simulated: bool


class Executor:
    def __init__(self, config, jupiter: JupiterClient):
        self.config = config
        self.jupiter = jupiter

    async def execute_swap(self, in_amount: float, input_mint: str, output_mint: str) -> ExecutionResult:
        quote = await self.jupiter.quote(in_amount, input_mint, output_mint, self.config.slippage_bps)
        if quote.slippage_bps > self.config.slippage_bps:
            raise RuntimeError("slippage_cap")
        if self.config.dry_run:
            logger.info("dry-run swap", extra={"in": in_amount, "out": quote.out_amount})
            metrics.trades_total.labels(type="paper").inc()
            return ExecutionResult(txid="dry-run", received=quote.out_amount, simulated=True)
        swap = await self.jupiter.swap(quote)
        txid = swap.get("txid", "unknown")
        metrics.trades_total.labels(type="live").inc()
        return ExecutionResult(txid=txid, received=quote.out_amount, simulated=False)

