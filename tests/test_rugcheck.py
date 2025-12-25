from memesensei.core.safety.rugcheck import RugCheckGate, RugCheckReport


def test_rugcheck_blocks_high_risk():
    gate = RugCheckGate(threshold=0.5)
    report = RugCheckReport(address="token", risk_score=0.8, trust_score=0.2)
    allowed, reason = gate.evaluate(report)
    assert not allowed
    assert "exceeds" in reason


def test_rugcheck_allows_safe():
    gate = RugCheckGate(threshold=0.5)
    report = RugCheckReport(address="token", risk_score=0.3, trust_score=0.8)
    allowed, reason = gate.evaluate(report)
    assert allowed
    assert reason is None
