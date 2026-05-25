from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.clause_types import CLAUSE_TYPE_LABELS, ClauseType
from app.deps import DbSession
from app.models import Document, Label, Sentence

router = APIRouter(tags=["clause-types"])


class ClauseTypeOption(BaseModel):
    """Dropdown entry: machine value plus human label."""

    value: ClauseType
    label: str


class ClauseTypeCount(BaseModel):
    """Dashboard facet: a clause type with the number of documents that use it."""

    value: ClauseType
    label: str
    count: int


@router.get("/clause-types")
def list_clause_types() -> list[ClauseTypeOption]:
    """Return every supported clause type with its display label."""
    return [ClauseTypeOption(value=ct, label=label) for ct, label in CLAUSE_TYPE_LABELS.items()]


@router.get("/clause-type-counts")
async def list_clause_type_counts(
    db: DbSession,
    q: Annotated[
        str | None,
        Query(description="Restrict counts to documents whose title or content matches q"),
    ] = None,
) -> list[ClauseTypeCount]:
    """Return per-clause-type document counts, optionally filtered by ``q``.

    Every clause type is present in the response; types with no matching
    documents are returned with ``count=0`` so the dashboard facet list is
    stable regardless of the current filter.
    """
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
    counts_by_type: dict[str, int] = {clause_type: count for clause_type, count in rows}
    return [
        ClauseTypeCount(value=ct, label=label, count=counts_by_type.get(ct.value, 0))
        for ct, label in CLAUSE_TYPE_LABELS.items()
    ]
