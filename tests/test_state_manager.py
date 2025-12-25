from trading_system.core.state import StateManager

def test_state_manager_tables():
    state = StateManager(db_path=":memory:")
    state.insert("INSERT INTO orders(id, symbol, quantity, direction, timestamp) VALUES(?,?,?,?,?)", ("1", "SPY", 10, "BUY", "now"))
    rows = state.fetchall("SELECT * FROM orders")
    assert len(rows) == 1
