import logging
from pathlib import Path
from typing import Dict, List
import pandas as pd
from ..core.events import MarketDataEvent, OrderEvent, FillEvent
from ..data.connectors import CSVDataConnector
from ..data.normalizer import normalize_bar
from ..data.cache import DataCache
from ..strategies.ema_trend import EMATrendStrategy
from ..risk.risk_manager import RiskManager, RiskConfig
from ..execution.paper_broker import PaperBroker
from ..execution.order_manager import OrderManager
from ..execution.fill_tracker import apply_fill_to_position
from .metrics import performance_report
from ..core.state import StateManager

logger = logging.getLogger(__name__)


def run_backtest(
    csv_path: str,
    symbol: str,
    report_path: str,
    initial_equity: float = 100000.0,
    db_path: str = ":memory:",
) -> Dict:
    cache = DataCache()
    strategy = EMATrendStrategy(cache)
    risk = RiskManager(
        RiskConfig(max_positions=5, daily_loss_limit=1000, max_drawdown_pct=0.2, atr_period=14, risk_per_trade=0.01), cache
    )
    state = StateManager(db_path=db_path)
    broker = PaperBroker(bus=None)
    order_manager = OrderManager(state)

    positions: Dict[str, Dict[str, float]] = {}
    prices: Dict[str, float] = {}
    cash = initial_equity
    equity_curve: List[float] = [initial_equity]
    returns: List[float] = []

    connector = CSVDataConnector(csv_path, symbol)
    for bar in connector.stream():
        prices[bar["symbol"]] = bar["close"]
        md = MarketDataEvent(symbol=bar["symbol"], data=normalize_bar(bar), timestamp=bar["timestamp"])
        signal = strategy.on_bar(md)
        if signal.direction == "HOLD":
            market_value = sum(p["qty"] * prices.get(sym, 0.0) for sym, p in positions.items())
            equity = cash + market_value
            prev_equity = equity_curve[-1]
            returns.append((equity - prev_equity) / prev_equity if prev_equity else 0.0)
            equity_curve.append(equity)
            continue
        risk_event = risk.evaluate(signal)
        if risk_event.approved:
            qty = getattr(risk_event, "quantity", 0) or 1
            order = OrderEvent(symbol=signal.symbol, quantity=qty, direction=signal.direction)
            order_manager.record_order(order)
            last_price = bar["close"]
            fill = broker.simulate_fill(order, last_price)
            order_manager.record_fill(fill)
            risk.register_fill(fill)
            pos = positions.get(fill.symbol, {"qty": 0, "avg_price": 0.0, "realized": 0.0})
            new_qty, new_avg, realized = apply_fill_to_position(int(pos["qty"]), float(pos["avg_price"]), fill)
            positions[fill.symbol] = {
                "qty": new_qty,
                "avg_price": new_avg,
                "realized": pos["realized"] + realized - fill.commission,
            }
            cash += (-fill.price * fill.quantity - fill.commission) if fill.direction == "BUY" else (fill.price * fill.quantity - fill.commission)
            state.upsert_position(fill.symbol, new_qty, new_avg)
            if realized != 0:
                state.insert(
                    "INSERT INTO trades(symbol, pnl, timestamp) VALUES(?,?,?)",
                    (fill.symbol, realized - fill.commission, str(fill.timestamp)),
                )
        market_value = sum(p["qty"] * prices.get(sym, 0.0) for sym, p in positions.items())
        equity = cash + market_value
        prev_equity = equity_curve[-1]
        returns.append((equity - prev_equity) / prev_equity if prev_equity else 0.0)
        equity_curve.append(equity)

    report = performance_report(returns, equity_curve[1:])
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    pd.Series(report).to_csv(report_path)
    logger.info("Backtest report saved to %s", report_path)
    return report
