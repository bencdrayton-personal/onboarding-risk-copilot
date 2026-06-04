"""The reasoning layer, behind one interface.

`Reasoner.recommend()` returns a structured Recommendation. Two backends:

- "mock"      : a deterministic, dependency-free heuristic. Lets the whole repo
                run and the evals reproduce with no API key. CI-friendly.
- "anthropic" : calls Claude to produce the same structured output. Used when
                ANTHROPIC_API_KEY is set (and `--model anthropic` is passed).

The contract is identical either way, so the policy layer and evals never need
to know which backend produced the recommendation. The deterministic guardrail
in policy.py wraps whichever backend is used, so safety does not depend on the
model.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from .schema import Applicant, CreditSignals, Decision, Reason, Recommendation

SYSTEM_PROMPT = """You are a commercial trade-credit onboarding assistant.
Given an applicant and bureau signals, recommend APPROVE, REFER or DECLINE for
the requested credit limit and terms.

Principles:
- The cost of a wrong APPROVE (bad debt) far exceeds the cost of a REFER (a
  human spends a few minutes). When unsure, prefer REFER.
- Every reason MUST cite a specific signal field. Never invent data.
- Weigh the requested exposure, not just the score: a large limit demands more
  caution than a small one.

Return ONLY JSON of the form:
{"decision": "APPROVE|REFER|DECLINE", "confidence": 0.0-1.0,
 "reasons": [{"field": "<signal field>", "statement": "<plain english>",
              "direction": "supports|against|neutral"}]}"""


class Reasoner:
    def __init__(self, mode: str = "mock", model: str = "claude-sonnet-4-6"):
        self.mode = mode
        self.model = model

    # ------------------------------------------------------------------ #
    def recommend(self, applicant: Applicant, s: CreditSignals) -> Recommendation:
        if self.mode == "anthropic":
            return self._recommend_anthropic(applicant, s)
        return self._recommend_mock(applicant, s)

    # ------------------------------------------------------------------ #
    def _recommend_mock(self, applicant: Applicant, s: CreditSignals) -> Recommendation:
        """Heuristic stand-in for a model. Deterministic and explainable."""
        reasons: list[Reason] = []
        risk = 0.0

        # Rating
        idx = s.rating_index()
        if idx <= 1:
            reasons.append(Reason("credit_rating",
                f"Strong credit rating {s.credit_rating}.", "supports"))
        elif idx >= 6:
            risk += 2
            reasons.append(Reason("credit_rating",
                f"Weak credit rating {s.credit_rating}.", "against"))
        risk += idx * 0.3

        # Default probability
        risk += s.pd_12m * 0.15
        if s.pd_12m >= 5:
            reasons.append(Reason("pd_12m",
                f"Elevated 12-month default probability {s.pd_12m:.1f}%.", "against"))
        elif s.pd_12m <= 2:
            reasons.append(Reason("pd_12m",
                f"Low default probability {s.pd_12m:.1f}%.", "supports"))

        # Payment defaults
        if s.payment_defaults:
            risk += 1.5 + s.payment_defaults * 0.5
            reasons.append(Reason("payment_defaults",
                f"{s.payment_defaults} payment default(s) totalling "
                f"${s.default_amount_aud:,}.", "against"))

        # Court actions / director changes
        if s.court_actions:
            risk += 2
            reasons.append(Reason("court_actions",
                f"{s.court_actions} active court action(s).", "against"))
        if s.director_changes_90d >= 2:
            risk += 1.5
            reasons.append(Reason("director_changes_90d",
                f"{s.director_changes_90d} director changes in 90 days.", "against"))

        # Tenure & registration
        if s.abn_age_years >= 5 and s.entity_status == "Active":
            reasons.append(Reason("abn_age_years",
                f"Established entity, {s.abn_age_years:.0f} years on the ABR.",
                "supports"))
        elif s.abn_age_years < 2:
            risk += 1
            reasons.append(Reason("abn_age_years",
                f"Young entity, only {s.abn_age_years:.1f} years registered.",
                "against"))
        if not s.gst_registered:
            risk += 0.5
            reasons.append(Reason("gst_registered",
                "Not registered for GST; turnover may be limited.", "neutral"))

        # Late payment behaviour
        if s.avg_days_beyond_terms >= 20:
            risk += 1
            reasons.append(Reason("avg_days_beyond_terms",
                f"Pays {s.avg_days_beyond_terms} days beyond terms on average.",
                "against"))

        # Exposure scaling
        exposure_factor = applicant.requested_limit_aud / 25_000
        risk *= (0.8 + 0.2 * min(exposure_factor, 3))

        # Map risk score to decision
        if risk <= 1.2:
            decision = Decision.APPROVE
        elif risk >= 4.0:
            decision = Decision.DECLINE
        else:
            decision = Decision.REFER

        # Confidence: high when far from the decision boundaries
        if decision == Decision.APPROVE:
            confidence = max(0.5, min(0.97, 1 - risk / 1.2 * 0.4))
        elif decision == Decision.DECLINE:
            confidence = max(0.5, min(0.97, (risk - 2) / 4))
        else:
            confidence = 0.55  # REFER is inherently the "unsure" bucket

        if not reasons:
            reasons.append(Reason("credit_rating",
                f"Profile {s.credit_rating}, default prob {s.pd_12m:.1f}%.",
                "neutral"))

        return Recommendation(decision=decision, confidence=round(confidence, 2),
                              reasons=reasons[:5], source="model")

    # ------------------------------------------------------------------ #
    def _recommend_anthropic(self, applicant: Applicant, s: CreditSignals) -> Recommendation:
        try:
            import anthropic  # lazy import; only needed in live mode
        except ImportError as e:
            raise RuntimeError(
                "anthropic package not installed. `pip install anthropic` or "
                "run with --model mock."
            ) from e

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        payload = {
            "applicant": {
                "legal_name": applicant.legal_name,
                "requested_limit_aud": applicant.requested_limit_aud,
                "requested_terms_days": applicant.requested_terms_days,
            },
            "signals": s.to_dict(),
        }
        msg = client.messages.create(
            model=self.model,
            max_tokens=900,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start : end + 1])
        reasons = [Reason(**r) for r in data.get("reasons", [])]
        return Recommendation(
            decision=Decision(data["decision"]),
            confidence=float(data["confidence"]),
            reasons=reasons,
            source="model",
        )
