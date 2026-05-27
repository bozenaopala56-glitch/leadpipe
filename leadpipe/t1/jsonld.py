from __future__ import annotations

import json
from typing import Any

from ._html import soup_from_html


def _iter_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        items: list[dict[str, Any]] = []
        for item in value:
            items.extend(_iter_items(item))
        return items
    if not isinstance(value, dict):
        return []
    graph = value.get("@graph")
    if isinstance(graph, list):
        return [item for item in graph if isinstance(item, dict)]
    return [value]


def _type_name(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def extract_jsonld(html_text: str) -> dict[str, Any]:
    soup = soup_from_html(html_text)
    items: list[dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(script.get_text(strip=True))
        except json.JSONDecodeError:
            continue
        for item in _iter_items(payload):
            item_type = _type_name(item.get("@type"))
            normalized = {**item, "type": item_type}
            items.append(normalized)

    organization = next(
        (
            item
            for item in items
            if item.get("type") in {"Organization", "LocalBusiness", "Corporation", "Store", "ProfessionalService"}
        ),
        {},
    )
    return {"items": items, "organization": organization}
