# US Equities Scalping Bot (Production-Oriented Framework)

This repository includes a robust, **rules-compliant scalping framework** for liquid US equities/ETFs with a strong focus on:
- risk control,
- explainable rules,
- funded-account style constraints,
- backtest + walk-forward + Monte Carlo validation,
- paper-first deployment.

> **No guaranteed returns.** This is a risk-managed framework designed to reduce operational and strategy risk, not eliminate market risk.

## 1) Architecture Overview

### Core modules
- `trading_system/scalping/config.py`
  - typed config for broker, risk, execution, strategy, validation.
- `trading_system/scalping/data_adapter.py`
  - data adapter layer (`CSVDataAdapter`, `BrokerDataAdapter`) so strategy logic is portable across backtest/paper/live.
- `trading_system/scalping/strategy.py`
  - composite strategy with 3 modules:
    1. trend pullback (EMA alignment + pullback),
    2. mean reversion (z-score vs VWAP),
    3. breakout (micro-range breakout + volume confirmation),
  - regime filter:
    - spread proxy threshold,
    - ATR range,
    - minimum volume,
    - regime classification (`trending`, `choppy`, `high_volatility`) via ATR + ADX proxy + realized vol.
- `trading_system/scalping/risk.py`
  - funded-account style risk manager:
    - per-trade risk sizing,
    - max position %, max trades/day,
    - daily loss kill switch,
    - trailing drawdown kill switch,
    - consecutive-loss breaker,
    - cash-account sizing protection.
- `trading_system/scalping/execution.py`
  - marketable-limit simulation with slippage, commission, and partial fill approximation.
- `trading_system/scalping/backtest.py`
  - intraday backtest loop + exits (stop/TP/time exit),
  - walk-forward validation,
  - Monte Carlo trade-sequence shuffle,
  - slippage sensitivity analysis,
  - metrics + prop-rule breach reporting.
- `trading_system/scalping/runner.py`
  - unified run entry points: `run_backtest`, `run_paper`, `run_live`.
- `trading_system/cli/scalper.py`
  - single command interface for backtest/paper/live.

### Data flow
1. Adapter yields bars (historical/live).
2. Strategy computes signals with regime gating.
3. Risk manager approves/rejects and sizes quantity.
4. Execution adapter simulates/sends order.
5. Position manager applies exits + updates equity.
6. Reports/logs persisted (JSON outputs under `logs/`).

### Guardrails implemented
- No martingale / no grid / no doubling down.
- Kill-switches for daily loss, max drawdown, loss streak.
- Parameterized transaction costs + slippage.
- Explicitly paper-first, live mode marked guarded.
- Force-flat expected before session end (configurable `force_flat_time_et`).

---

## 2) Full Codebase Map

- `trading_system/scalping/__init__.py`
- `trading_system/scalping/config.py`
- `trading_system/scalping/data_adapter.py`
- `trading_system/scalping/indicators.py`
- `trading_system/scalping/strategy.py`
- `trading_system/scalping/risk.py`
- `trading_system/scalping/execution.py`
- `trading_system/scalping/backtest.py`
- `trading_system/scalping/runner.py`
- `trading_system/cli/scalper.py`
- `configs/scalping_conservative.yaml`
- `configs/scalping_moderate.yaml`
- tests:
  - `tests/test_scalping_risk.py`
  - `tests/test_scalping_backtest.py`

---

## 3) Example Config Profiles

- Conservative funded-account profile:
  - `configs/scalping_conservative.yaml`
- Moderate profile:
  - `configs/scalping_moderate.yaml`

Both include configurable limits:
- daily max loss,
- max drawdown,
- max position sizing,
- max trades/day,
- max consecutive losses,
- slippage cap assumptions,
- force-flat time.

---

## 4) Setup & Usage

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Single-command runs
```bash
python -m trading_system.cli.scalper backtest --config configs/scalping_conservative.yaml
python -m trading_system.cli.scalper paper --config configs/scalping_conservative.yaml
python -m trading_system.cli.scalper live --config configs/scalping_conservative.yaml
```

Outputs are saved in `logs/`:
- `backtest_report.json`
- `paper_status.json`
- `live_status.json`

---

## Validation Framework Included

Backtest run includes:
- in/out style time splits via walk-forward windows,
- Monte Carlo trade order randomization,
- slippage sensitivity sweeps.

Metrics reported:
- ending equity,
- win rate,
- avg win/loss,
- expectancy,
- profit factor,
- Sharpe,
- max drawdown,
- prop-rule breach indicator.

---

## VPS Deployment Checklist (Windows/Linux)

1. **Paper trade first for multiple sessions.**
2. Sync NTP time; verify timezone handling to ET.
3. Configure broker API keys as environment variables (never hardcode).
4. Enable webhook/email alerts for start/stop and kill-switch triggers.
5. Set process supervisor:
   - Linux: `systemd` / Docker restart policy,
   - Windows: Task Scheduler / NSSM service.
6. Cap resources and monitor latency/CPU.
7. Add daily log rotation and remote backup.
8. Add manual kill command + emergency broker flatten script.
9. Validate “no overnight” close behavior in paper.
10. Run live at reduced size first; scale only after stable behavior.

---

## Notes for Broker Integration

- Current framework ships with a backtest-ready adapter and a broker adapter interface.
- To go live with Alpaca/IBKR/TradeStation:
  - implement `BrokerDataAdapter` stream source,
  - wire order placement/cancel/replace,
  - enforce broker-side bracket + day-only TIF,
  - confirm PDT/cash settlement constraints as applicable.
