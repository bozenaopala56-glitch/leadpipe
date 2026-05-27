from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone
from typing import Any

from .url import normalize_host


def _issuer_name(cert: dict[str, Any]) -> str | None:
    issuer = cert.get("issuer") or ()
    parts = []
    for item in issuer:
        for key, value in item:
            if key in {"organizationName", "commonName"}:
                parts.append(value)
    return ", ".join(parts) or None


def _expires_days(cert: dict[str, Any]) -> int | None:
    not_after = cert.get("notAfter")
    if not not_after:
        return None
    try:
        expires_at = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (expires_at - datetime.now(timezone.utc)).days


def scan_ssl(domain: str) -> dict[str, Any]:
    """Polaczenie TLS, pobiera cert.
    Zwraca: {valid, expires_days, issuer, hostname_match}
    Obsluga: timeout 5s, brak HTTPS -> {valid: false, https_missing: true}.
    """
    host = normalize_host(domain)
    result: dict[str, Any] = {
        "valid": False,
        "expires_days": None,
        "issuer": None,
        "hostname_match": False,
        "https_missing": False,
        "cert_expired": False,
        "ssl_invalid": False,
        "error": None,
    }
    if not host:
        result["https_missing"] = True
        result["error"] = "missing domain"
        return result

    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
        days = _expires_days(cert)
        result.update(
            {
                "valid": True,
                "expires_days": days,
                "issuer": _issuer_name(cert),
                "hostname_match": True,
                "cert_expired": days is not None and days < 0,
            }
        )
        return result
    except ssl.SSLError as exc:
        result["ssl_invalid"] = True
        result["error"] = str(exc)
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        result["https_missing"] = True
        result["error"] = str(exc)
        return result

    try:
        context = ssl._create_unverified_context()
        with socket.create_connection((host, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
        days = _expires_days(cert)
        hostname_match = False
        try:
            ssl.match_hostname(cert, host)
            hostname_match = True
        except Exception:
            hostname_match = False
        result.update(
            {
                "expires_days": days,
                "issuer": _issuer_name(cert),
                "hostname_match": hostname_match,
                "cert_expired": days is not None and days < 0,
            }
        )
    except Exception:
        pass
    return result
