from pathlib import Path
from trading_system.backtest.simulator import run_backtest


def test_backtest_in_memory_db(tmp_path):
    target = Path("data/backtest_state.db")
    if target.exists():
        target.unlink()
    report_path = tmp_path / "report.csv"
    run_backtest("data/sample/spy_sample.csv", "SPY", str(report_path))
    assert not target.exists()


def test_backtest_report(tmp_path):
    report_path = tmp_path / "report.csv"
    report = run_backtest("data/sample/spy_sample.csv", "SPY", str(report_path))
    assert report
    assert report_path.exists()


def test_backtest_registers_fills(monkeypatch, tmp_path):
    calls = []

    def spy(self, fill):
        calls.append(fill.symbol)
        return original(self, fill)

    from trading_system.backtest import simulator

    original = simulator.RiskManager.register_fill
    monkeypatch.setattr(simulator.RiskManager, "register_fill", spy)

    report_path = tmp_path / "report.csv"
    run_backtest("data/sample/spy_sample.csv", "SPY", str(report_path))
    assert calls
