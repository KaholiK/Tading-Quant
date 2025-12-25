import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


SCHEMA = {
    "orders": """CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, symbol TEXT, quantity INTEGER, direction TEXT, timestamp TEXT);""",
    "fills": """CREATE TABLE IF NOT EXISTS fills(id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, symbol TEXT, quantity INTEGER, price REAL, commission REAL, timestamp TEXT);""",
    "positions": """CREATE TABLE IF NOT EXISTS positions(symbol TEXT PRIMARY KEY, quantity INTEGER, avg_price REAL);""",
    "trades": """CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, pnl REAL, timestamp TEXT);""",
}


class StateManager:
    def __init__(self, db_path: str = "data/state.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        for ddl in SCHEMA.values():
            cur.execute(ddl)
        self.conn.commit()

    def insert(self, query: str, params: Tuple[Any, ...]):
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()

    def fetchall(self, query: str, params: Tuple[Any, ...] = ()) -> Iterable[Tuple[Any, ...]]:
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def get_position(self, symbol: str) -> Tuple[int, float]:
        rows = self.fetchall("SELECT quantity, avg_price FROM positions WHERE symbol=?", (symbol,))
        if not rows:
            return 0, 0.0
        qty, avg = rows[0]
        return int(qty), float(avg)

    def upsert_position(self, symbol: str, quantity: int, avg_price: float):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO positions(symbol, quantity, avg_price) VALUES(?,?,?)"
            " ON CONFLICT(symbol) DO UPDATE SET quantity=excluded.quantity, avg_price=excluded.avg_price",
            (symbol, quantity, avg_price),
        )
        self.conn.commit()
