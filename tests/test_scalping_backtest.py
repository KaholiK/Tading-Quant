import pandas as pd

from trading_system.scalping.backtest import BacktestEngine
from trading_system.scalping.config import BotConfig
from trading_system.scalping.data_adapter import CSVDataAdapter


def test_backtest_runs_on_sample_data(tmp_path):
    rows = []
    ts = pd.Timestamp("2024-01-02 14:30:00+00:00")
    for i in range(80):
        rows.append(
            {
                "timestamp": ts + pd.Timedelta(minutes=i),
                "symbol": "SPY",
                "open": 100 + i * 0.02,
                "high": 100.2 + i * 0.02,
                "low": 99.8 + i * 0.02,
                "close": 100 + i * 0.02,
                "volume": 300000,
            }
        )
    f = tmp_path / "bars.csv"
    pd.DataFrame(rows).to_csv(f, index=False)

    cfg = BotConfig()
    cfg.universe.symbols = ["SPY"]
    engine = BacktestEngine(cfg, CSVDataAdapter(f, ["SPY"]))
    report = engine.run()
    assert "ending_equity" in report
