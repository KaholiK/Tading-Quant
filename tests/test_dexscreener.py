from memesensei.core.scanners.dexscreener import DexScreenerClient


def test_parse_pairs():
    client = DexScreenerClient()
    payload = {
        "pairs": [
            {
                "pairAddress": "pair1",
                "baseToken": {"address": "token1"},
                "liquidity": {"usd": 50000},
                "txns": {"m5": {"volume": 12000}, "h1": {"volume": 52000}},
                "age": 4000,
            }
        ]
    }
    pairs = client.parse_pairs(payload)
    assert len(pairs) == 1
    assert pairs[0].liquidity_usd == 50000
    assert pairs[0].volume_5m_usd == 12000
    assert pairs[0].pair_address == "pair1"
