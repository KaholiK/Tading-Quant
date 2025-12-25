from trading_system.execution.fill_tracker import apply_fill_to_position
from trading_system.core.events import FillEvent


def make_fill(direction: str, qty: int, price: float) -> FillEvent:
    return FillEvent(symbol="SPY", quantity=qty, price=price, direction=direction, commission=0.0, order_id="1")


def test_apply_fill_long_add_reduce_flip():
    qty, avg, realized = apply_fill_to_position(10, 100.0, make_fill("BUY", 10, 110.0))
    assert qty == 20 and round(avg, 2) == 105.0 and realized == 0

    qty, avg, realized = apply_fill_to_position(10, 100.0, make_fill("SELL", 4, 110.0))
    assert qty == 6 and avg == 100.0 and round(realized, 2) == 40.0

    qty, avg, realized = apply_fill_to_position(10, 100.0, make_fill("SELL", 15, 90.0))
    assert qty == -5 and avg == 90.0 and round(realized, 2) == -100.0


def test_apply_fill_short_add_reduce_flip():
    qty, avg, realized = apply_fill_to_position(-10, 100.0, make_fill("SELL", 5, 105.0))
    assert qty == -15 and round(avg, 2) == 101.67 and realized == 0

    qty, avg, realized = apply_fill_to_position(-10, 100.0, make_fill("BUY", 4, 90.0))
    assert qty == -6 and avg == 100.0 and round(realized, 2) == 40.0

    qty, avg, realized = apply_fill_to_position(-10, 100.0, make_fill("BUY", 15, 110.0))
    assert qty == 5 and avg == 110.0 and round(realized, 2) == -100.0
