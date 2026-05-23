from __future__ import annotations

from uuid import UUID

from .models import DecisionTrace as DecisionTraceModel
from .models import RuleEvaluation, ScoreBreakdown
from .ruleset import CURRENT_RULESET_VERSION


class DecisionTrace:
    """Mutable builder for the auditable decision trace contract."""

    def __init__(self, lead_id: UUID | None = None, ruleset_version: str = CURRENT_RULESET_VERSION) -> None:
        self.lead_id = lead_id
        self.ruleset_version = ruleset_version
        self.evaluated_rules: list[RuleEvaluation] = []
        self.winning_rule: str | None = None
        self.blocked_by: list[str] = []
        self.score_breakdown = ScoreBreakdown()

    def record_rule(self, rule_key: str, result: bool, reason: str, decision: str | None = None, score: float | None = None) -> None:
        self.evaluated_rules.append(
            RuleEvaluation(rule_key=rule_key, result=result, reason=reason, decision=decision, score=score)
        )

    def set_winning_rule(self, rule_key: str | None) -> None:
        self.winning_rule = rule_key

    def block(self, rule_key: str) -> None:
        if rule_key not in self.blocked_by:
            self.blocked_by.append(rule_key)

    def set_score_breakdown(
        self,
        *,
        evidence_strength: float,
        signal_confidence: float,
        contactability: float,
        industry_fit: float,
        lead_value: float,
        penalties: float = 0,
    ) -> None:
        self.score_breakdown = ScoreBreakdown(
            evidence_strength=evidence_strength,
            signal_confidence=signal_confidence,
            contactability=contactability,
            industry_fit=industry_fit,
            lead_value=lead_value,
            penalties=penalties,
        )

    def decision_reason(self, action: str | None = None, campaign: str | None = None) -> str:
        if self.blocked_by:
            return f"Lead zablokowany przez reguly: {', '.join(self.blocked_by)}."
        if action in {"t2_required", "t2_optional"}:
            return "Potrzebna jest ocena wizualna, bo dane techniczne i kontaktowe nie rozstrzygaja bezpiecznie kampanii."
        if action == "send" and campaign:
            score = round(self.score_breakdown.campaign_score, 1)
            return f"Wybrano kampanie {campaign}, bo dowody i dopasowanie daja wynik {score}/100."
        if action == "manual_review":
            return "Lead wymaga recznego sprawdzenia, bo automatyczne reguly nie daja wystarczajacej pewnosci."
        if action == "retry":
            return "Skan wymaga ponowienia z powodu przejsciowego bledu technicznego."
        if action == "skip":
            return "Lead pominiety przez reguly jakosci danych, dopasowania albo compliance."
        return "Decyzja zapisana na podstawie jawnych regul rulesetu."

    def to_model(self, action: str | None = None, campaign: str | None = None) -> DecisionTraceModel:
        return DecisionTraceModel(
            lead_id=self.lead_id,
            ruleset_version=self.ruleset_version,
            evaluated_rules=self.evaluated_rules,
            winning_rule=self.winning_rule,
            blocked_by=self.blocked_by,
            score_breakdown=self.score_breakdown,
            decision_reason=self.decision_reason(action, campaign),
        )
