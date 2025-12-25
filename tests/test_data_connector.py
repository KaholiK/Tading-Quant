from trading_system.data.connectors import PaperDataConnector, CSVDataConnector
from trading_system.data.normalizer import normalize_bar


def test_paper_data_connector_generates():
    connector = PaperDataConnector(["SPY"], minutes=1)
    bars = list(connector.stream())
    assert len(bars) >= 1


def test_csv_connector_reads_sample():
    connector = CSVDataConnector("data/sample/spy_sample.csv", "SPY")
    bars = list(connector.stream())
    assert bars[0]["symbol"] == "SPY"
    norm = normalize_bar(bars[0])
    assert "close" in norm
