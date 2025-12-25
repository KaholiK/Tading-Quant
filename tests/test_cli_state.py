import sqlite3
import sys
from trading_system.cli.run import main

def test_cli_paper_persists_state(tmp_path):
    db_path = tmp_path / "state.db"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
risk:
  max_positions: 5
  daily_loss_limit: 10000
  max_drawdown_pct: 0.5
  atr_period: 2
  risk_per_trade: 0.05
fees:
  commission_per_share: 0.0
  slippage_bps: 0.0
live_trading:
  confirmation_token: test
logging:
  level: INFO
  file: logs/test.log
"""
    )
    sys.argv = [
        "run",
        "--mode",
        "paper",
        "--symbols",
        "SPY",
        "--minutes",
        "20",
        "--db",
        str(db_path),
        "--config",
        str(config_path),
    ]
    main()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    orders = cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    fills = cur.execute("SELECT COUNT(*) FROM fills").fetchone()[0]
    conn.close()
    assert orders > 0
    assert fills > 0
