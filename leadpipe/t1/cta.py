from __future__ import annotations

from typing import Any

from ._html import soup_from_html


CTA_KEYWORDS = {
    "kontakt",
    "contact",
    "napisz",
    "wyslij",
    "wyślij",
    "zadzwon",
    "zadzwoń",
    "umow",
    "umów",
    "konsultacje",
    "wycena",
    "zapytaj",
    "oferta",
}


def analyze_ctas(html_text: str) -> dict[str, Any]:
    soup = soup_from_html(html_text)
    ctas: list[dict[str, str]] = []
    keyword_hits = 0
    for element in soup.find_all(["a", "button", "input"]):
        text = element.get_text(" ", strip=True) or element.get("value") or element.get("aria-label") or ""
        lowered = text.lower()
        matched = sorted(keyword for keyword in CTA_KEYWORDS if keyword in lowered)
        if matched:
            keyword_hits += len(matched)
            ctas.append({"text": text, "href": element.get("href") or "", "keywords": ",".join(matched)})
    return {
        "ctas": ctas,
        "cta_count": len(ctas),
        "cta_missing": not ctas,
        "weak_cta": bool(ctas) and keyword_hits < 2,
    }
