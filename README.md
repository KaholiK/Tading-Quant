# MemeSensei

Production-grade, headless meme-coin trading stack focused on Solana with an extensible architecture for future EVM chains. It runs a 24/7 core trading loop and a Telegram controller for admin-only monitoring and overrides. **Telegram never holds signing keys.**

## Features
- Discovery via DexScreener boosts + lookups
- Safety gates using RugCheck (required) and optional Birdeye enrichment
- Strategies: momentum breakout and mean reversion scalp
- Risk controls: position caps, daily loss guard, cooldowns, slippage + liquidity gates, loss-streak pause
- Execution via Jupiter Quote/Swap with DRY_RUN paper trading and simulated P&L
- SQLite persistence for positions, trades, and decision reasons
- FastAPI control plane with Prometheus metrics
- Telegram controller (python-telegram-bot) that talks to FastAPI over HTTP
- Global kill switch flag + Telegram `/killswitch` command

## Security
- Private keys are never exposed to Telegram. Signing happens only inside the core service.
- Keys can be loaded from an encrypted keypair file unlocked by a passphrase env var, or from a `BASE58_SECRET` env var for development with a loud warning.
- Admin authentication: only `ADMIN_TELEGRAM_USER_IDS` are allowed to issue commands; all others are rejected and logged.

## Configuration
Environment variables (see `.env.example`) or `config.toml` (see `config.toml.example`):
- Core: `CHAIN`, `DRY_RUN`, `MAX_POSITION_USD`, `MAX_OPEN_POSITIONS`, `MAX_DAILY_LOSS_USD`, `SLIPPAGE_BPS`, `MIN_LIQUIDITY_USD`, `MIN_VOL_5M_USD`, `MIN_VOL_1H_USD`, `MIN_PAIR_AGE_SECONDS`, `RUGCHECK_THRESHOLD`, `COOLDOWN_SECONDS_AFTER_TRADE`, `LOSS_STREAK_COOLDOWN`, `ENABLE_STRATEGY_S1`, `ENABLE_STRATEGY_S2`, `KILL_SWITCH`, `CORE_API_PORT`
- Telegram: `TELEGRAM_BOT_TOKEN`, `ADMIN_TELEGRAM_USER_IDS`, `TELEGRAM_CHAT_ID_DEFAULT`

## Running locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn memesensei.core.api.server:create_app --factory --reload
```

Core and Telegram can also be run via Docker compose:
```bash
docker compose up --build
```

## Core API
- `GET /health` – heartbeat
- `GET /metrics` – Prometheus metrics
- `GET /status` – uptime/mode/kill switch/last decision
- `GET /positions` – open positions
- `GET /trades?limit=50` – trades
- `GET /decisions?limit=50` – decisions + blocked reasons
- `POST /control/pause|resume|killswitch|setrisk` – runtime control (setrisk whitelist enforced)

## Telegram commands
Admin-only commands mapped to the API: `/start`, `/status`, `/positions`, `/pnl`, `/recent`, `/pause`, `/resume`, `/killswitch`, `/setrisk`, `/help`. Notifications are emitted by polling the core.

## Testing
```bash
pytest
```

## Gate explanations
Every candidate pair must pass:
- Liquidity, 5m/1h volume, and pair age thresholds from DexScreener
- RugCheck risk score threshold (hard stop)
- Optional Birdeye holder concentration check
- Slippage cap and cooldowns enforced by the risk manager

If any gate fails, the trade is blocked, the reason is persisted, and it is surfaced via `/recent`.

## Disclaimer
This project is for educational purposes. Meme coins are extremely volatile; profitability is not guaranteed.
