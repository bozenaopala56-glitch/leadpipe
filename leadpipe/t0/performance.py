from __future__ import annotations

import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def scan_performance(url: str) -> dict[str, Any]:
    """Mierzy TTFB, rozmiar, kompresje.
    Zwraca: {ttfb_ms, page_size_bytes, gzip_enabled, cache_headers}
    """
    request = Request(url, headers={"User-Agent": "leadpipe-t0/0.1", "Accept-Encoding": "gzip"})
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=10) as response:
            first_chunk = response.read(1)
            ttfb_ms = int((time.perf_counter() - started) * 1000)
            rest = response.read(500_001)
            headers = dict(response.headers.items())
            size = len(first_chunk) + len(rest)
            cache_headers = {
                "cache_control": headers.get("Cache-Control") or headers.get("cache-control"),
                "expires": headers.get("Expires") or headers.get("expires"),
            }
            return {
                "ttfb_ms": ttfb_ms,
                "page_size_bytes": size,
                "gzip_enabled": (headers.get("Content-Encoding") or headers.get("content-encoding") or "").lower()
                == "gzip",
                "cache_headers": cache_headers,
                "error": None,
            }
    except HTTPError as exc:
        return {
            "ttfb_ms": int((time.perf_counter() - started) * 1000),
            "page_size_bytes": 0,
            "gzip_enabled": False,
            "cache_headers": {},
            "error": f"HTTP {exc.code}",
        }
    except (TimeoutError, socket.timeout, URLError, OSError) as exc:
        return {
            "ttfb_ms": None,
            "page_size_bytes": 0,
            "gzip_enabled": False,
            "cache_headers": {},
            "error": str(getattr(exc, "reason", exc)),
        }
