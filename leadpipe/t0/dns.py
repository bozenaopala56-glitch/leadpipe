from __future__ import annotations

import socket
from typing import Any


def scan_dns(domain: str) -> dict[str, Any]:
    """A/AAAA/MX/TXT records.
    Zwraca: {has_a_record, has_mx, has_txt, ips: []}
    Uzywa socket.getaddrinfo + dns.resolver jesli dostepny.
    """
    normalized = domain.strip().lower().removeprefix("http://").removeprefix("https://").split("/")[0]
    result: dict[str, Any] = {
        "has_a_record": False,
        "has_mx": False,
        "has_txt": False,
        "ips": [],
        "error": None,
    }

    try:
        records = socket.getaddrinfo(normalized, None, type=socket.SOCK_STREAM)
        ips = sorted({record[4][0] for record in records if record and record[4]})
        result["ips"] = ips
        result["has_a_record"] = bool(ips)
    except OSError as exc:
        result["error"] = str(exc)

    try:
        import dns.resolver  # type: ignore[import-not-found]

        resolver = dns.resolver.Resolver()
        resolver.lifetime = 5
        resolver.timeout = 3
        for record_type, key in (("MX", "has_mx"), ("TXT", "has_txt")):
            try:
                result[key] = bool(resolver.resolve(normalized, record_type))
            except Exception:
                result[key] = False
    except ImportError:
        pass

    return result
