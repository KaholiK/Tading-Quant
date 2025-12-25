from typing import Dict, List

class DataCache:
    def __init__(self):
        self.cache: Dict[str, List[float]] = {}

    def add(self, symbol: str, price: float):
        self.cache.setdefault(symbol, []).append(price)

    def history(self, symbol: str, window: int = 10) -> List[float]:
        return self.cache.get(symbol, [])[-window:]
