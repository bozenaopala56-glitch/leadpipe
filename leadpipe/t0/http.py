from __future__ import annotations

import socket
import time
from http.client import HTTPResponse
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def http_error_301(self, req: Request, fp: HTTPResponse, code: int, msg: str, headers: Any) -> HTTPResponse:
        return fp

    http_error_302 = http_error_303 = http_error_307 = http_error_308 = http_error_301


def _request_once(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "leadpipe-t0/0.1"})
    opener = build_opener(_NoRedirect)
    started = time.perf_counter()
    try:
        with opener.open(request, timeout=timeout) as response:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return {
                "status_code": response.getcode(),
                "url": response.geturl(),
                "headers": dict(response.headers.items()),
                "elapsed_ms": elapsed_ms,
                "error": None,
            }
    except HTTPError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "status_code": exc.code,
            "url": url,
            "headers": dict(exc.headers.items()) if exc.headers else {},
            "elapsed_ms": elapsed_ms,
            "error": None,
        }
    except (TimeoutError, socket.timeout, ConnectionResetError, URLError, OSError) as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        reason = getattr(exc, "reason", exc)
        return {"status_code": None, "url": url, "headers": {}, "elapsed_ms": elapsed_ms, "error": str(reason)}


def _is_redirect(status_code: int | None) -> bool:
    return status_code in {301, 302, 303, 307, 308}


def scan_http(domain: str) -> dict[str, Any]:
    """Sprawdza HTTP/HTTPS, redirects, status code.
    Zwraca: {status_code, final_url, https_available, redirect_count, headers}
    Obsluga: timeout 10s, retry 2x, 429 backoff.
    """
    host = domain.strip().removeprefix("http://").removeprefix("https://").split("/")[0]
    urls = [f"https://{host}", f"http://{host}"]
    last_error: str | None = None
    transient_error = False

    for start_url in urls:
        current_url = start_url
        redirect_count = 0
        headers: dict[str, str] = {}
        status_code: int | None = None

        for attempt in range(3):
            response = _request_once(current_url, timeout=10)
            status_code = response["status_code"]
            headers = response["headers"]
            last_error = response["error"]

            if status_code == 429:
                transient_error = True
                time.sleep(min(2**attempt, 4))
                continue
            if status_code in {503} or (last_error and "reset" in last_error.lower()):
                transient_error = True
                if attempt < 2:
                    time.sleep(min(2**attempt, 4))
                    continue

            while _is_redirect(status_code) and redirect_count < 10:
                location = headers.get("Location") or headers.get("location")
                if not location:
                    break
                location = urljoin(current_url, location)
                current_url = location
                redirect_count += 1
                response = _request_once(current_url, timeout=10)
                status_code = response["status_code"]
                headers = response["headers"]
                last_error = response["error"]

            if status_code is not None:
                http_redirects_to_https = False
                if start_url.startswith("https://"):
                    http_probe = _request_once(f"http://{host}", timeout=10)
                    location = (http_probe.get("headers") or {}).get("Location") or (
                        http_probe.get("headers") or {}
                    ).get("location")
                    http_redirects_to_https = bool(
                        _is_redirect(http_probe.get("status_code")) and location and urljoin(f"http://{host}", location).startswith("https://")
                    )
                else:
                    http_redirects_to_https = current_url.startswith("https://")
                return {
                    "status_code": status_code,
                    "final_url": current_url,
                    "https_available": current_url.startswith("https://") or start_url.startswith("https://"),
                    "http_redirects_to_https": http_redirects_to_https,
                    "redirect_count": redirect_count,
                    "headers": headers,
                    "transient_error": transient_error,
                    "error": None,
                }
            break

    return {
        "status_code": None,
        "final_url": None,
        "https_available": False,
        "http_redirects_to_https": False,
        "redirect_count": 0,
        "headers": {},
        "transient_error": transient_error,
        "error": last_error or "HTTP scan failed",
    }
