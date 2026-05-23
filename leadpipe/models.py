from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        populate_by_name=True,
        validate_assignment=True,
        json_schema_extra={"examples": []},
    )


class LeadStatus(str, Enum):
    NEW = "new"
    SCANNED = "scanned"
    DECIDED = "decided"
    EXPORTED = "exported"
    SUPPRESSED = "suppressed"
    SKIPPED = "skipped"


class ScanStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class SignalSource(str, Enum):
    IMPORT = "import"
    T0 = "t0"
    T0_5 = "t0_5"
    T1 = "t1"
    T2 = "t2"
    FEEDBACK = "feedback"


class EvidenceType(str, Enum):
    HTTP = "http"
    DNS = "dns"
    TLS = "tls"
    HTML = "html"
    CONTACT = "contact"
    BUSINESS = "business"
    VISUAL = "visual"
    FEEDBACK = "feedback"
    MANUAL = "manual"


class DecisionAction(str, Enum):
    SKIP = "skip"
    RETRY = "retry"
    MANUAL_REVIEW = "manual_review"
    T2_REQUIRED = "t2_required"
    T2_OPTIONAL = "t2_optional"
    SEND = "send"


class CampaignKey(str, Enum):
    REDESIGN_OUTDATED = "REDESIGN_OUTDATED"
    REDESIGN_ADS_WASTE = "REDESIGN_ADS_WASTE"
    REDESIGN_CONVERSION = "REDESIGN_CONVERSION"
    REDESIGN_TRUST = "REDESIGN_TRUST"
    WORDPRESS_REWORK = "WORDPRESS_REWORK"
    MOBILE_REBUILD = "MOBILE_REBUILD"
    TECH_REBUILD = "TECH_REBUILD"


class OutreachEventType(str, Enum):
    SENT = "sent"
    OPEN = "open"
    REPLY = "reply"
    POSITIVE_REPLY = "positive_reply"
    MEETING = "meeting"
    SOFT_BOUNCE = "soft_bounce"
    HARD_BOUNCE = "hard_bounce"
    OPT_OUT = "opt_out"
    MANUAL_REJECT = "manual_reject"


class SuppressionScope(str, Enum):
    EMAIL = "email"
    DOMAIN = "domain"
    NIP = "nip"
    PHONE = "phone"
    LEAD = "lead"
    BATCH = "batch"


class BatchStatus(str, Enum):
    CREATED = "created"
    IMPORTING = "importing"
    READY = "ready"
    SCANNING = "scanning"
    DECIDING = "deciding"
    EXPORTED = "exported"
    FAILED = "failed"


class RuleEvaluation(StrictModel):
    rule_key: str = Field(min_length=1)
    result: bool
    reason: str = Field(default="", max_length=1000)
    decision: str | None = None
    score: float | None = None


class ScoreBreakdown(StrictModel):
    evidence_strength: float = Field(default=0, ge=0, le=100)
    signal_confidence: float = Field(default=0, ge=0, le=100)
    contactability: float = Field(default=0, ge=0, le=100)
    industry_fit: float = Field(default=0, ge=0, le=100)
    lead_value: float = Field(default=0, ge=0, le=100)
    penalties: float = Field(default=0, ge=0)

    @property
    def campaign_score(self) -> float:
        return max(
            0.0,
            0.45 * self.evidence_strength
            + 0.20 * self.signal_confidence
            + 0.15 * self.contactability
            + 0.15 * self.industry_fit
            + 0.05 * self.lead_value
            - self.penalties,
        )


class Lead(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "input_domain": "https://www.example.pl/",
                    "normalized_domain": "example.pl",
                    "company_name": "Example Sp. z o.o.",
                    "nip": "1234563218",
                    "source": "sample",
                    "contact_email": "biuro@example.pl",
                }
            ]
        },
    )

    id: UUID = Field(default_factory=uuid4)
    batch_id: UUID | None = None
    input_domain: str = Field(min_length=1, max_length=255)
    normalized_domain: str = Field(min_length=1, max_length=255)
    registered_domain: str | None = Field(default=None, max_length=255)
    url: HttpUrl | None = None
    company_name: str | None = Field(default=None, max_length=255)
    nip: str | None = Field(default=None, pattern=r"^\d{10}$")
    source: str | None = Field(default=None, max_length=100)
    contact_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    status: LeadStatus = LeadStatus.NEW
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @field_validator("normalized_domain", "registered_domain")
    @classmethod
    def domain_lowercase(cls, value: str | None) -> str | None:
        return value.lower().strip().removeprefix("www.") if value else value

    @field_validator("nip", mode="before")
    @classmethod
    def normalize_nip(cls, value: Any) -> str | None:
        return "".join(ch for ch in str(value) if ch.isdigit()) if value else value


class Signal(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    lead_id: UUID | None = None
    key: str = Field(min_length=1, max_length=120)
    value: bool | int | float | str | list[str] | dict[str, Any] | None
    source: SignalSource
    confidence: float = Field(default=1.0, ge=0, le=1)
    evidence_ids: list[UUID] = Field(default_factory=list)
    observed_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    lead_id: UUID | None = None
    scan_result_id: UUID | None = None
    type: EvidenceType
    key: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=2000)
    source_url: HttpUrl | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)
    captured_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScanResult(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    lead_id: UUID
    status: ScanStatus
    layer: SignalSource = SignalSource.T0
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
    http_status: int | None = Field(default=None, ge=100, le=599)
    final_url: HttpUrl | None = None
    signals: list[Signal] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    raw_snapshot_path: str | None = None
    error: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecisionTrace(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    lead_id: UUID | None = None
    ruleset_version: str = Field(min_length=1)
    evaluated_rules: list[RuleEvaluation] = Field(default_factory=list)
    winning_rule: str | None = None
    blocked_by: list[str] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    decision_reason: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=utcnow)


class CampaignDecision(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    lead_id: UUID
    scan_result_id: UUID | None = None
    decision_trace_id: UUID | None = None
    action: DecisionAction
    campaign: CampaignKey | None = None
    subject: str | None = Field(default=None, max_length=255)
    confidence: float = Field(default=0, ge=0, le=1)
    decision_reason: str = Field(default="", max_length=2000)
    evidence_ids: list[UUID] = Field(default_factory=list)
    ruleset_version: str = Field(min_length=1)
    rule_key: str | None = None
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    @model_validator(mode="after")
    def send_requires_campaign(self) -> CampaignDecision:
        if self.action == DecisionAction.SEND and self.campaign is None:
            raise ValueError("send decision requires campaign")
        return self


class OutreachEvent(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    lead_id: UUID
    campaign_decision_id: UUID | None = None
    event: OutreachEventType
    email: EmailStr | None = None
    occurred_at: datetime = Field(default_factory=utcnow)
    provider_message_id: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SuppressionEntry(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    scope: SuppressionScope
    value: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=1000)
    active: bool = True
    permanent: bool = False
    starts_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime | None = None
    source: str | None = Field(default=None, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Batch(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=120)
    source: str | None = Field(default=None, max_length=100)
    status: BatchStatus = BatchStatus.CREATED
    imported_count: int = Field(default=0, ge=0)
    accepted_count: int = Field(default=0, ge=0)
    rejected_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None


class ImportRecord(StrictModel):
    row_number: int = Field(ge=1)
    domain: str = Field(min_length=1, max_length=255)
    url: HttpUrl | None = None
    company_name: str | None = Field(default=None, max_length=255)
    nip: str | None = Field(default=None, pattern=r"^\d{10}$")
    source: str | None = Field(default=None, max_length=100)
    contact_email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=2000)
    valid: bool = True
    errors: list[str] = Field(default_factory=list)

    @field_validator("domain")
    @classmethod
    def normalize_domain_value(cls, value: str) -> str:
        return value.strip().lower().removeprefix("http://").removeprefix("https://").strip("/")
