import unicodedata
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.deps import DbSession
from app.models import ClauseType, Document, Label, Sentence
from app.slugify import slugify

router = APIRouter(tags=["clause-types"])

_MAX_COLLISION_SUFFIX = 50


def _validate_label(v: str) -> str:
    """Reject labels that would corrupt the dashboard render.

    ``Field(min_length=1)`` accepts ``"   "`` because it counts whitespace;
    that label slugifies to ``""`` and we fall back to ``"clause_type"``,
    polluting the taxonomy with effectively-blank rows. Strip first, then
    enforce that the slug has at least one alphanumeric.

    Also reject invisible / formatting characters (zero-width spaces,
    RTL/LRO directional overrides, BOM, control chars). Angular's
    interpolation is XSS-safe, but these chars hide content or flip
    rendering direction in chips and tables.
    """
    stripped = v.strip()
    if not stripped:
        raise ValueError("label cannot be empty or whitespace-only")
    for ch in stripped:
        cat = unicodedata.category(ch)
        # Cc = control, Cf = format (incl. ZWSP, RLO, BOM), Cs = surrogate,
        # Co = private use, Cn = unassigned, Zl/Zp = line/paragraph separators.
        if cat.startswith("C") or cat in ("Zl", "Zp"):
            raise ValueError("label contains a disallowed control or formatting character")
    if not slugify(stripped):
        raise ValueError("label must contain at least one alphanumeric character")
    return stripped


class ClauseTypeCreate(BaseModel):
    """Incoming payload for creating a clause type. ``value`` is derived server-side."""

    model_config = ConfigDict(extra="forbid")

    label: Annotated[str, Field(min_length=1, max_length=200), AfterValidator(_validate_label)]


class ClauseTypeUpdate(BaseModel):
    """Patch payload. Only ``label`` is editable; ``value`` is immutable by design."""

    model_config = ConfigDict(extra="forbid")

    label: Annotated[str, Field(min_length=1, max_length=200), AfterValidator(_validate_label)]


class ClauseTypeOption(BaseModel):
    """Dropdown entry: machine value plus human label."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    value: str
    label: str


class ClauseTypeCount(ClauseTypeOption):
    """Dashboard facet: a clause type with the number of documents that use it."""

    count: int


def _is_value_uniqueness_violation(exc: IntegrityError) -> bool:
    """True if ``exc`` is a uniqueness clash on ``clause_types.value``.

    Matches the constraint name (Postgres) or the qualified column phrase
    (SQLite) explicitly — a generic ``"unique" in cause`` would also match
    a future unique on ``label``, since Postgres always phrases unique
    violations as "duplicate key value violates unique constraint ..." and
    that "value" is the literal keyword, not the column name.
    """
    cause = str(getattr(exc, "orig", exc)).lower()
    return "uq_clause_types_value" in cause or "clause_types.value" in cause


async def _insert_with_value_suffix(db: DbSession, label: str) -> ClauseType:
    """Insert a new ClauseType, suffixing ``value`` on uniqueness clashes.

    Tries the bare slug first, then ``_2``, ``_3``, … up to
    ``_MAX_COLLISION_SUFFIX``. The label is stored verbatim every time so
    users see the name they typed.
    """
    base = slugify(label) or "clause_type"
    candidates = [base] + [f"{base}_{n}" for n in range(2, _MAX_COLLISION_SUFFIX + 1)]
    for candidate in candidates:
        clause_type = ClauseType(value=candidate, label=label)
        db.add(clause_type)
        try:
            await db.commit()
        except IntegrityError as exc:
            await db.rollback()
            if not _is_value_uniqueness_violation(exc):
                raise
            continue
        await db.refresh(clause_type)
        return clause_type
    raise HTTPException(
        status.HTTP_409_CONFLICT,
        detail=f"Could not find a free value derived from {label!r} after "
        f"{_MAX_COLLISION_SUFFIX} attempts.",
    )


@router.get("/clause-types")
async def list_clause_types(db: DbSession) -> list[ClauseTypeOption]:
    """Return every clause type currently registered, ordered by id."""
    rows = (await db.scalars(select(ClauseType).order_by(ClauseType.id))).all()
    return [ClauseTypeOption.model_validate(ct) for ct in rows]


@router.post("/clause-types", status_code=status.HTTP_201_CREATED)
async def create_clause_type(payload: ClauseTypeCreate, db: DbSession) -> ClauseTypeOption:
    """Create a new clause type with a slugified ``value`` derived from ``label``.

    Duplicate slugs are auto-resolved with a numeric suffix (``_2``, ``_3``, …)
    so the UX never blocks the user on a collision.
    """
    return ClauseTypeOption.model_validate(await _insert_with_value_suffix(db, payload.label))


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
    return ClauseTypeOption.model_validate(clause_type)


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
    counts_by_id: dict[int, int] = {ct_id: count for ct_id, count in (await db.execute(stmt)).all()}
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
