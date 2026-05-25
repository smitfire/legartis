from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.clause_types import CLAUSE_TYPE_LABELS, ClauseType
from app.deps import DbSession
from app.models import Document, Label, Sentence

router = APIRouter(tags=["clause-types"])


class ClauseTypeOption(BaseModel):
    value: ClauseType
    label: str


class ClauseTypeCount(BaseModel):
    value: ClauseType
    label: str
    count: int


@router.get("/clause-types", response_model=list[ClauseTypeOption])
def list_clause_types() -> list[ClauseTypeOption]:
    return [ClauseTypeOption(value=ct, label=label) for ct, label in CLAUSE_TYPE_LABELS.items()]


@router.get("/clause-type-counts", response_model=list[ClauseTypeCount])
async def list_clause_type_counts(
    db: DbSession,
    q: Annotated[
        str | None,
        Query(description="Restrict counts to documents whose title or content matches q"),
    ] = None,
) -> list[ClauseTypeCount]:
    stmt = (
        select(Label.clause_type, func.count(func.distinct(Sentence.document_id)))
        .join(Sentence, Sentence.id == Label.sentence_id)
        .group_by(Label.clause_type)
    )
    if q:
        needle = q.lower()
        stmt = stmt.join(Document, Document.id == Sentence.document_id).where(
            or_(
                func.lower(Document.title).contains(needle),
                func.lower(Document.content).contains(needle),
            )
        )
    rows = (await db.execute(stmt)).all()
    counts_map: dict[str, int] = {clause_type: count for clause_type, count in rows}
    return [
        ClauseTypeCount(value=ct, label=label, count=counts_map.get(ct.value, 0))
        for ct, label in CLAUSE_TYPE_LABELS.items()
    ]
