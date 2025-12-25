from fastapi import FastAPI
from ..core.engine import Engine
from ..core.state import StateManager

app = FastAPI(title="AMATS Dashboard")
engine_ref: Engine | None = None
state_ref: StateManager | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    return {"running": bool(engine_ref and engine_ref.running), "paused": bool(engine_ref and engine_ref.paused)}


@app.get("/positions")
def positions():
    if not state_ref:
        return []
    return state_ref.fetchall("SELECT symbol, quantity, avg_price FROM positions")


@app.get("/orders")
def orders():
    if not state_ref:
        return []
    return state_ref.fetchall("SELECT id, symbol, quantity, direction, timestamp FROM orders")


@app.get("/trades")
def trades():
    if not state_ref:
        return []
    return state_ref.fetchall("SELECT id, symbol, pnl, timestamp FROM trades")


@app.get("/metrics")
def metrics():
    return {"message": "metrics unavailable in stub"}


@app.post("/kill-switch")
def kill_switch():
    if engine_ref:
        engine_ref.engage_kill_switch("api request")
    return {"kill": True}


@app.post("/pause")
def pause():
    if engine_ref:
        engine_ref.pause()
    return {"paused": True}


@app.post("/resume")
def resume():
    if engine_ref:
        engine_ref.resume()
    return {"resumed": True}


def attach_engine(engine: Engine, state: StateManager):
    global engine_ref, state_ref
    engine_ref = engine
    state_ref = state
