from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.deps import DbSession
from app.models import ClauseType, Label, Sentence
from app.schemas import LabelOut

router = APIRouter(tags=["labels"])


class LabelCreate(BaseModel):
    """Incoming payload for tagging a sentence with a clause type."""

    clause_type: str
    source: str = "MANUAL"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


@router.post(
    "/sentences/{sentence_id}/labels",
    status_code=status.HTTP_201_CREATED,
    response_model=LabelOut,
)
async def create_label(sentence_id: int, payload: LabelCreate, db: DbSession) -> Label:
    """Attach a clause-type label to a sentence.

    Returns 404 if the sentence does not exist, 409 if the sentence already
    carries this clause type (``uq_label_sentence_clausetype`` violation),
    and 422 if the clause type value is not registered in ``clause_types``.
    """
    sentence = await db.get(Sentence, sentence_id)
    if sentence is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sentence not found")

    clause_type = await db.scalar(select(ClauseType).where(ClauseType.value == payload.clause_type))
    if clause_type is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown clause type: {payload.clause_type!r}",
        )

    label = Label(
        sentence_id=sentence_id,
        clause_type_id=clause_type.id,
        source=payload.source,
        confidence=payload.confidence,
    )
    db.add(label)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        cause = str(getattr(exc, "orig", exc)).lower()
        if "uq_label_sentence_clausetype" in cause or "unique" in cause:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Sentence is already labelled with this clause type.",
            ) from exc
        if "foreign key" in cause or "fk_labels_clause_type_id" in cause:
            # Clause type was deleted between the lookup above and the commit.
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Clause type was removed before this label could be saved.",
            ) from exc
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Label violates a database constraint: {cause}",
        ) from exc

    refreshed = await db.scalar(
        select(Label).options(joinedload(Label.clause_type)).where(Label.id == label.id)
    )
    if refreshed is None:
        # We just committed a Label with this id inside the same session, so
        # this is unreachable unless the row was deleted from underneath us.
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Label was committed but could not be re-read.",
        )
    return refreshed


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(label_id: int, db: DbSession) -> Response:
    """Remove a label by id; 404 if it does not exist, 204 on success."""
    label = await db.get(Label, label_id)
    if label is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Label not found")
    await db.delete(label)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
