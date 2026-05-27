from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from leadpipe.models import Lead

from .signals import compute_t0_signals


def _lead_domain(lead: Lead | dict[str, Any]) -> str:
    if isinstance(lead, Lead):
        return lead.normalized_domain
    return str(lead.get("normalized_domain") or lead.get("domain") or lead.get("input_domain") or "")


def _lead_id(lead: Lead | dict[str, Any]) -> str | None:
    if isinstance(lead, Lead):
        return str(lead.id)
    value = lead.get("id") or lead.get("lead_id")
    return str(value) if value is not None else None


def _scan_one(lead: Lead | dict[str, Any]) -> dict[str, Any]:
    domain = _lead_domain(lead)
    result = compute_t0_signals(domain)
    scan_result = result.pop("scan_result")
    return {"lead_id": _lead_id(lead), "signals": result, "scan_result": scan_result}


def run_t0_batch(leads: list[Lead | dict[str, Any]], concurrency: int = 5, max_retries: int = 2) -> list[dict[str, Any]]:
    """Skanuje batch leadow z concurrency.
    Zwraca liste {lead_id, signals, scan_result} per lead.
    """
    del max_retries
    workers = max(1, concurrency)
    results: list[dict[str, Any] | None] = [None] * len(leads)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(_scan_one, lead): index for index, lead in enumerate(leads)}
        for future in as_completed(future_map):
            index = future_map[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                results[index] = {
                    "lead_id": _lead_id(leads[index]),
                    "signals": {"domain_present": False, "scan_failed_final": True, "transient_scan_error": False},
                    "scan_result": {"error": str(exc)},
                }
    return [result for result in results if result is not None]
