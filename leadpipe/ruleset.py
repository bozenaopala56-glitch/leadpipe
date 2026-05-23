from __future__ import annotations

from datetime import date
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field

CURRENT_RULESET_VERSION = "ruleset-2026-05-23-v1"


class RulesetVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    date: date
    changes: list[str] = Field(default_factory=list)

    @property
    def audit_hash(self) -> str:
        payload = f"{self.name}|{self.date.isoformat()}|{'|'.join(self.changes)}"
        return sha256(payload.encode("utf-8")).hexdigest()


def load_current_ruleset_version() -> RulesetVersion:
    return RulesetVersion(
        name=CURRENT_RULESET_VERSION,
        date=date(2026, 5, 23),
        changes=[
            "Initial MVP rules for T2 eligibility, gates, campaigns, suppression, evidence and feedback.",
            "DecisionTrace stores evaluated rules, winner, blockers and score breakdown.",
        ],
    )
