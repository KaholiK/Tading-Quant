from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BrokerConfig:
    provider: str = "alpaca"
    account_type: str = "cash"
    paper: bool = True


@dataclass
class LimitsConfig:
    daily_max_loss_pct: float = 0.01
    max_drawdown_pct: float = 0.05
    max_position_pct: float = 0.10
    max_trades_per_day: int = 50
    max_concurrent_positions: int = 2
    max_consecutive_losses: int = 4
    max_slippage_bps: float = 8.0


@dataclass
class RiskConfig:
    risk_per_trade_pct: float = 0.0015
    stop_atr_mult: float = 1.2
    take_profit_r_mult: float = 1.5
    trailing_stop_atr_mult: float = 1.0
    time_stop_bars: int = 8
    force_flat_time_et: str = "15:55"


@dataclass
class ExecutionConfig:
    order_type: str = "marketable_limit"
    limit_offset_bps: float = 2.0
    commission_per_share: float = 0.0035
    slippage_bps: float = 1.5
    partial_fill_ratio: float = 0.9


@dataclass
class StrategyConfig:
    primary_timeframe: str = "1m"
    modules_enabled: list[str] = field(default_factory=lambda: ["trend_pullback", "mean_reversion", "breakout"])
    spread_bps_max: float = 4.0
    min_volume: int = 250000
    atr_min: float = 0.05
    atr_max: float = 4.0


@dataclass
class UniverseConfig:
    symbols: list[str] = field(default_factory=lambda: ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"])
    rth_only: bool = True


@dataclass
class ValidationConfig:
    train_fraction: float = 0.65
    walk_forward_windows: int = 3
    monte_carlo_runs: int = 500
    sensitivity_slippage_bps: list[float] = field(default_factory=lambda: [1.0, 2.0, 4.0])


@dataclass
class BotConfig:
    name: str = "us_equities_scalper"
    starting_equity: float = 50000.0
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    limits: LimitsConfig = field(default_factory=LimitsConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    universe: UniverseConfig = field(default_factory=UniverseConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    data_path: str = "data/sample/spy_sample.csv"
    log_dir: str = "logs"


def _build(dc_cls: Any, payload: dict[str, Any]) -> Any:
    return dc_cls(**{k: v for k, v in payload.items() if k in dc_cls.__dataclass_fields__})


def load_bot_config(path: str | Path) -> BotConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return BotConfig(
        name=raw.get("name", "us_equities_scalper"),
        starting_equity=raw.get("starting_equity", 50000.0),
        broker=_build(BrokerConfig, raw.get("broker", {})),
        limits=_build(LimitsConfig, raw.get("limits", {})),
        risk=_build(RiskConfig, raw.get("risk", {})),
        execution=_build(ExecutionConfig, raw.get("execution", {})),
        strategy=_build(StrategyConfig, raw.get("strategy", {})),
        universe=_build(UniverseConfig, raw.get("universe", {})),
        validation=_build(ValidationConfig, raw.get("validation", {})),
        data_path=raw.get("data_path", "data/sample/spy_sample.csv"),
        log_dir=raw.get("log_dir", "logs"),
    )
