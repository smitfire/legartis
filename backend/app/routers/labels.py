from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clause_types import ClauseType
from app.deps import get_db
from app.models import Label, Sentence
from app.schemas import LabelOut

router = APIRouter(tags=["labels"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


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
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Sentence is already labelled with this clause type.",
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
