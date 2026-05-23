from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONB, list[dict[str, Any]]: JSONB, list[str]: JSONB}


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class LeadRow(TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_normalized_domain", "normalized_domain"),
        Index("ix_leads_nip", "nip"),
        Index("ix_leads_status", "status"),
        Index("ix_leads_batch_id", "batch_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("batches.id"), nullable=True)
    input_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    registered_domain: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(2048))
    company_name: Mapped[str | None] = mapped_column(String(255))
    nip: Mapped[str | None] = mapped_column(String(10))
    source: Mapped[str | None] = mapped_column(String(100))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    batch: Mapped["BatchRow | None"] = relationship(back_populates="leads")
    scan_results: Mapped[list["ScanResultRow"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    decisions: Mapped[list["CampaignDecisionRow"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    outreach_events: Mapped[list["OutreachEventRow"]] = relationship(back_populates="lead", cascade="all, delete-orphan")


class BatchRow(TimestampMixin, Base):
    __tablename__ = "batches"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="created")
    imported_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    leads: Mapped[list[LeadRow]] = relationship(back_populates="batch")


class ScanResultRow(TimestampMixin, Base):
    __tablename__ = "scan_results"
    __table_args__ = (Index("ix_scan_results_lead_id", "lead_id"), Index("ix_scan_results_status", "status"))

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    layer: Mapped[str] = mapped_column(String(20), nullable=False, default="t0")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    http_status: Mapped[int | None] = mapped_column(Integer)
    final_url: Mapped[str | None] = mapped_column(String(2048))
    signals: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    raw_snapshot_path: Mapped[str | None] = mapped_column(String(2048))
    error: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    lead: Mapped[LeadRow] = relationship(back_populates="scan_results")
    decisions: Mapped[list["CampaignDecisionRow"]] = relationship(back_populates="scan_result")


class DecisionTraceRow(Base):
    __tablename__ = "decision_traces"
    __table_args__ = (Index("ix_decision_traces_lead_id", "lead_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    ruleset_version: Mapped[str] = mapped_column(String(80), nullable=False)
    evaluated_rules: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    winning_rule: Mapped[str | None] = mapped_column(String(120))
    blocked_by: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    decisions: Mapped[list["CampaignDecisionRow"]] = relationship(back_populates="decision_trace")


class CampaignDecisionRow(Base):
    __tablename__ = "campaign_decisions"
    __table_args__ = (
        Index("ix_campaign_decisions_lead_id", "lead_id"),
        Index("ix_campaign_decisions_status", "action"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    scan_result_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("scan_results.id"))
    decision_trace_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("decision_traces.id"))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    campaign: Mapped[str | None] = mapped_column(String(80))
    subject: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    ruleset_version: Mapped[str] = mapped_column(String(80), nullable=False)
    rule_key: Mapped[str | None] = mapped_column(String(120))
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lead: Mapped[LeadRow] = relationship(back_populates="decisions")
    scan_result: Mapped[ScanResultRow | None] = relationship(back_populates="decisions")
    decision_trace: Mapped[DecisionTraceRow | None] = relationship(back_populates="decisions")
    outreach_events: Mapped[list["OutreachEventRow"]] = relationship(back_populates="campaign_decision")


class OutreachEventRow(Base):
    __tablename__ = "outreach_events"
    __table_args__ = (
        Index("ix_outreach_events_lead_id", "lead_id"),
        Index("ix_outreach_events_decision_id", "campaign_decision_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    campaign_decision_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("campaign_decisions.id"))
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    lead: Mapped[LeadRow] = relationship(back_populates="outreach_events")
    campaign_decision: Mapped[CampaignDecisionRow | None] = relationship(back_populates="outreach_events")


class SuppressionEntryRow(Base):
    __tablename__ = "suppression_entries"
    __table_args__ = (
        Index("ix_suppression_scope_value", "scope", "value"),
        Index("ix_suppression_active", "active"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    permanent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str | None] = mapped_column(String(100))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)


def create_engine(database_url: str, **kwargs: Any) -> AsyncEngine:
    return create_async_engine(database_url, **kwargs)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)
