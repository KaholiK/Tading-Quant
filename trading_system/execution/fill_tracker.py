from typing import Tuple
from ..core.events import FillEvent
from ..core.state import StateManager


def apply_fill_to_position(qty: int, avg_price: float, fill: FillEvent) -> Tuple[int, float, float]:
    """Update position based on a fill and return (new_qty, new_avg_price, realized_pnl)."""
    side = 1 if fill.direction == "BUY" else -1
    fill_qty = fill.quantity * side
    new_qty = qty + fill_qty
    realized = 0.0

    if qty == 0:
        new_avg = fill.price
    elif qty * fill_qty > 0:
        # Adding to existing position (same direction)
        new_avg = ((abs(qty) * avg_price) + (abs(fill_qty) * fill.price)) / abs(new_qty)
    else:
        closing = min(abs(qty), abs(fill_qty))
        if qty > 0:
            realized += closing * (fill.price - avg_price)
        else:
            realized += closing * (avg_price - fill.price)

        if new_qty == 0:
            new_avg = 0.0
        elif new_qty * qty < 0:
            # flipped direction
            new_avg = fill.price
        else:
            new_avg = avg_price
    return int(new_qty), float(new_avg), float(realized)


class FillTracker:
    def __init__(self, state: StateManager):
        self.state = state

    def handle_fill(self, fill: FillEvent):
        qty, avg_price = self.state.get_position(fill.symbol)
        new_qty, new_avg, realized = apply_fill_to_position(qty, avg_price, fill)
        self.state.upsert_position(fill.symbol, new_qty, new_avg)
        realized_net = realized - fill.commission
        if realized_net != 0:
            self.state.insert(
                "INSERT INTO trades(symbol, pnl, timestamp) VALUES(?,?,?)",
                (fill.symbol, realized_net, str(fill.timestamp)),
            )
