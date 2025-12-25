from trading_system.core.events import MarketDataEvent, SignalEvent, RiskEvent, OrderEvent, FillEvent, SystemEvent, PositionEvent

def test_event_types():
    assert MarketDataEvent(symbol="SPY", data={}).type == "MARKET"
    assert SignalEvent(symbol="SPY").type == "SIGNAL"
    assert RiskEvent().type == "RISK"
    assert OrderEvent(symbol="SPY").type == "ORDER"
    assert FillEvent(symbol="SPY", direction="BUY").type == "FILL"
    assert SystemEvent().type == "SYSTEM"
    assert PositionEvent(symbol="SPY").type == "POSITION"
