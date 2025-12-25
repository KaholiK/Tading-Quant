from trading_system.backtest.metrics import performance_report


def test_performance_report_fields():
    report = performance_report([0.01, -0.005, 0.02], [100000, 101000, 100500])
    assert set(report.keys()) == {"sharpe", "sortino", "calmar", "max_drawdown", "win_rate", "expectancy"}
