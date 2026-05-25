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
