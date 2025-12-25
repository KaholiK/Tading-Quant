from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT,
    size_usd REAL,
    entry_price REAL,
    opened_at REAL
);
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT,
    side TEXT,
    size_usd REAL,
    price REAL,
    pnl REAL,
    executed_at REAL
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT,
    action TEXT,
    allowed INTEGER,
    reason TEXT,
    decided_at REAL
);
"""


@dataclass(slots=True)
class Position:
    address: str
    size_usd: float
    entry_price: float
    opened_at: float


class PortfolioStore:
    def __init__(self, path: str = "data/memesensei.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.executescript(DB_SCHEMA)
        self._conn.commit()

    def record_position(self, address: str, size_usd: float, entry_price: float) -> None:
        self._conn.execute(
            "INSERT INTO positions(address, size_usd, entry_price, opened_at) VALUES (?, ?, ?, ?)",
            (address, size_usd, entry_price, time.time()),
        )
        self._conn.commit()

    def close_position(self, address: str, exit_price: float) -> Optional[float]:
        cur = self._conn.execute("SELECT * FROM positions WHERE address=? ORDER BY opened_at DESC LIMIT 1", (address,))
        row = cur.fetchone()
        if not row:
            return None
        pnl = (exit_price - row["entry_price"]) * (row["size_usd"] / max(row["entry_price"], 1e-6))
        self._conn.execute("DELETE FROM positions WHERE id=?", (row["id"],))
        self.record_trade(address, "sell", row["size_usd"], exit_price, pnl)
        self._conn.commit()
        return pnl

    def record_trade(self, address: str, side: str, size_usd: float, price: float, pnl: float = 0.0) -> None:
        self._conn.execute(
            "INSERT INTO trades(address, side, size_usd, price, pnl, executed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (address, side, size_usd, price, pnl, time.time()),
        )
        self._conn.commit()

    def record_decision(self, address: str, action: str, allowed: bool, reason: str) -> None:
        self._conn.execute(
            "INSERT INTO decisions(address, action, allowed, reason, decided_at) VALUES (?, ?, ?, ?, ?)",
            (address, action, int(allowed), reason, time.time()),
        )
        self._conn.commit()

    def list_positions(self) -> List[Position]:
        cur = self._conn.execute("SELECT address, size_usd, entry_price, opened_at FROM positions")
        return [Position(**dict(row)) for row in cur.fetchall()]

    def list_trades(self, limit: int = 50):
        cur = self._conn.execute("SELECT address, side, size_usd, price, pnl, executed_at FROM trades ORDER BY executed_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

    def list_decisions(self, limit: int = 50):
        cur = self._conn.execute("SELECT address, action, allowed, reason, decided_at FROM decisions ORDER BY decided_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

    def pnl_summary(self) -> dict:
        cur = self._conn.execute("SELECT SUM(pnl) as total FROM trades")
        total = cur.fetchone()["total"] or 0.0
        return {"total": total, "daily": total}

