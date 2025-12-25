import argparse
import logging
import os
import time
import yaml
from ..core.event_bus import EventBus
from ..core.engine import Engine
from ..core.events import MarketDataEvent, SignalEvent, RiskEvent, OrderEvent, FillEvent, PositionEvent
from ..core.state import StateManager
from ..data.connectors import PaperDataConnector
from ..data.normalizer import normalize_bar
from ..data.cache import DataCache
from ..strategies.ema_trend import EMATrendStrategy
from ..strategies.mean_reversion import MeanReversionStrategy
from ..strategies.breakout import BreakoutStrategy
from ..risk.risk_manager import RiskConfig, RiskManager
from ..execution.paper_broker import PaperBroker
from ..execution.order_manager import OrderManager
from ..execution.fill_tracker import FillTracker
from ..services.dashboard import attach_engine
from ..utils.logging import setup_logging


def load_config(path: str):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="paper")
    parser.add_argument("--symbols", default="SPY,QQQ")
    parser.add_argument("--timeframe", default="1m")
    parser.add_argument("--minutes", type=int, default=5)
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--db", default="data/state.db")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging(config.get("logging", {}).get("level", "INFO"), config.get("logging", {}).get("file", "logs/system.log"))

    if args.mode == "live":
        if not (os.getenv("ENABLE_LIVE_TRADING") == "true" and os.getenv("LIVE_TRADING_CONFIRMATION_TOKEN") == config.get("live_trading", {}).get("confirmation_token")):
            raise SystemExit("Live trading disabled. Set env vars to proceed.")

    bus = EventBus()
    cache = DataCache()
    state = StateManager(db_path=args.db)
    risk = RiskManager(
        RiskConfig(
            max_positions=config["risk"]["max_positions"],
            daily_loss_limit=config["risk"]["daily_loss_limit"],
            max_drawdown_pct=config["risk"]["max_drawdown_pct"],
            atr_period=config["risk"]["atr_period"],
            risk_per_trade=config["risk"]["risk_per_trade"],
        ),
        cache,
    )
    broker = PaperBroker(bus, commission_per_share=config["fees"]["commission_per_share"], slippage_bps=config["fees"]["slippage_bps"])
    order_manager = OrderManager(state)
    fill_tracker = FillTracker(state)

    ema = EMATrendStrategy(cache)
    mean_rev = MeanReversionStrategy(cache)
    breakout = BreakoutStrategy(cache)
    strategies = [ema, mean_rev, breakout]
    last_prices = {}

    def on_market(event: MarketDataEvent):
        last_prices[event.symbol] = event.data["close"]
        for strat in strategies:
            signal = strat.on_bar(event)
            bus.publish(signal)

    def on_signal(event: SignalEvent):
        if event.direction == "HOLD":
            return
        risk_event = risk.evaluate(event)
        bus.publish(risk_event)

    def on_risk(event: RiskEvent):
        if not event.approved:
            logging.info("Risk rejected: %s", event.reason)
            return
        qty = getattr(event, "quantity", 1) or 1
        order = OrderEvent(symbol=event.signal.symbol, quantity=qty, direction=event.signal.direction)
        bus.publish(order)

    def on_order(event: OrderEvent):
        order_manager.record_order(event)
        price = last_prices.get(event.symbol, 0)
        broker.place_order(event, price)

    def on_fill(event: FillEvent):
        order_manager.record_fill(event)
        fill_tracker.handle_fill(event)
        risk.register_fill(event)
        qty, avg = state.get_position(event.symbol)
        bus.publish(PositionEvent(symbol=event.symbol, quantity=qty, avg_price=avg))

    handlers = {
        "MARKET": [on_market],
        "SIGNAL": [on_signal],
        "RISK": [on_risk],
        "ORDER": [on_order],
        "FILL": [on_fill],
    }

    engine = Engine(bus, handlers, state)
    attach_engine(engine, state)
    engine.start()

    connector = PaperDataConnector(symbols=args.symbols.split(","), timeframe=args.timeframe, minutes=args.minutes)
    for bar in connector.stream():
        md = MarketDataEvent(symbol=bar["symbol"], data=normalize_bar(bar), timestamp=bar["timestamp"])
        bus.publish(md)
    engine.stop()


if __name__ == "__main__":
    main()
