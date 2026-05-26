from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class LabelOut(BaseModel):
    """API view of a single clause-type annotation.

    The ``clause_type`` field is serialised as the machine ``value`` string,
    whether the source is a plain string or a joined ``ClauseType`` ORM row.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    sentence_id: int
    clause_type: str
    source: str
    confidence: float | None = None
    created_at: datetime

    @field_validator("clause_type", mode="before")
    @classmethod
    def _flatten_clause_type(cls, v: Any) -> Any:
        # Two intended inputs: a joined ClauseType ORM row (use its `.value`)
        # or a plain string (already the wire format). Anything else is a
        # programmer error — raise so it surfaces as a 500 / test failure
        # instead of silently serialising an int, dict, or None.
        from app.models import ClauseType

        if isinstance(v, ClauseType):
            return v.value
        if isinstance(v, str):
            return v
        raise TypeError(f"clause_type must be ClauseType or str, got {type(v).__name__}")


class SentenceOut(BaseModel):
    """Sentence plus its attached labels, as returned by the document detail view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    text: str
    labels: list[LabelOut] = []


class DocumentOut(BaseModel):
    """Full document payload with nested sentences and labels."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    uploaded_at: datetime
    sentences: list[SentenceOut] = []


class DocumentSummary(BaseModel):
    """Compact view of a document for the dashboard list."""

    id: int
    title: str
    uploaded_at: datetime
    sentence_count: int
    label_count: int
    clause_types: list[str] = []


class DocumentGroup(BaseModel):
    """A clause type and the documents that contain at least one label of it."""

    clause_type: str
    documents: list[DocumentSummary]


class GroupedDocuments(BaseModel):
    """Dashboard payload when ``group_by=type`` is requested."""

    groups: list[DocumentGroup]
