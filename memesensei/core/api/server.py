from __future__ import annotations

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from memesensei.core.config.models import load_config
from memesensei.core.portfolio.state import PortfolioStore
from memesensei.core.service import CoreService

config = load_config()
service = CoreService(config)
app = FastAPI(title="MemeSensei Core")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    status = service.status()
    lines = [f"memesensei_kill_switch {int(status['kill_switch'])}", f"memesensei_paused {int(status['paused'])}"]
    return "\n".join(lines)


@app.get("/status")
async def status():
    return service.status()


@app.get("/positions")
async def positions():
    return [pos.__dict__ for pos in service.store.list_positions()]


@app.get("/trades")
async def trades(limit: int = 50):
    return [t.__dict__ for t in service.store.list_trades(limit)]


@app.get("/decisions")
async def decisions(limit: int = 50):
    # placeholder blocked reasons come from trades table reason
    return [t.__dict__ for t in service.store.list_trades(limit)]


@app.post("/control/pause")
async def pause():
    service.pause()
    return {"paused": True}


@app.post("/control/resume")
async def resume():
    service.resume()
    return {"paused": False}


@app.post("/control/killswitch")
async def killswitch(state: bool = True):
    service.toggle_kill(state)
    return {"kill_switch": service.kill_switch}


SAFE_KEYS = {"max_position_usd", "max_open_positions", "slippage_bps"}


@app.post("/control/setrisk")
async def setrisk(key: str, value: float):
    if key not in SAFE_KEYS:
        raise HTTPException(status_code=400, detail="key not allowed")
    setattr(service.config.risk_limits, key, value)
    return {key: value}


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(service.run())
