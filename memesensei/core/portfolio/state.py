from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

DB_PATH = Path("data/portfolio.db")
DB_PATH.parent.mkdir(exist_ok=True)


@dataclass
class Position:
    token: str
    size: float
    entry_price: float
    timestamp: float


@dataclass
class Trade:
    token: str
    side: str
    size: float
    price: float
    pnl: float
    timestamp: float
    reason: str


class PortfolioStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS positions(
                token TEXT PRIMARY KEY,
                size REAL,
                entry_price REAL,
                timestamp REAL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS trades(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT,
                side TEXT,
                size REAL,
                price REAL,
                pnl REAL,
                timestamp REAL,
                reason TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def upsert_position(self, position: Position) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO positions(token, size, entry_price, timestamp) VALUES (?, ?, ?, ?)",
            (position.token, position.size, position.entry_price, position.timestamp),
        )
        conn.commit()
        conn.close()

    def remove_position(self, token: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM positions WHERE token = ?", (token,))
        conn.commit()
        conn.close()

    def record_trade(self, trade: Trade) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO trades(token, side, size, price, pnl, timestamp, reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trade.token, trade.side, trade.size, trade.price, trade.pnl, trade.timestamp, trade.reason),
        )
        conn.commit()
        conn.close()

    def list_positions(self) -> List[Position]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        rows = cur.execute("SELECT token, size, entry_price, timestamp FROM positions").fetchall()
        conn.close()
        return [Position(*row) for row in rows]

    def list_trades(self, limit: int = 50) -> List[Trade]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT token, side, size, price, pnl, timestamp, reason FROM trades ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [Trade(*row) for row in rows]

    def realized_pnl(self) -> float:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        value = cur.execute("SELECT SUM(pnl) FROM trades").fetchone()[0]
        conn.close()
        return float(value or 0.0)
