from __future__ import annotations

import re
from typing import Any


COMPETITOR = ["projektowanie stron", "strony www", "seo", "google ads", "agencja", "software house", "hosting"]
INDUSTRIAL = ["producent", "produkcja", "przemysl", "przemysł", "instalacje", "maszyny", "b2b"]
SERVICES = ["uslugi", "usługi", "serwis", "montaz", "montaż", "doradztwo"]
MEDICAL = ["klinika", "gabinet", "medycz", "stomatolog"]


def _score(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if re.search(rf"\b{re.escape(keyword)}", text))


def classify_industry(text_or_html: str) -> dict[str, Any]:
    text = re.sub(r"<[^>]+>", " ", text_or_html or "").lower()
    competitor_score = _score(text, COMPETITOR)
    industrial_score = _score(text, INDUSTRIAL)
    services_score = _score(text, SERVICES)
    medical_score = _score(text, MEDICAL)

    if competitor_score:
        return {
            "industry": "digital",
            "competitor": True,
            "competitor_confidence": min(1.0, 0.55 + competitor_score * 0.15),
            "industry_fit": 25,
            "lead_value": 35,
        }
    if industrial_score:
        return {"industry": "industrial", "competitor": False, "competitor_confidence": 0.0, "industry_fit": 85, "lead_value": 78}
    if medical_score:
        return {"industry": "medical", "competitor": False, "competitor_confidence": 0.0, "industry_fit": 65, "lead_value": 72}
    if services_score:
        return {"industry": "services", "competitor": False, "competitor_confidence": 0.0, "industry_fit": 70, "lead_value": 60}
    return {"industry": "unknown", "competitor": False, "competitor_confidence": 0.0, "industry_fit": 50, "lead_value": 50}
