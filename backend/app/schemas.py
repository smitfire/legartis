from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def _extract_value(v: Any) -> Any:
    """Pydantic ``before`` validator that pulls ``.value`` off an ORM ClauseType.

    Lets us keep the wire field name ``clause_type: str`` while the SQLAlchemy
    Label exposes ``clause_type`` as a joined relationship returning a
    ``ClauseType`` row. Pass-through for plain strings so the same DTO works in
    request shapes and other code paths.
    """
    return getattr(v, "value", v)


class LabelOut(BaseModel):
    """API view of a single clause-type annotation."""

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
        return _extract_value(v)


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
