from __future__ import annotations

import json

from leadpipe.cli import main


def test_cli_import_scan_decide_pipeline_with_local_state(tmp_path, monkeypatch, capsys) -> None:
    state_path = tmp_path / "state.json"
    csv_path = tmp_path / "leads.csv"
    csv_path.write_text("domain,company_name,nip\nexample.pl,Example,1234563218\n", encoding="utf-8")
    monkeypatch.setenv("LEADPIPE_STATE", str(state_path))

    assert main(["import", str(csv_path)]) == 0
    imported = capsys.readouterr().out
    assert "imported=1" in imported

    assert main(["scan", "batch"]) == 0
    scanned = capsys.readouterr().out
    assert "scanned=1" in scanned

    state = json.loads(state_path.read_text(encoding="utf-8"))
    lead_id = state["leads"][0]["id"]
    assert state["leads"][0]["status"] == "scanned"

    assert main(["decide", lead_id]) == 0
    decided = capsys.readouterr().out
    assert "decision=" in decided

    assert main(["pipeline", "1", "--file", str(csv_path)]) == 0
    piped = capsys.readouterr().out
    assert "pipeline_done=1" in piped
