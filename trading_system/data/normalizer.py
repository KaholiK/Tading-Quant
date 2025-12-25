from typing import Dict


def normalize_bar(bar: Dict) -> Dict:
    return {
        "timestamp": bar["timestamp"],
        "symbol": bar["symbol"],
        "open": float(bar["open"]),
        "high": float(bar["high"]),
        "low": float(bar["low"]),
        "close": float(bar["close"]),
        "volume": float(bar.get("volume", 0)),
    }
