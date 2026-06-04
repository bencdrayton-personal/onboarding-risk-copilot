"""Enrichment: turn an ABN into a set of credit signals.

Two layers:

1. Public data (real): the Australian Business Register's ABN Lookup web
   service. Free, but requires a one-time GUID registration. If a GUID is
   supplied via ABN_LOOKUP_GUID, we call it live; otherwise we fall back to a
   local fixture so the repo runs offline.

2. Bureau signals (synthetic): payment defaults, court actions, ratings, etc.
   A real deployment would read these from the bureau. Here they are generated
   deterministically from the ABN so the same ABN always yields the same
   profile, and they are clearly labelled synthetic. No bureau data is scraped.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from typing import Optional

from .schema import CreditSignals, RATING_ORDER

ABN_LOOKUP_ENDPOINT = "https://abr.business.gov.au/json/AbnDetails.aspx"


def _stable_unit(abn: str, salt: str) -> float:
    """A deterministic float in [0,1) derived from the ABN and a salt."""
    h = hashlib.sha256(f"{abn}:{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def lookup_abn_public(abn: str, guid: Optional[str] = None) -> Optional[dict]:
    """Call the real ABN Lookup service if a GUID is available, else None."""
    guid = guid or os.environ.get("ABN_LOOKUP_GUID")
    if not guid:
        return None
    params = urllib.parse.urlencode({"abn": abn.replace(" ", ""), "guid": guid})
    url = f"{ABN_LOOKUP_ENDPOINT}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
        # The service wraps JSON in a callback; strip it.
        start, end = raw.find("{"), raw.rfind("}")
        return json.loads(raw[start : end + 1])
    except Exception:
        return None


def _synthetic_signals(abn: str) -> CreditSignals:
    """Generate a deterministic, clearly-synthetic credit profile from an ABN."""
    age = round(0.5 + _stable_unit(abn, "age") * 18, 1)
    gst = _stable_unit(abn, "gst") > 0.25
    completeness = round(0.4 + _stable_unit(abn, "complete") * 0.6, 2)

    rating_idx = min(int(_stable_unit(abn, "rating") * len(RATING_ORDER)),
                     len(RATING_ORDER) - 1)
    rating = RATING_ORDER[rating_idx]
    # Default probability rises with rating index, plus noise.
    pd = round(0.5 + rating_idx * 1.4 + _stable_unit(abn, "pd") * 3, 1)

    defaults = int(_stable_unit(abn, "def") * 4) if rating_idx > 4 else 0
    default_amt = defaults * int(2000 + _stable_unit(abn, "amt") * 18000)
    courts = 1 if _stable_unit(abn, "court") > 0.85 else 0
    dir_changes = 2 if _stable_unit(abn, "dir") > 0.9 else (
        1 if _stable_unit(abn, "dir2") > 0.7 else 0)
    dbt = int(_stable_unit(abn, "dbt") * 45)

    return CreditSignals(
        entity_status="Active",
        entity_type="Australian Private Company",
        abn_age_years=age,
        gst_registered=gst,
        state=["NSW", "VIC", "QLD", "WA", "SA"][int(_stable_unit(abn, "st") * 5)],
        credit_rating=rating,
        pd_12m=pd,
        payment_defaults=defaults,
        default_amount_aud=default_amt,
        court_actions=courts,
        director_changes_90d=dir_changes,
        avg_days_beyond_terms=dbt,
        data_completeness=completeness,
    )


def enrich(abn: str, guid: Optional[str] = None) -> CreditSignals:
    """Build credit signals for an ABN, using public data where available."""
    signals = _synthetic_signals(abn)

    public = lookup_abn_public(abn, guid)
    if public:
        status = public.get("AbnStatus") or signals.entity_status
        signals.entity_status = "Active" if status.lower().startswith("act") else status
        signals.entity_type = public.get("EntityTypeName") or signals.entity_type
        signals.gst_registered = bool(public.get("Gst"))
        signals.state = public.get("AddressState") or signals.state
    return signals
