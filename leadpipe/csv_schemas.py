from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Iterable, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, ValidationError, field_validator

from .models import OutreachEventType


class CsvModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ImportCsvSchema(CsvModel):
    domain: str = Field(min_length=1, max_length=255)
    url: HttpUrl | None = None
    company_name: str | None = Field(default=None, max_length=255)
    nip: str | None = Field(default=None, pattern=r"^\d{10}$")
    source: str | None = Field(default=None, max_length=100)
    contact_email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str) -> str:
        return value.strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").strip("/")

    @field_validator("nip", mode="before")
    @classmethod
    def normalize_nip(cls, value: object) -> str | None:
        return "".join(ch for ch in str(value) if ch.isdigit()) if value else None


class ExportCsvSchema(CsvModel):
    firma: str | None = None
    domena: str
    email: EmailStr | None = None
    telefon: str | None = None
    kampania: str | None = None
    subject: str | None = None
    evidence_1: str | None = None
    evidence_2: str | None = None
    evidence_3: str | None = None
    confidence: float = Field(ge=0, le=1)
    suppression_status: str = "clear"


class FeedbackCsvSchema(CsvModel):
    domain: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    event: OutreachEventType
    timestamp: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str) -> str:
        return value.strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").strip("/")


T = TypeVar("T", bound=CsvModel)


def _read_rows(path_or_text: str | Path) -> list[dict[str, str]]:
    if isinstance(path_or_text, Path) or Path(str(path_or_text)).exists():
        with Path(path_or_text).open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    return list(csv.DictReader(StringIO(str(path_or_text))))


def parse_csv(path_or_text: str | Path, schema: type[T]) -> tuple[list[T], list[tuple[int, list[str]]]]:
    records: list[T] = []
    errors: list[tuple[int, list[str]]] = []
    for row_number, row in enumerate(_read_rows(path_or_text), start=2):
        cleaned = {key: (value if value != "" else None) for key, value in row.items() if key}
        try:
            records.append(schema.model_validate(cleaned))
        except ValidationError as exc:
            errors.append((row_number, [err["msg"] for err in exc.errors()]))
    return records, errors


def dump_csv(records: Iterable[CsvModel]) -> str:
    rows = [record.model_dump(mode="json") for record in records]
    if not rows:
        return ""
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
