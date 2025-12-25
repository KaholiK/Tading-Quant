import argparse
import logging
from pathlib import Path
import yaml
from ..backtest.simulator import run_backtest
from ..utils.logging import setup_logging


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()

    config = yaml.safe_load(open(args.config))
    setup_logging()
    csv_path = config.get("backtest", {}).get("sample_data", "data/sample/spy_sample.csv")
    report_path = Path("data/reports") / f"{args.symbol}_report.csv"
    report = run_backtest(csv_path, args.symbol, str(report_path))
    print("Performance report", report)


if __name__ == "__main__":
    main()
