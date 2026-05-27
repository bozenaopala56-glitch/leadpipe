from __future__ import annotations

from leadpipe.t0.http import scan_http
from leadpipe.t0.performance import scan_performance
from leadpipe.t0.signals import _fetch_html
from leadpipe.t0.url import normalize_host


def test_t0_rejects_empty_and_non_http_urls_without_network() -> None:
    assert normalize_host("https://www.Example.pl/path?q=1") == "example.pl"
    assert normalize_host("http://bad host/") == ""

    http = scan_http("")
    assert http["status_code"] is None
    assert http["error"] == "missing domain"

    performance = scan_performance("file:///tmp/secret")
    assert performance["error"] == "unsupported URL scheme"

    html, error = _fetch_html("file:///tmp/secret")
    assert html == ""
    assert error == "unsupported URL scheme"
