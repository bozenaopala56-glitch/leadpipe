from __future__ import annotations

from typing import Any

from .contact import extract_contacts
from .cta import analyze_ctas
from .forms import analyze_forms
from .industry import classify_industry
from .jsonld import extract_jsonld


def _append_unique(values: list[str], candidate: object) -> None:
    text = str(candidate or "").strip()
    if text and text not in values:
        values.append(text)


def run_t1(html_text: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    jsonld = extract_jsonld(html_text)
    contacts = extract_contacts(html_text)
    organization = jsonld.get("organization") or {}
    if isinstance(organization, dict):
        _append_unique(contacts["emails"], str(organization.get("email") or "").lower())
        _append_unique(contacts["phones"], organization.get("telephone"))
        contacts["contactability"] = min(
            100,
            (45 if contacts["emails"] else 0) + (35 if contacts["phones"] else 0) + (20 if contacts["social"] else 0),
        )
    forms = analyze_forms(html_text)
    ctas = analyze_ctas(html_text)
    industry = classify_industry(html_text)
    evidence_count = sum(
        [
            bool(jsonld["items"]),
            bool(contacts["emails"] or contacts["phones"]),
            forms["form_present"],
            not ctas["cta_missing"],
            industry["industry"] != "unknown",
        ]
    )
    t1_confidence = min(1.0, 0.3 + evidence_count * 0.14)
    signals = {
        "has_email": bool(contacts["emails"]),
        "has_phone": bool(contacts["phones"]),
        "contactability": contacts["contactability"],
        "form_present": forms["form_present"],
        "form_missing": forms["form_missing"],
        "cta_missing": ctas["cta_missing"],
        "weak_cta": ctas["weak_cta"],
        "industry_fit": industry["industry_fit"],
        "lead_value": industry["lead_value"],
        "competitor": industry["competitor"],
        "competitor_confidence": industry["competitor_confidence"],
        "t1_confidence": t1_confidence,
        "campaign_confidence": t1_confidence,
    }
    return {
        "headers": headers or {},
        "jsonld": jsonld,
        "contacts": contacts,
        "forms": forms,
        "ctas": ctas,
        "industry": industry,
        "signals": signals,
    }


__all__ = ["run_t1"]
