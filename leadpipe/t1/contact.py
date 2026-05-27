from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote

from ._html import soup_from_html


EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}(?![\w.-])")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?48[\s.-]?)?(?:\d[\s().-]?){9,12}(?!\d)")
SOCIAL_HOSTS = {
    "facebook": "facebook.",
    "linkedin": "linkedin.",
    "instagram": "instagram.",
    "youtube": "youtube.",
    "x": "twitter.",
}


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def _normalize_phone(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit() or ch == "+")


def extract_contacts(html_text: str) -> dict[str, Any]:
    soup = soup_from_html(html_text)
    text = soup.get_text(" ", strip=True)
    emails = EMAIL_RE.findall(text)
    phones = [_normalize_phone(match.group(0)) for match in PHONE_RE.finditer(text)]
    social: dict[str, list[str]] = {key: [] for key in SOCIAL_HOSTS}

    for link in soup.find_all("a", href=True):
        href = unquote(str(link["href"]).strip())
        lowered = href.lower()
        if lowered.startswith("mailto:"):
            emails.extend(EMAIL_RE.findall(href[7:]))
        elif lowered.startswith("tel:"):
            phones.append(_normalize_phone(href[4:]))
        else:
            for name, host in SOCIAL_HOSTS.items():
                if host in lowered:
                    social[name].append(href)

    emails = _unique([email.lower() for email in emails])
    phones = _unique([phone for phone in phones if len("".join(ch for ch in phone if ch.isdigit())) >= 9])
    social = {key: _unique(values) for key, values in social.items() if values}
    contactability = min(100, (45 if emails else 0) + (35 if phones else 0) + (20 if social else 0))
    return {"emails": emails, "phones": phones, "social": social, "contactability": contactability}
