# MemeSensei

Autonomous meme-coin trading skeleton with Solana-first architecture and Telegram controls. The project is designed for headless VPS operation with clear separation between signing keys (core service only) and Telegram control.

## Features
- Core FastAPI service exposing health, metrics, status, portfolio, trades, decisions, and control endpoints.
- DexScreener discovery parsing, RugCheck safety gate, strategy plug-ins, and risk limits.
- Paper-trading/dry-run support with simulated PnL tracking.
- Kill switch exposed via environment variable and `/killswitch` Telegram command.
- SQLite persistence for positions and trades.
- Telegram controller calling the core API with admin-only command handling.
- Docker images for the core and Telegram controller plus docker-compose for local orchestration.

## Security
- Telegram never sees signing keys; only the core service may load keys.
- Secrets are either loaded from an encrypted key file (preferred) or from a development-only `BASE58_SECRET` env var which emits a warning banner.
- Admin-only Telegram commands; unauthorized attempts are logged.

## Configuration
Configuration can be supplied via environment variables or `config.toml`.

Important env vars (see `.env.example`):
- `DRY_RUN` toggles paper mode.
- `KILL_SWITCH` disables new trades globally.
- `ADMIN_TELEGRAM_USER_IDS` comma-separated list for command authorization.
- `ENCRYPTED_KEY_PATH` + `KEY_PASSPHRASE_ENV` for loading private keys securely.
- `BASE58_SECRET` only for local development.

`config.toml.example` shows risk limit defaults and API port selection.

## Running locally
```bash
make install   # pip install -r requirements.txt
make run-core  # uvicorn memesensei.core.api.server:app --reload
```

## Docker
Build and start the services:
```bash
docker compose up --build
```
Services:
- `core`: FastAPI service with trading loop
- `telegram`: lightweight controller polling the core API
- `prometheus`: optional metrics scraping

## Tests
Run all tests with:
```bash
pytest -q
```

## Safety & Gates
Every candidate trade must pass:
- DexScreener liquidity/volume/age thresholds.
- RugCheck risk/trust thresholds.
- Risk manager limits: position size, max open positions, daily loss, cooldowns, slippage caps.
- Strategy signal must indicate `buy`; otherwise no trade.

Blocked reasons are recorded in trades and surfaced through Telegram `/recent` and the `/decisions` API.

## Disclaimers
Meme coins are extremely volatile and risky. Profitability is **not** guaranteed. Use DRY_RUN first and never expose private keys to Telegram or untrusted systems.
