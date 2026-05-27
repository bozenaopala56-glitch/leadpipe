from __future__ import annotations

import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .dns import scan_dns
from .html import scan_html
from .http import scan_http
from .performance import scan_performance
from .ssl import scan_ssl
from .tech import detect_tech
from .url import is_http_url


def _fetch_html(url: str | None) -> tuple[str, str | None]:
    if not url:
        return "", "missing final_url"
    if not is_http_url(url):
        return "", "unsupported URL scheme"
    request = Request(url, headers={"User-Agent": "leadpipe-t0/0.1"})
    try:
        with urlopen(request, timeout=10) as response:
            content_type = response.headers.get_content_charset() or "utf-8"
            payload = response.read(750_000)
            return payload.decode(content_type, errors="replace"), None
    except HTTPError as exc:
        try:
            payload = exc.read(750_000)
            charset = exc.headers.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace"), f"HTTP {exc.code}"
        except Exception:
            return "", f"HTTP {exc.code}"
    except (TimeoutError, socket.timeout, URLError, OSError) as exc:
        return "", str(getattr(exc, "reason", exc))


def compute_t0_signals(domain: str) -> dict[str, Any]:
    """Uruchamia wszystkie moduly, scala wyniki.
    Zwraca dict gotowy do wstrzykniecia do DecisionEngine.evaluate(signals).
    """
    dns_result = scan_dns(domain)
    http_result = scan_http(domain)
    ssl_result = scan_ssl(domain)

    html_text, html_error = _fetch_html(http_result.get("final_url"))
    html_result = scan_html(html_text) if html_text else {
        "viewport_present": False,
        "company_in_title": False,
        "form_present": False,
        "cta_keywords_found": [],
        "contact_hidden": False,
        "html_size": 0,
    }
    tech_result = detect_tech(html_text, http_result.get("headers") or {})
    performance_result = (
        scan_performance(http_result["final_url"]) if http_result.get("final_url") else {
            "ttfb_ms": None,
            "page_size_bytes": 0,
            "gzip_enabled": False,
            "cache_headers": {},
            "error": "missing final_url",
        }
    )

    status_code = http_result.get("status_code")
    domain_present = bool(dns_result.get("has_a_record") and status_code is not None)
    cache_headers = performance_result.get("cache_headers") or {}
    cta_keywords = html_result.get("cta_keywords_found") or []
    evidence_signal_count = sum(
        1
        for value in (
            status_code is not None,
            bool(html_text),
            bool(cta_keywords),
            bool(tech_result.get("cms_type")),
            bool(dns_result.get("has_mx")),
        )
        if value
    )
    t0_confidence = min(1.0, 0.2 + evidence_signal_count * 0.16)

    signals = {
        "domain_present": domain_present,
        "scan_failed_final": not domain_present and bool(http_result.get("error")),
        "transient_scan_error": bool(http_result.get("transient_error")),
        "https_missing": bool(domain_present and not http_result.get("https_available")) or bool(ssl_result.get("https_missing")),
        "ssl_invalid": bool(ssl_result.get("ssl_invalid")),
        "cert_expired": bool(ssl_result.get("cert_expired")),
        "viewport_missing": not bool(html_result.get("viewport_present")),
        "company_identity_missing": not bool(html_result.get("company_in_title")),
        "form_present": bool(html_result.get("form_present")),
        "form_missing": not bool(html_result.get("form_present")),
        "cta_missing": not bool(cta_keywords),
        "weak_cta": 0 < len(cta_keywords) < 2,
        "contact_hidden": bool(html_result.get("contact_hidden")),
        "html_too_large": int(html_result.get("html_size") or performance_result.get("page_size_bytes") or 0) > 500_000,
        "wordpress_detected": bool(tech_result.get("wordpress")),
        "cms_detected": bool(tech_result.get("cms_detected")),
        "old_assets": bool(tech_result.get("old_assets")),
        "old_stack": bool(tech_result.get("old_assets")),
        "gtm_detected": bool(tech_result.get("gtm")),
        "meta_pixel_detected": bool(tech_result.get("meta_pixel")),
        "not_mobile_friendly": not bool(html_result.get("viewport_present")) and "@media" not in html_text.lower(),
        "speed_slow": (performance_result.get("ttfb_ms") or 0) > 2000,
        "compression_missing": not bool(performance_result.get("gzip_enabled")),
        "cache_missing": not bool(cache_headers.get("cache_control") or cache_headers.get("expires")),
        "t0_confidence": t0_confidence,
        "evidence_strength": t0_confidence * 100,
    }

    return {
        **signals,
        "scan_result": {
            "dns": dns_result,
            "http": http_result,
            "ssl": ssl_result,
            "html": html_result,
            "tech": tech_result,
            "performance": performance_result,
            "html_error": html_error,
        },
    }
