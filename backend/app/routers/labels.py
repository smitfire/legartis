from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from app.clause_types import ClauseType
from app.deps import DbSession
from app.models import Label, Sentence
from app.schemas import LabelOut

router = APIRouter(tags=["labels"])


class LabelCreate(BaseModel):
    clause_type: ClauseType
    source: str = "MANUAL"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


@router.post(
    "/sentences/{sentence_id}/labels",
    status_code=status.HTTP_201_CREATED,
    response_model=LabelOut,
)
async def create_label(sentence_id: int, payload: LabelCreate, db: DbSession) -> Label:
    sentence = await db.get(Sentence, sentence_id)
    if sentence is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sentence not found")

    label = Label(
        sentence_id=sentence_id,
        clause_type=payload.clause_type.value,
        source=payload.source,
        confidence=payload.confidence,
    )
    db.add(label)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        # Discriminate uniqueness violations from other constraint failures so we
        # don't tell callers "duplicate label" when it was actually a CHECK or FK
        # violation (which would mean a bug, not a duplicate).
        cause = str(getattr(exc, "orig", exc)).lower()
        if "unique" in cause or "uq_label_sentence_clausetype" in cause:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Sentence is already labelled with this clause type.",
            ) from exc
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Label violates a database constraint.",
        ) from exc

    await db.refresh(label)
    return label


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(label_id: int, db: DbSession) -> Response:
    label = await db.get(Label, label_id)
    if label is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Label not found")
    await db.delete(label)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
