from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .csv_schemas import ImportCsvSchema, parse_csv
from .engine import DecisionEngine
from .models import Lead, LeadStatus
from .t0 import run_t0_batch
from .t0_5 import run_t0_5
from .t1 import run_t1


def _empty_state() -> dict[str, Any]:
    return {"leads": [], "scans": {}, "decisions": {}}


def _state_path() -> Path:
    return Path(os.environ.get("LEADPIPE_STATE", ".leadpipe/state.json"))


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        return _empty_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_state()
    if not isinstance(payload, dict):
        return _empty_state()
    leads = payload.get("leads", [])
    scans = payload.get("scans", {})
    decisions = payload.get("decisions", {})
    return {
        "leads": leads if isinstance(leads, list) else [],
        "scans": scans if isinstance(scans, dict) else {},
        "decisions": decisions if isinstance(decisions, dict) else {},
    }


def _save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(path)


def _lead_from_import(record: ImportCsvSchema) -> Lead:
    return Lead(
        input_domain=record.domain,
        normalized_domain=record.domain,
        url=record.url,
        company_name=record.company_name,
        nip=record.nip,
        source=record.source,
        contact_email=record.contact_email,
        metadata={"notes": record.notes} if record.notes else {},
    )


def _find_leads(state: dict[str, Any], selector: str, limit: int | None = None) -> list[Lead]:
    raw_leads = state.get("leads", [])
    if not isinstance(raw_leads, list):
        return []
    if selector == "batch":
        selected = raw_leads[:limit] if limit else raw_leads
    else:
        selected = [item for item in raw_leads if isinstance(item, dict) and item.get("id") == selector]
    leads: list[Lead] = []
    for item in selected:
        try:
            leads.append(Lead.model_validate(item))
        except ValueError:
            continue
    return leads


def _store_lead(state: dict[str, Any], lead: Lead) -> None:
    if not isinstance(state.get("leads"), list):
        state["leads"] = []
    dumped = lead.model_dump(mode="json")
    for index, item in enumerate(state["leads"]):
        if item.get("id") == dumped["id"]:
            state["leads"][index] = dumped
            return
    state["leads"].append(dumped)


def command_import(args: argparse.Namespace) -> int:
    records, errors = parse_csv(args.file, ImportCsvSchema)
    if errors:
        for row, messages in errors:
            print(f"row={row} errors={'; '.join(messages)}")
        return 2
    state = _load_state()
    imported = 0
    for record in records:
        lead = _lead_from_import(record)
        _store_lead(state, lead)
        imported += 1
    _save_state(state)
    print(f"imported={imported}")
    return 0


def _scan_leads(state: dict[str, Any], leads: list[Lead]) -> int:
    if not leads:
        return 0
    t0_results = run_t0_batch(leads, concurrency=1)
    for lead, t0_result in zip(leads, t0_results):
        html_text = str((t0_result.get("scan_result") or {}).get("html_text") or "")
        t0_5_result = run_t0_5(lead, html_text=html_text)
        t1_result = run_t1(html_text, headers=((t0_result.get("scan_result") or {}).get("http") or {}).get("headers") or {})
        updated = lead.model_copy(update={"status": LeadStatus.SCANNED, "nip": t0_5_result["lead"].get("nip") or lead.nip})
        _store_lead(state, updated)
        state["scans"][str(lead.id)] = {"t0": t0_result, "t0_5": t0_5_result, "t1": t1_result}
    return len(leads)


def command_scan(args: argparse.Namespace) -> int:
    state = _load_state()
    leads = _find_leads(state, args.selector)
    scanned = _scan_leads(state, leads)
    _save_state(state)
    print(f"scanned={scanned}")
    return 0


def _decision_signals(state: dict[str, Any], lead_id: str) -> dict[str, Any]:
    scan = state.get("scans", {}).get(lead_id) or {}
    signals: dict[str, Any] = {}
    signals.update((scan.get("t0") or {}).get("signals") or {})
    signals.update((scan.get("t0_5") or {}).get("signals") or {})
    signals.update((scan.get("t1") or {}).get("signals") or {})
    signals.setdefault("evidence_count", sum(1 for value in signals.values() if value not in (False, None, "", 0, [], {})))
    return signals


def _decide_leads(state: dict[str, Any], leads: list[Lead]) -> int:
    engine = DecisionEngine()
    count = 0
    for lead in leads:
        decision, trace = engine.evaluate(lead, _decision_signals(state, str(lead.id)))
        state["decisions"][str(lead.id)] = {
            "decision": decision.model_dump(mode="json"),
            "trace": trace.model_dump(mode="json"),
        }
        _store_lead(state, lead.model_copy(update={"status": LeadStatus.DECIDED}))
        print(f"lead_id={lead.id} decision={decision.action} campaign={decision.campaign or ''}")
        count += 1
    return count


def command_decide(args: argparse.Namespace) -> int:
    state = _load_state()
    leads = _find_leads(state, args.selector)
    decided = _decide_leads(state, leads)
    _save_state(state)
    if decided == 0:
        print("decision=missing_lead")
        return 1
    return 0


def command_pipeline(args: argparse.Namespace) -> int:
    state = _load_state()
    before_ids = {item.get("id") for item in state.get("leads", [])}
    if args.file:
        import_args = argparse.Namespace(file=args.file)
        records, errors = parse_csv(import_args.file, ImportCsvSchema)
        if errors:
            for row, messages in errors:
                print(f"row={row} errors={'; '.join(messages)}")
            return 2
        for record in records[: args.batch_size]:
            _store_lead(state, _lead_from_import(record))
    new_leads = [Lead.model_validate(item) for item in state["leads"] if item.get("id") not in before_ids]
    leads = new_leads or _find_leads(state, "batch", args.batch_size)
    processed = _scan_leads(state, leads)
    _decide_leads(state, leads)
    _save_state(state)
    print(f"pipeline_done={processed}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="leadpipe")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("file")
    import_parser.set_defaults(func=command_import)

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("selector")
    scan_parser.set_defaults(func=command_scan)

    decide_parser = subparsers.add_parser("decide")
    decide_parser.add_argument("selector")
    decide_parser.set_defaults(func=command_decide)

    pipeline_parser = subparsers.add_parser("pipeline")
    pipeline_parser.add_argument("batch_size", type=int)
    pipeline_parser.add_argument("--file")
    pipeline_parser.set_defaults(func=command_pipeline)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
