from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.clause_types import ClauseType


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sentences: Mapped[list[Sentence]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Sentence.position",
    )


class Sentence(Base):
    __tablename__ = "sentences"
    __table_args__ = (UniqueConstraint("document_id", "position", name="uq_sentence_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped[Document] = relationship(back_populates="sentences")
    labels: Mapped[list[Label]] = relationship(
        back_populates="sentence",
        cascade="all, delete-orphan",
    )


# Static list of valid clause-type machine values. Generated from the StrEnum so it
# stays in sync — values are constants (not user input), so f-string interpolation
# into the CHECK clause is safe.
_VALID_CLAUSE_TYPES_SQL = ", ".join(f"'{ct.value}'" for ct in ClauseType)


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("sentence_id", "clause_type", name="uq_label_sentence_clausetype"),
        CheckConstraint(f"clause_type IN ({_VALID_CLAUSE_TYPES_SQL})", name="ck_label_clause_type"),
        CheckConstraint("source IN ('MANUAL', 'AUTO')", name="ck_label_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sentence_id: Mapped[int] = mapped_column(
        ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_type: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default="MANUAL")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sentence: Mapped[Sentence] = relationship(back_populates="labels")
