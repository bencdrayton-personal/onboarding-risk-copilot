"""Load the labelled synthetic applicant set."""
from __future__ import annotations

import json
import os

from src.schema import Applicant, CreditSignals

_DATA = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_applicants.json")


def load_applicants():
    """Yield (Applicant, CreditSignals, ground_truth) tuples."""
    with open(os.path.abspath(_DATA)) as f:
        payload = json.load(f)
    out = []
    for row in payload["applicants"]:
        app = Applicant(
            abn=row["abn"],
            legal_name=row["legal_name"],
            requested_limit_aud=row["requested_limit_aud"],
            requested_terms_days=row["requested_terms_days"],
        )
        signals = CreditSignals(**row["signals"])
        out.append((app, signals, row["ground_truth"]))
    return out
