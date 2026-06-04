#!/usr/bin/env python3
"""Evaluation harness.

Measures what a product team actually cares about for an automated credit
decision, not just raw accuracy:

- Accuracy            : exact match to the analyst label.
- Unsafe-approve rate : the expensive error. Cases the model APPROVED that
                        should have been REFER or DECLINE. Target: zero.
- Auto-decision rate  : share decided without a human (APPROVE or DECLINE).
                        Higher = more efficiency, but only safe if unsafe-approve
                        stays at zero.
- Referral rate       : share sent to a human (REFER).
- Citation faithfulness: share of reasons that cite a real signal field
                        (a hallucination guardrail).

Run:  python -m evals.run_evals          (mock backend, no key)
      python -m evals.run_evals --model anthropic
"""
from __future__ import annotations

import argparse
from dataclasses import fields

from src.copilot import Copilot
from src.schema import CreditSignals
from evals.dataset import load_applicants

CLASSES = ["APPROVE", "REFER", "DECLINE"]
_VALID_FIELDS = {f.name for f in fields(CreditSignals)} | {"policy"}


def run(model: str = "mock") -> dict:
    copilot = Copilot(mode=model)
    data = load_applicants()

    confusion = {t: {p: 0 for p in CLASSES} for t in CLASSES}
    unsafe_approvals = []
    reason_total = reason_grounded = 0

    for app, signals, truth in data:
        a = copilot.assess(app, signals=signals)
        pred = a.recommendation.decision.value
        confusion[truth][pred] += 1

        # Unsafe approval: approved something that should not have been
        if pred == "APPROVE" and truth in {"REFER", "DECLINE"}:
            unsafe_approvals.append((app.legal_name, truth))

        for r in a.recommendation.reasons:
            reason_total += 1
            if r.field in _VALID_FIELDS:
                reason_grounded += 1

    n = len(data)
    correct = sum(confusion[c][c] for c in CLASSES)
    auto = sum(confusion[t][p] for t in CLASSES for p in ("APPROVE", "DECLINE"))
    referrals = sum(confusion[t]["REFER"] for t in CLASSES)

    return {
        "n": n,
        "accuracy": correct / n,
        "unsafe_approve_rate": len(unsafe_approvals) / n,
        "unsafe_cases": unsafe_approvals,
        "auto_decision_rate": auto / n,
        "referral_rate": referrals / n,
        "citation_faithfulness": (reason_grounded / reason_total) if reason_total else 0,
        "confusion": confusion,
    }


def _print(r: dict) -> None:
    print("\nOnboarding Risk Copilot — evaluation")
    print("=" * 52)
    print(f"  Applicants evaluated     : {r['n']}")
    print(f"  Accuracy (vs analyst)    : {r['accuracy']:.0%}")
    print(f"  Unsafe-approve rate      : {r['unsafe_approve_rate']:.0%}   (target 0%)")
    print(f"  Auto-decision rate       : {r['auto_decision_rate']:.0%}")
    print(f"  Referral rate            : {r['referral_rate']:.0%}")
    print(f"  Citation faithfulness    : {r['citation_faithfulness']:.0%}")
    print("\n  Confusion matrix (rows = truth, cols = predicted)")
    header = "            " + "".join(f"{c:>9}" for c in CLASSES)
    print(header)
    for t in CLASSES:
        row = "".join(f"{r['confusion'][t][p]:>9}" for p in CLASSES)
        print(f"    {t:<8}{row}")
    if r["unsafe_cases"]:
        print("\n  ⚠ Unsafe approvals:")
        for name, truth in r["unsafe_cases"]:
            print(f"    - {name} (should have been {truth})")
    else:
        print("\n  No unsafe approvals. Every clear-cut DECLINE/REFER was caught.")
    print("=" * 52)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["mock", "anthropic"], default="mock")
    args = p.parse_args()
    _print(run(args.model))
