"""Deterministic guardrail layer.

This is the heart of the product argument: the model assists, but it never has
the final say on a risky case. A rules layer runs *around* the model and always
takes the most conservative path.

Two errors are not equal. A wrong auto-APPROVE becomes bad debt (thousands of
dollars). A wrong REFER costs a few minutes of a human's time. So the policy is
deliberately asymmetric: it lets clear-cut cases through and escalates anything
ambiguous or high-exposure to a human.

All thresholds live here, in one place, so they can be tuned and governed
without touching model logic.
"""
from __future__ import annotations

from dataclasses import dataclass

from .schema import Applicant, CreditSignals, Decision

# --- Tunable policy thresholds (a product/risk decision, not a model one) ---
AUTO_DECISION_CAP_AUD = 50_000     # above this exposure, never auto-decide
PD_DECLINE_PCT = 12.0              # modelled default prob that forces decline
PD_REFER_PCT = 5.0                # default prob that forces human review
WORST_AUTO_APPROVE_RATING = "B2"  # ratings worse than this cannot auto-approve
MIN_CONFIDENCE_TO_AUTOMATE = 0.70  # model below this -> human review
THIN_FILE_THRESHOLD = 0.55        # data completeness below this -> human review

_RATING_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "E", "F"]


@dataclass
class PolicyResult:
    hard_decision: Decision | None   # set only when policy alone decides
    floor: Decision                  # most lenient decision policy will allow
    flags: list[str]


def _rating_idx(r: str) -> int:
    return _RATING_ORDER.index(r) if r in _RATING_ORDER else len(_RATING_ORDER) - 1


def evaluate(applicant: Applicant, s: CreditSignals) -> PolicyResult:
    """Return policy constraints for this applicant.

    - hard_decision: a non-negotiable outcome (e.g. deregistered entity).
    - floor: the most lenient outcome policy permits; the final decision is the
      more conservative of (model decision, floor).
    """
    flags: list[str] = []

    # --- Hard declines: nothing the model says can override these ---
    if s.entity_status.lower() in {"deregistered", "cancelled"}:
        return PolicyResult(
            hard_decision=Decision.DECLINE,
            floor=Decision.DECLINE,
            flags=[f"Entity status is {s.entity_status}; cannot extend credit."],
        )

    if s.pd_12m >= PD_DECLINE_PCT:
        flags.append(
            f"Modelled 12-month default probability {s.pd_12m:.1f}% "
            f"exceeds decline threshold {PD_DECLINE_PCT:.0f}%."
        )
        return PolicyResult(
            hard_decision=Decision.DECLINE, floor=Decision.DECLINE, flags=flags
        )

    # --- Forced human review (REFER floor): clear-cut automation is unsafe ---
    floor = Decision.APPROVE

    if applicant.requested_limit_aud > AUTO_DECISION_CAP_AUD:
        floor = Decision.REFER
        flags.append(
            f"Requested limit ${applicant.requested_limit_aud:,} exceeds the "
            f"${AUTO_DECISION_CAP_AUD:,} auto-decision cap; exposure too large "
            f"to approve without a human."
        )

    if s.director_changes_90d >= 2:
        floor = Decision.REFER
        flags.append(
            f"{s.director_changes_90d} director changes in 90 days. Businesses "
            f"losing 2+ directors in 12 months are materially more likely to "
            f"become insolvent; escalate to a human."
        )

    if s.court_actions >= 1:
        floor = Decision.REFER
        flags.append(
            f"{s.court_actions} active court action(s) on file; requires human "
            f"judgement on materiality."
        )

    if s.pd_12m >= PD_REFER_PCT:
        floor = Decision.REFER
        flags.append(
            f"Modelled default probability {s.pd_12m:.1f}% is elevated "
            f"(>= {PD_REFER_PCT:.0f}%); escalate."
        )

    if _rating_idx(s.credit_rating) > _rating_idx(WORST_AUTO_APPROVE_RATING):
        floor = Decision.REFER
        flags.append(
            f"Credit rating {s.credit_rating} is below the auto-approve floor "
            f"of {WORST_AUTO_APPROVE_RATING}."
        )

    if s.data_completeness < THIN_FILE_THRESHOLD:
        floor = Decision.REFER
        flags.append(
            f"Thin file (data completeness {s.data_completeness:.0%}); not "
            f"enough evidence to automate."
        )

    return PolicyResult(hard_decision=None, floor=floor, flags=flags)


def reconcile(model_decision: Decision, floor: Decision) -> Decision:
    """Final decision is the more conservative of the model and the policy floor."""
    return model_decision if model_decision.rank >= floor.rank else floor
