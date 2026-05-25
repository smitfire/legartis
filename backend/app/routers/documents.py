from typing import Annotated, Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import selectinload

from app.clause_types import ClauseType
from app.deps import DbSession
from app.models import Document, Label, Sentence
from app.schemas import DocumentGroup, DocumentOut, DocumentSummary, GroupedDocuments
from app.segmentation import segment

router = APIRouter(prefix="/documents", tags=["documents"])


def _document_with_sentences_query(document_id: int) -> Select[tuple[Document]]:
    return (
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.sentences).selectinload(Sentence.labels))
    )


def _to_summary(doc: Document) -> DocumentSummary:
    label_count = sum(len(s.labels) for s in doc.sentences)
    clause_types = sorted(
        {ClauseType(label.clause_type) for s in doc.sentences for label in s.labels}
    )
    return DocumentSummary(
        id=doc.id,
        title=doc.title,
        uploaded_at=doc.uploaded_at,
        sentence_count=len(doc.sentences),
        label_count=label_count,
        clause_types=clause_types,
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


@router.get("", response_model=None)
async def list_documents(
    db: DbSession,
    q: Annotated[str | None, Query(description="Case-insensitive text in title or content")] = None,
    type: Annotated[
        list[ClauseType] | None,
        Query(alias="type", description="Clause type filter; multi-select is OR'd"),
    ] = None,
    group_by: Annotated[Literal["type"] | None, Query()] = None,
) -> list[DocumentSummary] | GroupedDocuments:
    stmt = (
        select(Document)
        .options(selectinload(Document.sentences).selectinload(Sentence.labels))
        .order_by(Document.id)
    )

    if q:
        needle = q.lower()
        stmt = stmt.where(
            or_(
                func.lower(Document.title).contains(needle),
                func.lower(Document.content).contains(needle),
            )
        )

    if type:
        type_values = [ct.value for ct in type]
        stmt = (
            stmt.join(Sentence, Sentence.document_id == Document.id)
            .join(Label, Label.sentence_id == Sentence.id)
            .where(Label.clause_type.in_(type_values))
            .distinct()
        )

    docs = list((await db.execute(stmt)).scalars().unique().all())

    if group_by == "type":
        buckets: dict[str, list[DocumentSummary]] = {}
        for doc in docs:
            summary = _to_summary(doc)
            seen_in_doc: set[str] = set()
            for sentence in doc.sentences:
                for label in sentence.labels:
                    if label.clause_type in seen_in_doc:
                        continue
                    seen_in_doc.add(label.clause_type)
                    buckets.setdefault(label.clause_type, []).append(summary)
        return GroupedDocuments(
            groups=[
                DocumentGroup(clause_type=ClauseType(ct), documents=group_docs)
                for ct, group_docs in sorted(buckets.items())
            ]
        )

    return [_to_summary(doc) for doc in docs]


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(document_id: int, db: DbSession) -> Document:
    result = await db.execute(_document_with_sentences_query(document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc
