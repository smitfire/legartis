from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_db
from app.models import Document, Sentence
from app.schemas import DocumentOut
from app.segmentation import segment

router = APIRouter(prefix="/documents", tags=["documents"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _document_with_sentences_query(document_id: int) -> Select[tuple[Document]]:
    return (
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.sentences).selectinload(Sentence.labels))
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DocumentOut)
async def create_document(
    file: Annotated[UploadFile, File()],
    db: DbSession,
) -> Document:
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File must be UTF-8 encoded text.",
        ) from exc

    sentence_texts = segment(content)
    title = file.filename or "untitled"

    doc = Document(
        title=title,
        content=content,
        sentences=[Sentence(position=i, text=text) for i, text in enumerate(sentence_texts)],
    )

    db.add(doc)
    await db.commit()

    result = await db.execute(_document_with_sentences_query(doc.id))
    return result.scalar_one()


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: int, db: DbSession) -> Document:
    result = await db.execute(_document_with_sentences_query(document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc
