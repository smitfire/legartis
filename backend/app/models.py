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


class Base(DeclarativeBase):
    pass


class ClauseType(Base):
    """A clause category that users (and, later, the AI) can apply to sentences.

    Dynamic row in the ``clause_types`` table — replaces the old closed
    ``ClauseType`` StrEnum. ``value`` is the immutable machine identifier
    (e.g. ``governing_law``) referenced over the wire; ``label`` is the
    human-readable display name and is the only field that can be edited.
    """

    __tablename__ = "clause_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Document(Base):
    """An uploaded contract, stored verbatim with its segmented sentences."""

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
    """One sentence inside a document; ``position`` is unique per document."""

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


class Label(Base):
    """A clause-type annotation on a sentence.

    A sentence may carry at most one label per ``clause_type_id`` (enforced
    by ``uq_label_sentence_clausetype``); the router translates that
    conflict into HTTP 409. ``source`` distinguishes ``MANUAL`` from
    future ``AUTO`` labels and is the seam where automated classification
    would plug in.
    """

    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("sentence_id", "clause_type_id", name="uq_label_sentence_clausetype"),
        CheckConstraint("source IN ('MANUAL', 'AUTO')", name="ck_label_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sentence_id: Mapped[int] = mapped_column(
        ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_type_id: Mapped[int] = mapped_column(
        ForeignKey("clause_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default="MANUAL")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sentence: Mapped[Sentence] = relationship(back_populates="labels")
    clause_type: Mapped[ClauseType] = relationship(lazy="joined")
