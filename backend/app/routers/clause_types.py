from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.deps import DbSession
from app.models import ClauseType, Document, Label, Sentence
from app.slugify import slugify

router = APIRouter(tags=["clause-types"])


class ClauseTypeCreate(BaseModel):
    """Incoming payload for creating a clause type. ``value`` is derived server-side."""

    label: str = Field(min_length=1, max_length=200)


class ClauseTypeUpdate(BaseModel):
    """Patch payload. Only ``label`` is editable; ``value`` is immutable by design."""

    label: str = Field(min_length=1, max_length=200)


_MAX_COLLISION_SUFFIX = 50


async def _insert_with_value_suffix(db: DbSession, label: str) -> ClauseType:
    """Insert a new ClauseType, silently suffixing ``value`` on uniqueness clashes.

    The first attempt uses the bare slug; if that collides, ``_2``, ``_3``, …
    are tried up to ``_MAX_COLLISION_SUFFIX``. The label is stored verbatim
    in every case so users see the name they typed.
    """
    base = slugify(label) or "clause_type"
    for suffix in range(1, _MAX_COLLISION_SUFFIX + 1):
        candidate = base if suffix == 1 else f"{base}_{suffix}"
        clause_type = ClauseType(value=candidate, label=label)
        db.add(clause_type)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        await db.refresh(clause_type)
        return clause_type
    raise HTTPException(
        status.HTTP_409_CONFLICT,
        detail=f"Could not find a free value derived from {label!r} after "
        f"{_MAX_COLLISION_SUFFIX} attempts.",
    )


class ClauseTypeOption(BaseModel):
    """Dropdown entry: machine value plus human label."""

    id: int
    value: str
    label: str


class ClauseTypeCount(BaseModel):
    """Dashboard facet: a clause type with the number of documents that use it."""

    id: int
    value: str
    label: str
    count: int


@router.get("/clause-types")
async def list_clause_types(db: DbSession) -> list[ClauseTypeOption]:
    """Return every clause type currently registered, ordered by id."""
    stmt = select(ClauseType).order_by(ClauseType.id)
    return [
        ClauseTypeOption(id=ct.id, value=ct.value, label=ct.label)
        for ct in (await db.scalars(stmt)).all()
    ]


@router.post("/clause-types", status_code=status.HTTP_201_CREATED)
async def create_clause_type(payload: ClauseTypeCreate, db: DbSession) -> ClauseTypeOption:
    """Create a new clause type with a slugified ``value`` derived from ``label``.

    Duplicate slugs are auto-resolved with a numeric suffix (``_2``, ``_3``, …)
    so the UX never blocks the user on a collision.
    """
    clause_type = await _insert_with_value_suffix(db, payload.label)
    return ClauseTypeOption(id=clause_type.id, value=clause_type.value, label=clause_type.label)


@router.patch("/clause-types/{clause_type_id}")
async def update_clause_type(
    clause_type_id: int, payload: ClauseTypeUpdate, db: DbSession
) -> ClauseTypeOption:
    """Update the display ``label`` of an existing clause type; 404 if unknown."""
    clause_type = await db.get(ClauseType, clause_type_id)
    if clause_type is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Clause type not found")
    clause_type.label = payload.label
    await db.commit()
    await db.refresh(clause_type)
    return ClauseTypeOption(id=clause_type.id, value=clause_type.value, label=clause_type.label)


@router.delete("/clause-types/{clause_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clause_type(clause_type_id: int, db: DbSession) -> Response:
    """Delete a clause type; cascades to every label that referenced it."""
    clause_type = await db.get(ClauseType, clause_type_id)
    if clause_type is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Clause type not found")
    await db.delete(clause_type)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/clause-type-counts")
async def list_clause_type_counts(
    db: DbSession,
    q: Annotated[
        str | None,
        Query(description="Restrict counts to documents whose title or content matches q"),
    ] = None,
) -> list[ClauseTypeCount]:
    """Return per-clause-type document counts, optionally filtered by ``q``.

    Every registered clause type is present in the response; types with no
    matching documents come back with ``count=0`` so the dashboard facet list
    is stable regardless of the current filter.
    """
    stmt = (
        select(Label.clause_type_id, func.count(func.distinct(Sentence.document_id)))
        .join(Sentence, Sentence.id == Label.sentence_id)
        .group_by(Label.clause_type_id)
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
    counts_by_id: dict[int, int] = {clause_type_id: count for clause_type_id, count in rows}
    types = (await db.scalars(select(ClauseType).order_by(ClauseType.id))).all()
    return [
        ClauseTypeCount(
            id=ct.id,
            value=ct.value,
            label=ct.label,
            count=counts_by_id.get(ct.id, 0),
        )
        for ct in types
    ]
