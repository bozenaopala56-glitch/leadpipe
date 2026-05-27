from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup


def _asset_years(html_text: str) -> list[int]:
    years = re.findall(r"(?:/|-|_)(20[0-2]\d|19\d{2})(?:/|-|_|\.)", html_text)
    return [int(year) for year in years]


def _soup(html_text: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html_text or "", "lxml")
    except Exception:
        return BeautifulSoup(html_text or "", "html.parser")


def detect_tech(html_text: str, headers: dict[str, Any]) -> dict[str, Any]:
    """Wykrywa WordPress, GTM, Meta Pixel, inny CMS.
    Zwraca: {wordpress, gtm, meta_pixel, cms_type, old_assets}
    """
    lowered = (html_text or "").lower()
    soup = _soup(html_text)
    generator = ""
    generator_meta = soup.find("meta", attrs={"name": re.compile("^generator$", re.I)})
    if generator_meta:
        generator = (generator_meta.get("content") or "").lower()

    wordpress = "/wp-content/" in lowered or "/wp-json/" in lowered or "wordpress" in generator
    cms_type = None
    if wordpress:
        cms_type = "wordpress"
    elif "joomla" in generator or "/media/system/js/" in lowered:
        cms_type = "joomla"
    elif "drupal" in generator or "/sites/default/" in lowered:
        cms_type = "drupal"

    current_year = datetime.now(timezone.utc).year
    old_assets = any(year <= current_year - 3 for year in _asset_years(html_text or ""))

    return {
        "wordpress": wordpress,
        "gtm": "googletagmanager.com" in lowered or "gtm-" in lowered,
        "meta_pixel": "connect.facebook.net" in lowered or "fbq(" in lowered,
        "cms_type": cms_type,
        "cms_detected": cms_type is not None and cms_type != "wordpress",
        "old_assets": old_assets,
        "server": headers.get("Server") or headers.get("server"),
    }
