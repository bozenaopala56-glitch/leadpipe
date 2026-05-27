from __future__ import annotations

import json
from datetime import date
from typing import Any
from urllib.request import Request, urlopen

from .enrich_nip import is_valid_nip, normalize_nip


def validate_vat_number(value: object) -> bool:
    text = str(value or "").strip().upper()
    if text.startswith("PL"):
        text = text[2:]
    return is_valid_nip(text)


def lookup_vat_status(nip: str, *, at_date: date | None = None) -> dict[str, Any]:
    normalized = normalize_nip(nip)
    if not normalized or not validate_vat_number(normalized):
        return {"vat_valid": False, "vat_status": "invalid"}
    query_date = (at_date or date.today()).isoformat()
    url = f"https://wl-api.mf.gov.pl/api/search/nip/{normalized}?date={query_date}"
    request = Request(url, headers={"User-Agent": "leadpipe/0.1"})
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read(300_000).decode("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"vat_valid": True, "vat_status": "unknown"}

    subject = (payload.get("result") or {}).get("subject") or {}
    status = str(subject.get("statusVat") or "unknown").lower()
    return {
        "vat_valid": True,
        "vat_status": status,
        "regon": subject.get("regon"),
        "krs": subject.get("krs"),
        "legal_name": subject.get("name"),
        "address": subject.get("workingAddress") or subject.get("residenceAddress"),
    }


def enrich_vat(nip: str | None, lookup: Any | None = None) -> dict[str, Any]:
    if not nip:
        return {"vat_valid": False, "vat_status": "missing"}
    normalized = normalize_nip(nip)
    if not normalized or not validate_vat_number(normalized):
        return {"vat_valid": False, "vat_status": "invalid"}
    result = lookup(normalized) if lookup else lookup_vat_status(normalized)
    if not isinstance(result, dict):
        return {"vat_valid": True, "vat_status": "unknown"}
    return {"vat_valid": True, **result}
