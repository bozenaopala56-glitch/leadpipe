from __future__ import annotations

from typing import Any

from ._html import soup_from_html


def analyze_forms(html_text: str) -> dict[str, Any]:
    soup = soup_from_html(html_text)
    forms: list[dict[str, Any]] = []
    for form in soup.find_all("form"):
        fields: list[str] = []
        for field in form.find_all(["input", "textarea", "select"]):
            name = field.get("name") or field.get("id") or field.get("type")
            if name and name not in fields:
                fields.append(str(name))
        forms.append(
            {
                "action": form.get("action") or "",
                "method": (form.get("method") or "get").lower(),
                "fields": fields,
                "is_contact_form": any(token in " ".join(fields).lower() for token in ["email", "message", "phone", "telefon"]),
            }
        )
    return {
        "form_present": bool(forms),
        "form_missing": not bool(forms),
        "forms": forms,
        "contact_form_present": any(form["is_contact_form"] for form in forms),
    }
