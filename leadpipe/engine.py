from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .decision_trace import DecisionTrace
from .models import CampaignDecision, CampaignKey, DecisionAction, Lead, ScoreBreakdown
from .ruleset import CURRENT_RULESET_VERSION


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal: str
    operator: str
    value: Any = None
    weight: float = 1.0


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    priority: int = 100
    conditions: list[Condition] = Field(default_factory=list)
    combine: str = "and"
    threshold: float | None = None
    decision: str
    campaign: CampaignKey | None = None
    confidence_threshold: float | None = None
    min_evidence: int = 0
    subject: str | None = None
    description: str = ""


class RuleFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    rules: list[Rule]


@dataclass(frozen=True)
class RuleMatch:
    rule: Rule
    score: float


class DecisionEngine:
    def __init__(self, rules_dir: str | Path | None = None) -> None:
        self.rules_dir = Path(rules_dir) if rules_dir else Path(str(files("leadpipe").joinpath("rules")))
        self.rule_files = self._load_rule_files()
        versions = {rule_file.version for rule_file in self.rule_files}
        self.ruleset_version = sorted(versions)[-1] if versions else CURRENT_RULESET_VERSION

    def _load_rule_files(self) -> list[RuleFile]:
        rule_files: list[RuleFile] = []
        for path in sorted(self.rules_dir.glob("*.yml")):
            with path.open(encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
            rule_files.append(RuleFile.model_validate(payload))
        return rule_files

    @property
    def rules(self) -> list[Rule]:
        all_rules = [rule for rule_file in self.rule_files for rule in rule_file.rules]
        return sorted(all_rules, key=lambda rule: (rule.priority, rule.key))

    def evaluate(self, lead: Lead | dict[str, Any], signals: dict[str, Any] | None = None) -> tuple[CampaignDecision, Any]:
        lead_model = lead if isinstance(lead, Lead) else Lead.model_validate(lead)
        context = self._context_from_lead(lead_model)
        context.update(signals or {})

        trace = DecisionTrace(lead_id=lead_model.id, ruleset_version=self.ruleset_version)
        trace.set_score_breakdown(
            evidence_strength=float(context.get("evidence_strength", 0) or 0),
            signal_confidence=float(context.get("signal_confidence", context.get("campaign_confidence", 0) * 100) or 0),
            contactability=float(context.get("contactability", 0) or 0),
            industry_fit=float(context.get("industry_fit", 0) or 0),
            lead_value=float(context.get("lead_value", 0) or 0),
            penalties=float(context.get("penalties", 0) or 0),
        )

        matched: RuleMatch | None = None
        for rule in self.rules:
            result, reason, score = self._evaluate_rule(rule, context)
            trace.record_rule(rule.key, result, reason, rule.decision, score)
            if result and matched is None:
                matched = RuleMatch(rule=rule, score=score)
                trace.set_winning_rule(rule.key)
                if rule.decision in {DecisionAction.SKIP.value, "skip_t2", "skip_t2_manual_review"}:
                    trace.block(rule.key)
                break

        if matched is None:
            action = DecisionAction.MANUAL_REVIEW
            campaign = None
            confidence = 0.0
            subject = None
            rule_key = None
        else:
            action = self._normalize_action(matched.rule.decision)
            campaign = matched.rule.campaign
            confidence = min(1.0, max(0.0, matched.score if matched.score <= 1 else matched.score / 100))
            subject = self._render_subject(matched.rule.subject, lead_model, campaign)
            rule_key = matched.rule.key

        trace_model = trace.to_model(action.value, campaign.value if campaign else None)
        decision = CampaignDecision(
            lead_id=lead_model.id,
            action=action,
            campaign=campaign,
            subject=subject,
            confidence=confidence,
            decision_reason=trace_model.decision_reason,
            ruleset_version=self.ruleset_version,
            rule_key=rule_key,
            score_breakdown=trace_model.score_breakdown,
            metadata={"trace": trace_model.model_dump(mode="json")},
        )
        return decision, trace_model

    def _context_from_lead(self, lead: Lead) -> dict[str, Any]:
        return {
            "domain_present": bool(lead.normalized_domain),
            "has_email": bool(lead.contact_email),
            "has_phone": bool(lead.phone),
            "nip_present": bool(lead.nip),
            "normalized_domain": lead.normalized_domain,
        }

    def _evaluate_rule(self, rule: Rule, context: dict[str, Any]) -> tuple[bool, str, float]:
        if not rule.conditions:
            return True, rule.description or "Regula bez warunkow pasuje.", 1.0
        evaluations = [self._evaluate_condition(condition, context) for condition in rule.conditions]
        if rule.combine == "or":
            matched = any(result for result, _ in evaluations)
            score = sum(1 for result, _ in evaluations if result) / len(evaluations)
        elif rule.combine == "weighted":
            total_weight = sum(max(0.0, condition.weight) for condition in rule.conditions) or 1.0
            score = sum(condition.weight for condition, (result, _) in zip(rule.conditions, evaluations) if result) / total_weight
            matched = score >= (rule.threshold if rule.threshold is not None else 0.7)
        else:
            matched = all(result for result, _ in evaluations)
            score = sum(1 for result, _ in evaluations if result) / len(evaluations)
        details = "; ".join(reason for _, reason in evaluations)
        reason = rule.description or details
        if not matched:
            reason = f"Nie spelniono: {details}"
        if rule.confidence_threshold is not None:
            confidence = float(context.get("campaign_confidence", score) or 0)
            matched = matched and confidence >= rule.confidence_threshold
        min_evidence = int(context.get("evidence_count", 0) or 0)
        if rule.min_evidence:
            matched = matched and min_evidence >= rule.min_evidence
        return matched, reason, score

    def _evaluate_condition(self, condition: Condition, context: dict[str, Any]) -> tuple[bool, str]:
        actual = context.get(condition.signal)
        expected = condition.value
        op = condition.operator
        if op == "exists":
            result = actual is not None and actual is not False and actual != ""
        elif op == "missing":
            result = actual is None or actual is False or actual == ""
        elif op == "eq":
            result = actual == expected
        elif op == "neq":
            result = actual != expected
        elif op == "in":
            result = actual in expected
        elif op == "contains":
            result = expected in (actual or [])
        elif op in {"gte", "gt", "lte", "lt"} and actual is None:
            result = False
        elif op == "gte":
            result = float(actual) >= float(expected)
        elif op == "gt":
            result = float(actual) > float(expected)
        elif op == "lte":
            result = float(actual) <= float(expected)
        elif op == "lt":
            result = float(actual) < float(expected)
        else:
            raise ValueError(f"Unsupported operator: {op}")
        return result, f"{condition.signal} {op} {expected} (actual={actual})"

    def _normalize_action(self, decision: str) -> DecisionAction:
        if decision in {"skip_t2", "skip_t2_manual_review"}:
            return DecisionAction.MANUAL_REVIEW if decision.endswith("manual_review") else DecisionAction.SKIP
        return DecisionAction(decision)

    def _render_subject(self, template: str | None, lead: Lead, campaign: CampaignKey | None) -> str | None:
        if not template:
            return None
        firma = lead.company_name or lead.normalized_domain
        return template.format(firma=firma, domena=lead.normalized_domain, campaign=campaign.value if campaign else "")
