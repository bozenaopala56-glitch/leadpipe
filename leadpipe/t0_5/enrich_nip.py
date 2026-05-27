from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from leadpipe.models import Lead


NIP_WEIGHTS = [6, 5, 7, 2, 3, 4, 5, 6, 7]
NIP_PATTERN = re.compile(r"(?<!\d)(?:PL\s*)?(\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})(?!\d)", re.I)


def normalize_nip(value: object) -> str | None:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits if digits else None


def is_valid_nip(value: object) -> bool:
    nip = normalize_nip(value)
    if not nip or len(nip) != 10:
        return False
    checksum = sum(int(nip[index]) * weight for index, weight in enumerate(NIP_WEIGHTS)) % 11
    return checksum != 10 and checksum == int(nip[-1])


def extract_nips(text: str) -> list[str]:
    found: list[str] = []
    for match in NIP_PATTERN.finditer(text or ""):
        nip = normalize_nip(match.group(1))
        if nip and is_valid_nip(nip) and nip not in found:
            found.append(nip)
    return found


def lookup_gus_regon(nip: str, *, base_url: str = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc/ajax") -> dict[str, Any]:
    """Best-effort public GUS lookup hook.

    The official REGON API usually requires a session key, so this function is intentionally
    conservative. It returns an empty dict when the endpoint is not configured or unavailable.
    """
    if not is_valid_nip(nip):
        return {}
    query = urlencode({"nip": nip})
    request = Request(f"{base_url}?{query}", headers={"User-Agent": "leadpipe/0.1"})
    try:
        with urlopen(request, timeout=10) as response:
            payload = response.read(200_000).decode("utf-8", errors="replace")
    except OSError:
        return {}
    return {"raw": payload} if payload else {}


def enrich_nip(lead: Lead | dict[str, Any], html_text: str = "", lookup: Any | None = None) -> dict[str, Any]:
    lead_model = lead if isinstance(lead, Lead) else Lead.model_validate(lead)
    nip = lead_model.nip if lead_model.nip and is_valid_nip(lead_model.nip) else None
    if not nip:
        candidates = extract_nips(html_text)
        nip = candidates[0] if candidates else None
    if lookup:
        lookup_result = lookup(lead_model, html_text)
        if isinstance(lookup_result, dict):
            lookup_nip = normalize_nip(lookup_result.get("nip"))
            if lookup_nip and is_valid_nip(lookup_nip):
                nip = lookup_nip
            result = {"nip": nip, "nip_valid": bool(nip and is_valid_nip(nip))}
            result.update({key: value for key, value in lookup_result.items() if key != "nip" and value is not None})
            return result
    if not nip:
        return {"nip_valid": False}

    result: dict[str, Any] = {"nip": nip, "nip_valid": True}
    lookup_result = lookup_gus_regon(nip)
    if isinstance(lookup_result, dict):
        result.update({key: value for key, value in lookup_result.items() if value is not None})
        result["nip"] = normalize_nip(result.get("nip") or nip)
    return result
