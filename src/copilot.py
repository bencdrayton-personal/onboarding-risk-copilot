"""Orchestrator: enrich -> reason -> guardrail -> auditable assessment."""
from __future__ import annotations

from typing import Optional

from . import policy
from .enrich import enrich
from .llm import Reasoner
from .schema import (Applicant, Assessment, CreditSignals, Decision,
                     Reason, Recommendation)


class Copilot:
    def __init__(self, mode: str = "mock", model: str = "claude-sonnet-4-6"):
        self.reasoner = Reasoner(mode=mode, model=model)

    def assess(
        self,
        applicant: Applicant,
        signals: Optional[CreditSignals] = None,
        guid: Optional[str] = None,
    ) -> Assessment:
        # 1. Enrich (unless caller supplied signals, e.g. the eval set)
        s = signals or enrich(applicant.abn, guid=guid)

        # 2. Policy pre-check: hard overrides short-circuit the model entirely
        pol = policy.evaluate(applicant, s)
        if pol.hard_decision is not None:
            rec = Recommendation(
                decision=pol.hard_decision,
                confidence=0.99,
                reasons=[Reason("policy", f, "against") for f in pol.flags],
                source="policy",
            )
            return Assessment(applicant, s, rec, policy_flags=pol.flags,
                              model_decision=None,
                              notes=["Decided by policy guardrail; model not consulted."])

        # 3. Model recommendation
        model_rec = self.reasoner.recommend(applicant, s)

        # 4. Confidence guardrail: a low-confidence APPROVE/DECLINE is unsafe
        notes: list[str] = []
        floor = pol.floor
        if model_rec.confidence < policy.MIN_CONFIDENCE_TO_AUTOMATE:
            if floor.rank < Decision.REFER.rank:
                floor = Decision.REFER
            notes.append(
                f"Model confidence {model_rec.confidence:.2f} below automation "
                f"threshold {policy.MIN_CONFIDENCE_TO_AUTOMATE:.2f}; floored to REFER."
            )

        # 5. Reconcile: take the more conservative of model vs policy floor
        final = policy.reconcile(model_rec.decision, floor)
        source = "model" if final == model_rec.decision and not pol.flags else "model+policy"

        if final != model_rec.decision:
            notes.append(
                f"Model said {model_rec.decision.value}; guardrail raised it to "
                f"{final.value} (most-conservative rule)."
            )

        final_rec = Recommendation(
            decision=final,
            confidence=model_rec.confidence,
            reasons=model_rec.reasons,
            source=source,
        )
        return Assessment(applicant, s, final_rec, policy_flags=pol.flags,
                          model_decision=model_rec.decision.value, notes=notes)
