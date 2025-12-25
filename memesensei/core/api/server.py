from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from ..service import CoreService
from ..config import load_config


class APIServer:
    def __init__(self, service: CoreService):
        self.service = service
        self.app = FastAPI(title="MemeSensei")
        self._register_routes()

    def _register_routes(self) -> None:
        app = self.app

        @app.get("/health")
        def health():
            return {"status": "ok"}

        @app.get("/metrics", response_class=PlainTextResponse)
        def metrics():
            return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

        @app.get("/status")
        def status():
            return self.service.status()

        @app.get("/positions")
        def positions():
            return [p.__dict__ for p in self.service.store.list_positions()]

        @app.get("/trades")
        def trades(limit: int = 50):
            return self.service.store.list_trades(limit=limit)

        @app.get("/decisions")
        def decisions(limit: int = 50):
            return self.service.store.list_decisions(limit=limit)

        @app.post("/control/pause")
        def pause():
            self.service.pause()
            return {"paused": True}

        @app.post("/control/resume")
        def resume():
            self.service.resume()
            return {"paused": False}

        @app.post("/control/killswitch")
        def killswitch(state: bool = True):
            self.service.toggle_kill_switch(state)
            return {"kill_switch": self.service.kill_switch}

        @app.post("/control/setrisk")
        def setrisk(key: str, value: float):
            safe_keys = {"max_position_usd", "max_daily_loss_usd", "slippage_bps", "max_open_positions"}
            if key not in safe_keys:
                raise HTTPException(status_code=400, detail="key_not_allowed")
            setattr(self.service.config, key, value)
            return {key: getattr(self.service.config, key)}


def create_app(service: CoreService | None = None) -> FastAPI:
    if service is None:
        core_cfg, _, _ = load_config()
        service = CoreService(core_cfg)
    return APIServer(service).app

