from __future__ import annotations

from bs4 import BeautifulSoup


def soup_from_html(html_text: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html_text or "", "lxml")
    except Exception:
        return BeautifulSoup(html_text or "", "html.parser")
