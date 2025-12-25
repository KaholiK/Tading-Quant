from trading_system.cli.run import main

def test_cli_paper_runs(monkeypatch):
    import sys
    sys.argv = ["run", "--mode", "paper", "--symbols", "SPY", "--minutes", "3", "--db", "data/test_cli.db"]
    main()
