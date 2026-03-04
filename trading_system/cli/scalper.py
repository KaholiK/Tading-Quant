from __future__ import annotations

import argparse
import json

from trading_system.scalping.runner import run_backtest, run_live, run_paper


def main() -> None:
    parser = argparse.ArgumentParser(description="US equities scalping bot")
    parser.add_argument("command", choices=["backtest", "paper", "live"])
    parser.add_argument("--config", default="configs/scalping_conservative.yaml")
    args = parser.parse_args()

    if args.command == "backtest":
        result = run_backtest(args.config)
    elif args.command == "paper":
        result = run_paper(args.config)
    else:
        result = run_live(args.config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
