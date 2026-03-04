from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .backtest import BacktestEngine, monte_carlo_trade_shuffle, walk_forward_validate
from .config import load_bot_config
from .data_adapter import CSVDataAdapter


def _ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_backtest(config_path: str) -> dict:
    cfg = load_bot_config(config_path)
    adapter = CSVDataAdapter(cfg.data_path, cfg.universe.symbols)
    engine = BacktestEngine(cfg, adapter)
    report = engine.run()

    frame = pd.read_csv(cfg.data_path)
    wf = walk_forward_validate(cfg, frame)
    mc = monte_carlo_trade_shuffle(engine.trades, runs=cfg.validation.monte_carlo_runs)
    slippage_sensitivity = {}
    for s in cfg.validation.sensitivity_slippage_bps:
        cfg.execution.slippage_bps = s
        slippage_sensitivity[f"slippage_{s}"] = BacktestEngine(cfg, adapter).run().get("ending_equity", cfg.starting_equity)

    full = {"backtest": report, "walk_forward": wf, "monte_carlo": mc, "sensitivity": slippage_sensitivity}
    out = _ensure_dir(cfg.log_dir) / "backtest_report.json"
    out.write_text(json.dumps(full, indent=2), encoding="utf-8")
    return full


def run_paper(config_path: str) -> dict:
    cfg = load_bot_config(config_path)
    msg = {
        "mode": "paper",
        "status": "ready",
        "note": "Paper runner uses same strategy+risk stack via broker adapter. Integrate streaming adapter and call BacktestEngine-like event loop.",
    }
    out = _ensure_dir(cfg.log_dir) / "paper_status.json"
    out.write_text(json.dumps(msg, indent=2), encoding="utf-8")
    return msg


def run_live(config_path: str) -> dict:
    cfg = load_bot_config(config_path)
    msg = {
        "mode": "live",
        "status": "guarded",
        "note": "Live mode requires explicit broker keys, kill-switch webhook, and dry-run checklist completion.",
    }
    out = _ensure_dir(cfg.log_dir) / "live_status.json"
    out.write_text(json.dumps(msg, indent=2), encoding="utf-8")
    return msg
