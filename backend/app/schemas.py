from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.clause_types import ClauseType


class LabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sentence_id: int
    clause_type: ClauseType
    source: str
    confidence: float | None = None
    created_at: datetime


class SentenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    text: str
    labels: list[LabelOut] = []


class DocumentOut(BaseModel):
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
    clause_types: list[ClauseType] = []


class DocumentGroup(BaseModel):
    clause_type: ClauseType
    documents: list[DocumentSummary]


class GroupedDocuments(BaseModel):
    groups: list[DocumentGroup]
