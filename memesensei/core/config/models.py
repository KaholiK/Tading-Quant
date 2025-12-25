from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from pydantic import BaseModel, Field, ValidationError
import tomllib


def _get_env_list(name: str) -> List[str]:
    value = os.getenv(name, "")
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class RiskLimits:
    max_position_usd: float = 200.0
    max_open_positions: int = 3
    max_daily_loss_usd: float = 500.0
    slippage_bps: int = 50
    min_liquidity_usd: float = 20000.0
    min_vol_5m_usd: float = 10000.0
    min_vol_1h_usd: float = 50000.0
    min_pair_age_seconds: int = 1800
    rugcheck_threshold: float = 0.75
    cooldown_seconds_after_trade: int = 60
    loss_streak_cooldown: int = 300


class Config(BaseModel):
    chain: str = Field(default=os.getenv("CHAIN", "solana"))
    dry_run: bool = Field(default=os.getenv("DRY_RUN", "true").lower() == "true")
    enable_strategy_s1: bool = Field(default=os.getenv("ENABLE_STRATEGY_S1", "true").lower() == "true")
    enable_strategy_s2: bool = Field(default=os.getenv("ENABLE_STRATEGY_S2", "true").lower() == "true")
    kill_switch: bool = Field(default=os.getenv("KILL_SWITCH", "false").lower() == "true")
    core_api_port: int = Field(default=int(os.getenv("CORE_API_PORT", 8000)))
    admin_telegram_ids: List[int] = Field(default_factory=lambda: [int(x) for x in _get_env_list("ADMIN_TELEGRAM_USER_IDS") if x.isdigit()])
    telegram_bot_token: str | None = Field(default=os.getenv("TELEGRAM_BOT_TOKEN"))
    telegram_chat_id_default: str | None = Field(default=os.getenv("TELEGRAM_CHAT_ID_DEFAULT"))
    encrypted_key_path: str | None = Field(default=os.getenv("ENCRYPTED_KEY_PATH"))
    key_passphrase_env: str | None = Field(default=os.getenv("KEY_PASSPHRASE_ENV"))
    base58_secret: str | None = Field(default=os.getenv("BASE58_SECRET"))

    risk_limits: RiskLimits = Field(default_factory=RiskLimits)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_toml(cls, path: str) -> "Config":
        with open(path, "rb") as f:
            data = tomllib.load(f)
        try:
            risk = data.get("risk_limits", {})
            risk_limits = RiskLimits(**risk)
            merged = {**data, "risk_limits": risk_limits}
            return cls(**merged)
        except ValidationError as exc:
            raise ValueError(f"Invalid config: {exc}") from exc


def load_config(path: str | None = None) -> Config:
    if path and os.path.exists(path):
        return Config.from_toml(path)
    return Config()
