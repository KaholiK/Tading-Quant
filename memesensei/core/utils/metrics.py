from prometheus_client import Counter, Gauge

trades_total = Counter("memesensei_trades_total", "Total trades executed", ["type"])
blocked_total = Counter("memesensei_blocked_total", "Total blocked decisions", ["reason"])
open_positions = Gauge("memesensei_open_positions", "Open position count")

__all__ = ["trades_total", "blocked_total", "open_positions"]
