import os
import pytest
from trading_system.cli.run import main


def test_live_guard_blocks(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_TRADING", "false")
    with pytest.raises(SystemExit):
        import sys
        sys.argv = ["run", "--mode", "live"]
        main()
