from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass
class Bar:
    timestamp: pd.Timestamp
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class DataAdapter:
    """Unified interface for backtest, paper and live sources."""

    def stream(self) -> Iterable[Bar]:
        raise NotImplementedError


class CSVDataAdapter(DataAdapter):
    def __init__(self, path: str | Path, symbols: list[str]):
        self.path = Path(path)
        self.symbols = set(symbols)

    def stream(self) -> Iterable[Bar]:
        frame = pd.read_csv(self.path)
        if "timestamp" not in frame.columns and "date" in frame.columns:
            frame = frame.rename(columns={"date": "timestamp"})
        if "symbol" not in frame.columns:
            fallback = next(iter(self.symbols))
            frame["symbol"] = fallback
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        frame = frame[frame["symbol"].isin(self.symbols)].sort_values("timestamp")
        for row in frame.itertuples(index=False):
            yield Bar(
                timestamp=row.timestamp,
                symbol=row.symbol,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
            )


class BrokerDataAdapter(DataAdapter):
    """Placeholder for Alpaca/IBKR integration while keeping identical shape."""

    def __init__(self, source_stream: Iterable[dict]):
        self.source_stream = source_stream

    def stream(self) -> Iterable[Bar]:
        for tick in self.source_stream:
            yield Bar(
                timestamp=pd.Timestamp(tick["timestamp"]),
                symbol=tick["symbol"],
                open=float(tick["open"]),
                high=float(tick["high"]),
                low=float(tick["low"]),
                close=float(tick["close"]),
                volume=float(tick["volume"]),
            )
