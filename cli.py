#!/usr/bin/env python3
"""Command-line entry point for the Onboarding Risk Copilot.

Examples:
    python cli.py --demo
    python cli.py --abn 51824753556 --name "Acme Pty Ltd" --limit 20000 --terms 30
    python cli.py --demo --model anthropic      # uses Claude if ANTHROPIC_API_KEY set
    python cli.py --abn 51824753556 --limit 20000 --json
"""
from __future__ import annotations

import argparse
import json
import sys

from src.copilot import Copilot
from src.schema import Applicant, CreditSignals

BADGE = {"APPROVE": "[ APPROVE ]", "REFER": "[ REFER  ]", "DECLINE": "[ DECLINE ]"}


def _print_assessment(a) -> None:
    d = a.to_dict()
    rec = d["recommendation"]
    app = d["applicant"]
    print("=" * 68)
    print(f"{app['legal_name']}   (ABN {app['abn']})")
    print(f"Requested: ${app['requested_limit_aud']:,} on "
          f"{app['requested_terms_days']}-day terms")
    print("-" * 68)
    print(f"  {BADGE.get(rec['decision'], rec['decision'])}   "
          f"confidence {rec['confidence']:.2f}   "
          f"(decided by: {rec['source']})")
    if d["model_decision"] and d["model_decision"] != rec["decision"]:
        print(f"  model alone said: {d['model_decision']}  ->  raised by guardrail")
    print("  Why:")
    for r in rec["reasons"]:
        mark = {"supports": "+", "against": "-", "neutral": "·"}.get(r["direction"], "·")
        print(f"    {mark} {r['statement']}  ({r['field']})")
    if d["policy_flags"]:
        print("  Guardrail flags:")
        for f in d["policy_flags"]:
            print(f"    ! {f}")
    if d["notes"]:
        for n in d["notes"]:
            print(f"  note: {n}")
    print("=" * 68)


def _demo(copilot: Copilot, as_json: bool) -> None:
    from evals.dataset import load_applicants
    results = []
    for app, signals, _truth in load_applicants():
        a = copilot.assess(app, signals=signals)
        results.append(a)
    if as_json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for a in results:
            _print_assessment(a)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Onboarding Risk Copilot")
    p.add_argument("--abn", help="ABN to assess")
    p.add_argument("--name", default="Applicant Pty Ltd", help="Legal name")
    p.add_argument("--limit", type=int, default=20_000, help="Requested credit limit (AUD)")
    p.add_argument("--terms", type=int, default=30, help="Requested terms (days)")
    p.add_argument("--demo", action="store_true", help="Run the bundled sample applicants")
    p.add_argument("--model", choices=["mock", "anthropic"], default="mock")
    p.add_argument("--json", action="store_true", help="Emit JSON")
    args = p.parse_args(argv)

    copilot = Copilot(mode=args.model)

    try:
        if args.demo:
            _demo(copilot, args.json)
            return 0

        if not args.abn:
            p.error("provide --abn ... or --demo")

        app = Applicant(abn=args.abn, legal_name=args.name,
                        requested_limit_aud=args.limit, requested_terms_days=args.terms)
        a = copilot.assess(app)
        if args.json:
            print(json.dumps(a.to_dict(), indent=2))
        else:
            _print_assessment(a)
        return 0
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
