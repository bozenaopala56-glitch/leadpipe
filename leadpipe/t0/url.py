from __future__ import annotations

import re
from urllib.parse import urlsplit


_HOST_RE = re.compile(r"^[a-z0-9.-]+$", re.I)


def normalize_host(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "://" not in text:
        text = f"//{text}"
    parsed = urlsplit(text)
    host = (parsed.hostname or "").strip().lower().removeprefix("www.")
    if not host or not _HOST_RE.fullmatch(host):
        return ""
    return host


def is_http_url(value: object) -> bool:
    try:
        parsed = urlsplit(str(value or ""))
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
