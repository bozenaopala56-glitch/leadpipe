from __future__ import annotations

from hashlib import sha256
from typing import Any

from leadpipe.models import Lead

from .cache import EnrichmentCache
from .enrich_nip import enrich_nip
from .enrich_vat import enrich_vat


def _cache_key(lead: Lead, html_text: str) -> str:
    identity = lead.nip or lead.normalized_domain or lead.input_domain
    html_hash = sha256((html_text or "").encode("utf-8", errors="replace")).hexdigest()
    return f"t0_5:{identity}:{html_hash}"


def run_t0_5(
    lead: Lead | dict[str, Any],
    html_text: str = "",
    *,
    nip_lookup: Any | None = None,
    vat_lookup: Any | None = None,
    cache: EnrichmentCache | None = None,
) -> dict[str, Any]:
    lead_model = lead if isinstance(lead, Lead) else Lead.model_validate(lead)
    key = _cache_key(lead_model, html_text)
    cached = cache.get(key) if cache else None
    if cached:
        return cached

    nip_data = enrich_nip(lead_model, html_text, lookup=nip_lookup)
    vat_data = enrich_vat(nip_data.get("nip") or lead_model.nip, lookup=vat_lookup)
    enrichment = {**nip_data, **{key: value for key, value in vat_data.items() if value is not None}}

    lead_payload = lead_model.model_dump(mode="json")
    if enrichment.get("nip"):
        lead_payload["nip"] = enrichment["nip"]
    if not lead_payload.get("company_name") and enrichment.get("legal_name"):
        lead_payload["company_name"] = enrichment["legal_name"]

    signals = {
        "nip_present": bool(enrichment.get("nip")),
        "regon_present": bool(enrichment.get("regon")),
        "vat_active": str(enrichment.get("vat_status") or "").lower() in {"czynny", "active", "registered"},
        "company_confirmed": bool(enrichment.get("nip") or enrichment.get("regon") or enrichment.get("legal_name")),
    }
    result = {"lead": lead_payload, "enrichment": enrichment, "signals": signals}
    if cache:
        cache.set(key, result)
    return result


__all__ = ["EnrichmentCache", "run_t0_5"]
