from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from leadpipe.csv_schemas import FeedbackCsvSchema, ImportCsvSchema, parse_csv
from leadpipe.engine import DecisionEngine
from leadpipe.models import (
    CampaignDecision,
    CampaignKey,
    DecisionAction,
    Evidence,
    EvidenceType,
    Lead,
    ScanResult,
    ScanStatus,
    Signal,
    SignalSource,
)
from leadpipe.ruleset import load_current_ruleset_version


def test_lead_validation_and_serialization_roundtrip() -> None:
    lead = Lead(
        input_domain="https://www.Example.PL/",
        normalized_domain="www.Example.PL",
        company_name="Example",
        nip="123-456-32-18",
        contact_email="biuro@example.pl",
    )

    dumped = lead.model_dump_json()
    restored = Lead.model_validate_json(dumped)

    assert restored.normalized_domain == "example.pl"
    assert restored.nip == "1234563218"
    assert restored.contact_email == "biuro@example.pl"


def test_closed_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Lead(input_domain="a.pl", normalized_domain="a.pl", unexpected=True)


def test_scan_result_nested_contracts() -> None:
    lead = Lead(input_domain="a.pl", normalized_domain="a.pl")
    evidence = Evidence(type=EvidenceType.TLS, key="ssl_invalid", value="certificate expired", confidence=0.9)
    signal = Signal(key="ssl_invalid", value=True, source=SignalSource.T0, confidence=0.9, evidence_ids=[evidence.id])
    scan = ScanResult(lead_id=lead.id, status=ScanStatus.OK, signals=[signal], evidence=[evidence], http_status=200)

    restored = ScanResult.model_validate_json(scan.model_dump_json())

    assert restored.signals[0].key == "ssl_invalid"
    assert restored.evidence[0].type == EvidenceType.TLS.value


def test_campaign_decision_send_requires_campaign() -> None:
    lead = Lead(input_domain="a.pl", normalized_domain="a.pl")

    with pytest.raises(ValidationError):
        CampaignDecision(lead_id=lead.id, action=DecisionAction.SEND, ruleset_version="ruleset-test")

    decision = CampaignDecision(
        lead_id=lead.id,
        action=DecisionAction.SEND,
        campaign=CampaignKey.REDESIGN_TRUST,
        confidence=0.8,
        ruleset_version="ruleset-test",
    )
    assert decision.campaign == CampaignKey.REDESIGN_TRUST.value


def test_campaign_key_contains_only_final_www_campaigns() -> None:
    assert {campaign.value for campaign in CampaignKey} == {
        "REDESIGN_OUTDATED",
        "REDESIGN_ADS_WASTE",
        "REDESIGN_CONVERSION",
        "REDESIGN_TRUST",
        "WORDPRESS_REWORK",
        "MOBILE_REBUILD",
        "TECH_REBUILD",
    }


def test_ruleset_hash_is_stable() -> None:
    version = load_current_ruleset_version()
    assert version.name == "ruleset-2026-05-23-v1"
    assert len(version.audit_hash) == 64
    assert version.audit_hash == load_current_ruleset_version().audit_hash


def test_csv_import_and_feedback_parsing() -> None:
    csv_text = "domain,url,company_name,nip,source,contact_email,notes\nwww.Example.pl,https://example.pl,Example,123-456-32-18,test,biuro@example.pl,ok\n"

    records, errors = parse_csv(csv_text, ImportCsvSchema)

    assert not errors
    assert records[0].domain == "example.pl"
    assert records[0].nip == "1234563218"

    feedback, feedback_errors = parse_csv(
        "domain,email,event,timestamp,notes\nexample.pl,biuro@example.pl,positive_reply,2026-05-23T10:00:00Z,dobry lead\n",
        FeedbackCsvSchema,
    )
    assert not feedback_errors
    assert feedback[0].event == "positive_reply"


def test_decision_engine_trust_campaign() -> None:
    engine = DecisionEngine()
    lead = Lead(input_domain="alfa.pl", normalized_domain="alfa.pl", company_name="Alfa", contact_email="biuro@alfa.pl")

    decision, trace = engine.evaluate(
        lead,
        {
            "ssl_invalid": True,
            "cert_expired": True,
            "low_trust": True,
            "campaign_confidence": 0.81,
            "contactability": 80,
            "industry_fit": 75,
            "lead_value": 70,
            "evidence_count": 2,
            "evidence_strength": 82,
        },
    )

    assert decision.action == "send"
    assert decision.campaign == "REDESIGN_TRUST"
    assert trace.winning_rule == "CAMPAIGN_REDESIGN_TRUST"
    assert trace.evaluated_rules


def test_decision_engine_weighted_tech_rebuild_campaign() -> None:
    engine = DecisionEngine()
    lead = Lead(input_domain="beta.pl", normalized_domain="beta.pl", company_name="Beta", contact_email="kontakt@beta.pl")

    decision, trace = engine.evaluate(
        lead,
        {
            "speed_slow": True,
            "old_stack": True,
            "old_assets": True,
            "cache_missing": True,
            "campaign_confidence": 0.77,
            "contactability": 70,
            "industry_fit": 70,
            "lead_value": 65,
            "evidence_count": 2,
            "evidence_strength": 74,
        },
    )

    assert decision.action == "send"
    assert decision.campaign == "TECH_REBUILD"
    assert trace.winning_rule == "CAMPAIGN_TECH_REBUILD"


def test_decision_engine_t2_and_suppression_paths() -> None:
    engine = DecisionEngine()
    lead = Lead(input_domain="delta.pl", normalized_domain="delta.pl", contact_email="biuro@delta.pl")

    decision, trace = engine.evaluate(
        lead,
        {
            "t0_confidence": 0.8,
            "t1_confidence": 0.4,
            "contactability": 80,
            "industry_fit": 80,
            "lead_value": 80,
            "evidence_count": 1,
            "campaign_confidence": 0.6,
        },
    )
    assert decision.action == "t2_required"
    assert trace.winning_rule == "T2_MUST_AMBIGUOUS_HOOK"

    suppressed, suppressed_trace = engine.evaluate(lead, {"suppressed": True})
    assert suppressed.action == "skip"
    assert suppressed_trace.blocked_by == ["GATE_COMPLIANCE_SUPPRESSION"]


def test_sample_leads_file_can_be_evaluated() -> None:
    engine = DecisionEngine()
    payload = json.loads(Path("data/sample-leads-for-test.json").read_text(encoding="utf-8"))

    decisions = []
    for item in payload:
        signals = item.pop("signals")
        decision, _ = engine.evaluate(Lead.model_validate(item), signals)
        decisions.append(decision.action)

    assert decisions == ["send", "send", "skip", "t2_required", "skip"]
