"""Configuration handling for MemeSensei."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from typing import List, Optional


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _get_list(name: str, default: Optional[List[int]] = None) -> List[int]:
    value = os.getenv(name)
    if not value:
        return default or []
    return [int(v.strip()) for v in value.split(",") if v.strip()]


@dataclass(slots=True)
class CoreConfig:
    chain: str = "solana"
    dry_run: bool = True
    max_position_usd: float = 250.0
    max_open_positions: int = 3
    max_daily_loss_usd: float = 500.0
    slippage_bps: int = 50
    min_liquidity_usd: float = 10000.0
    min_vol_5m_usd: float = 5000.0
    min_vol_1h_usd: float = 20000.0
    min_pair_age_seconds: int = 3600
    rugcheck_threshold: float = 0.6
    cooldown_seconds_after_trade: int = 30
    loss_streak_cooldown: int = 300
    enable_strategy_s1: bool = True
    enable_strategy_s2: bool = True
    kill_switch: bool = False
    core_api_port: int = 8000
    birdeye_api_key: Optional[str] = None
    dex_retry_limit: int = 3
    telegram_push_chat_id: Optional[str] = None
    admin_user_ids: List[int] = field(default_factory=list)


@dataclass(slots=True)
class KeyConfig:
    keypair_path: Optional[str] = None
    keypair_passphrase_env: Optional[str] = None
    base58_secret_env: Optional[str] = None


@dataclass(slots=True)
class TelegramConfig:
    bot_token: str = ""
    admin_user_ids: List[int] = field(default_factory=list)
    default_chat_id: Optional[str] = None


def load_toml_config(path: str) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config(config_path: Optional[str] = None) -> tuple[CoreConfig, KeyConfig, TelegramConfig]:
    data = {}
    if config_path and os.path.exists(config_path):
        data = load_toml_config(config_path)

    core_data = data.get("core", {})
    key_data = data.get("keys", {})
    tel_data = data.get("telegram", {})

    core = CoreConfig(
        chain=os.getenv("CHAIN", core_data.get("chain", "solana")),
        dry_run=_get_bool("DRY_RUN", core_data.get("dry_run", True)),
        max_position_usd=_get_float("MAX_POSITION_USD", core_data.get("max_position_usd", 250.0)),
        max_open_positions=_get_int("MAX_OPEN_POSITIONS", core_data.get("max_open_positions", 3)),
        max_daily_loss_usd=_get_float("MAX_DAILY_LOSS_USD", core_data.get("max_daily_loss_usd", 500.0)),
        slippage_bps=_get_int("SLIPPAGE_BPS", core_data.get("slippage_bps", 50)),
        min_liquidity_usd=_get_float("MIN_LIQUIDITY_USD", core_data.get("min_liquidity_usd", 10000.0)),
        min_vol_5m_usd=_get_float("MIN_VOL_5M_USD", core_data.get("min_vol_5m_usd", 5000.0)),
        min_vol_1h_usd=_get_float("MIN_VOL_1H_USD", core_data.get("min_vol_1h_usd", 20000.0)),
        min_pair_age_seconds=_get_int("MIN_PAIR_AGE_SECONDS", core_data.get("min_pair_age_seconds", 3600)),
        rugcheck_threshold=_get_float("RUGCHECK_THRESHOLD", core_data.get("rugcheck_threshold", 0.6)),
        cooldown_seconds_after_trade=_get_int("COOLDOWN_SECONDS_AFTER_TRADE", core_data.get("cooldown_seconds_after_trade", 30)),
        loss_streak_cooldown=_get_int("LOSS_STREAK_COOLDOWN", core_data.get("loss_streak_cooldown", 300)),
        enable_strategy_s1=_get_bool("ENABLE_STRATEGY_S1", core_data.get("enable_strategy_s1", True)),
        enable_strategy_s2=_get_bool("ENABLE_STRATEGY_S2", core_data.get("enable_strategy_s2", True)),
        kill_switch=_get_bool("KILL_SWITCH", core_data.get("kill_switch", False)),
        core_api_port=_get_int("CORE_API_PORT", core_data.get("core_api_port", 8000)),
        birdeye_api_key=os.getenv("BIRDEYE_API_KEY", core_data.get("birdeye_api_key")),
        dex_retry_limit=_get_int("DEX_RETRY_LIMIT", core_data.get("dex_retry_limit", 3)),
        telegram_push_chat_id=os.getenv("TELEGRAM_CHAT_ID_DEFAULT", core_data.get("telegram_push_chat_id")),
        admin_user_ids=_get_list("ADMIN_TELEGRAM_USER_IDS", core_data.get("admin_user_ids", [])),
    )

    keycfg = KeyConfig(
        keypair_path=key_data.get("keypair_path"),
        keypair_passphrase_env=key_data.get("keypair_passphrase_env"),
        base58_secret_env=os.getenv("BASE58_SECRET", key_data.get("base58_secret_env")),
    )

    telecfg = TelegramConfig(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", tel_data.get("bot_token", "")),
        admin_user_ids=_get_list("ADMIN_TELEGRAM_USER_IDS", tel_data.get("admin_user_ids", [])),
        default_chat_id=os.getenv("TELEGRAM_CHAT_ID_DEFAULT", tel_data.get("default_chat_id")),
    )
    if core.admin_user_ids and not telecfg.admin_user_ids:
        telecfg.admin_user_ids = core.admin_user_ids

    return core, keycfg, telecfg

