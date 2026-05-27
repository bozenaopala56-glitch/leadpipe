from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup


CTA_KEYWORDS = {
    "kontakt",
    "zadzwoń",
    "zadzwon",
    "wyślij",
    "wyslij",
    "napisz",
    "umów",
    "umow",
    "rezerwuj",
    "call",
    "contact",
    "send",
}


def _soup(html_text: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html_text or "", "lxml")
    except Exception:
        return BeautifulSoup(html_text or "", "html.parser")


def scan_html(html_text: str) -> dict[str, Any]:
    """Parsuje HTML, wyciaga meta, viewport, formularze, CTA.
    Zwraca: {viewport_present, company_in_title, form_present,
             cta_keywords_found: [...], contact_hidden, html_size}
    Uzywa BeautifulSoup.
    """
    soup = _soup(html_text)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    og_site_name = ""
    og_title = ""
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        if name == "viewport":
            viewport_present = True
        elif name == "og:site_name":
            og_site_name = meta.get("content") or ""
        elif name == "og:title":
            og_title = meta.get("content") or ""
    viewport_present = bool(soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)}))

    forms = soup.find_all("form")
    form_present = any((form.get("method") or "").lower() == "post" for form in forms)

    cta_keywords_found: list[str] = []
    for element in soup.find_all(["a", "button", "input"]):
        text = element.get_text(" ", strip=True) or element.get("value") or element.get("aria-label") or ""
        lowered = text.lower()
        for keyword in CTA_KEYWORDS:
            if keyword in lowered and keyword not in cta_keywords_found:
                cta_keywords_found.append(keyword)

    visible_text = soup.get_text(" ", strip=True).lower()
    script_text = " ".join(script.get_text(" ", strip=True).lower() for script in soup.find_all("script"))
    has_visible_contact = bool(re.search(r"\b(kontakt|contact)\b|[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d\s().-]{7,}", visible_text))
    has_script_contact = bool(re.search(r"\b(kontakt|contact)\b|[\w.+-]+@[\w.-]+\.\w+|\+?\d[\d\s().-]{7,}", script_text))

    return {
        "viewport_present": viewport_present,
        "company_in_title": bool(title or og_site_name or og_title),
        "form_present": form_present,
        "cta_keywords_found": sorted(cta_keywords_found),
        "contact_hidden": has_script_contact and not has_visible_contact,
        "html_size": len((html_text or "").encode("utf-8")),
        "title": title,
        "og_site_name": og_site_name,
    }
