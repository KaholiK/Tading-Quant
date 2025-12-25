PYTHON=python
PIP=pip

install:
$(PIP) install -r requirements.txt

format:
$(PYTHON) -m black trading_system tests || true

lint:
$(PYTHON) -m pylint trading_system || true

test:
pytest -q

run-paper:
$(PYTHON) -m trading_system.cli.run --mode paper --symbols SPY,QQQ --timeframe 1m --minutes 5

run-backtest:
$(PYTHON) -m trading_system.cli.backtest --symbol SPY --start 2020-01-01 --end 2023-01-01 --timeframe 1h

