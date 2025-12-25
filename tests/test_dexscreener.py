import pytest

from memesensei.core.clients.dexscreener import DexScreenerClient, PairData


def test_parse_pair():
    client = DexScreenerClient()
    sample = {
        "pairAddress": "abc",
        "info": {"baseToken": {"symbol": "TOKEN"}, "quoteToken": {"symbol": "USDC"}, "priceUsd": "0.1"},
        "liquidity": {"usd": 12000},
        "volume": {"m5": 7000, "h1": 22000},
        "age": {"since": 4000},
    }
    parsed = client._parse_pair(sample)
    assert isinstance(parsed, PairData)
    assert parsed.address == "abc"
    assert parsed.base_token == "TOKEN"
    assert parsed.liquidity_usd == 12000
    assert parsed.volume_5m == 7000
    assert parsed.age_seconds == 4000

