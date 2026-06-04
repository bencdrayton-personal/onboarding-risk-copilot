"""Typed data structures shared across the copilot.

Pure stdlib (dataclasses + enum) so the repo runs with no third-party
dependencies in mock mode.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Decision(str, Enum):
    APPROVE = "APPROVE"
    REFER = "REFER"
    DECLINE = "DECLINE"

    @property
    def rank(self) -> int:
        # Higher rank = more conservative. Used to take the most cautious
        # of the model's call and the policy layer's call.
        return {"APPROVE": 0, "REFER": 1, "DECLINE": 2}[self.value]


# Ordered best -> worst, mirroring a commercial credit rating band.
RATING_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "E", "F"]


@dataclass
class CreditSignals:
    """The data a credit bureau would assemble for an entity.

    `entity_status`, `abn_age_years` and `gst_registered` come from the public
    ABN Lookup (ABR) web service. The remaining fields are bureau-style risk
    signals; here they are synthetic and clearly labelled as such.
    """
    entity_status: str          # "Active" | "Deregistered" | "Cancelled"
    entity_type: str            # e.g. "Australian Private Company"
    abn_age_years: float
    gst_registered: bool
    state: str
    credit_rating: str          # one of RATING_ORDER
    pd_12m: float               # modelled probability of default in 12m (%)
    payment_defaults: int       # count of registered payment defaults
    default_amount_aud: int     # total $ of those defaults
    court_actions: int          # active court actions
    director_changes_90d: int   # directors appointed/ceased in last 90 days
    avg_days_beyond_terms: int  # how late they pay, on average
    data_completeness: float    # 0..1, how thin the file is

    def rating_index(self) -> int:
        try:
            return RATING_ORDER.index(self.credit_rating)
        except ValueError:
            return len(RATING_ORDER) - 1  # unknown rating treated as worst

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Applicant:
    abn: str
    legal_name: str
    requested_limit_aud: int
    requested_terms_days: int


@dataclass
class Reason:
    """A single driver of the recommendation, tied to an observable field."""
    field: str            # which signal this cites
    statement: str        # plain-English explanation
    direction: str        # "supports" | "against" | "neutral"


@dataclass
class Recommendation:
    decision: Decision
    confidence: float                 # 0..1
    reasons: list[Reason] = field(default_factory=list)
    source: str = "model"             # "model" | "policy" | "model+policy"


@dataclass
class Assessment:
    """The full, auditable output for one applicant."""
    applicant: Applicant
    signals: CreditSignals
    recommendation: Recommendation
    policy_flags: list[str] = field(default_factory=list)
    model_decision: Optional[str] = None   # what the model alone said
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "applicant": asdict(self.applicant),
            "signals": self.signals.to_dict(),
            "recommendation": {
                "decision": self.recommendation.decision.value,
                "confidence": round(self.recommendation.confidence, 2),
                "source": self.recommendation.source,
                "reasons": [asdict(r) for r in self.recommendation.reasons],
            },
            "policy_flags": self.policy_flags,
            "model_decision": self.model_decision,
            "notes": self.notes,
        }
