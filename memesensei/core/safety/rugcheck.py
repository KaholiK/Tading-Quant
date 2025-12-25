from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RugCheckReport:
    address: str
    risk_score: float
    trust_score: float


class RugCheckGate:
    def __init__(self, threshold: float):
        self.threshold = threshold

    def evaluate(self, report: RugCheckReport) -> tuple[bool, Optional[str]]:
        if report.risk_score > self.threshold:
            return False, f"RugCheck risk {report.risk_score} exceeds threshold {self.threshold}"
        if report.trust_score < 1 - self.threshold:
            return False, f"RugCheck trust {report.trust_score} below {(1 - self.threshold)}"
        return True, None
