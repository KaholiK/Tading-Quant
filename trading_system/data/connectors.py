import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Iterable, List
import pandas as pd

logger = logging.getLogger(__name__)


class PaperDataConnector:
    def __init__(self, symbols: List[str], timeframe: str = "1m", minutes: int = 5):
        self.symbols = symbols
        self.timeframe = timeframe
        self.minutes = minutes

    def stream(self) -> Iterable[Dict]:
        now = datetime.utcnow()
        for minute in range(self.minutes):
            ts = now + timedelta(minutes=minute)
            for sym in self.symbols:
                price = 100 + random.random() * 5
                yield {
                    "timestamp": ts,
                    "symbol": sym,
                    "open": price,
                    "high": price + 0.5,
                    "low": price - 0.5,
                    "close": price + random.uniform(-0.3, 0.3),
                    "volume": random.randint(1000, 5000),
                }


class CSVDataConnector:
    def __init__(self, csv_path: str, symbol: str):
        self.df = pd.read_csv(csv_path, parse_dates=["date"])
        self.symbol = symbol

    def stream(self) -> Iterable[Dict]:
        for _, row in self.df.iterrows():
            yield {
                "timestamp": row["date"],
                "symbol": self.symbol,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }
