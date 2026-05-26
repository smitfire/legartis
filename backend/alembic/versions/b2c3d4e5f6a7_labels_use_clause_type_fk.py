"""replace labels.clause_type text + CHECK with FK to clause_types

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-26 15:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Pre-flight: the backfill below produces NULL for any orphan label whose
    # clause_type text does not exist in clause_types. The previous CHECK
    # constraint + seed migration make this impossible in practice, but a
    # mismatch here would surface as an opaque NOT NULL violation on the
    # subsequent ALTER. Fail loudly with the offending values instead.
    bind = op.get_bind()
    orphans = bind.execute(
        sa.text(
            "SELECT DISTINCT labels.clause_type FROM labels "
            "WHERE labels.clause_type NOT IN (SELECT value FROM clause_types)"
        )
    ).scalars().all()
    if orphans:
        raise RuntimeError(
            f"Cannot migrate labels: {len(orphans)} clause_type value(s) have no "
            f"row in clause_types: {sorted(orphans)!r}. Insert them into "
            f"clause_types before re-running this migration."
        )

    # Add the FK column as nullable so we can backfill from the existing text column.
    op.add_column("labels", sa.Column("clause_type_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE labels "
        "SET clause_type_id = (SELECT id FROM clause_types WHERE value = labels.clause_type)"
    )
    op.alter_column("labels", "clause_type_id", nullable=False)

    op.drop_constraint("uq_label_sentence_clausetype", "labels", type_="unique")
    op.drop_constraint("ck_label_clause_type", "labels", type_="check")
    op.drop_column("labels", "clause_type")

    op.create_foreign_key(
        "fk_labels_clause_type_id",
        "labels",
        "clause_types",
        ["clause_type_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_labels_clause_type_id", "labels", ["clause_type_id"], unique=False
    )
    op.create_unique_constraint(
        "uq_label_sentence_clausetype", "labels", ["sentence_id", "clause_type_id"]
    )


def downgrade() -> None:
    op.add_column("labels", sa.Column("clause_type", sa.Text(), nullable=True))
    op.execute(
        "UPDATE labels "
        "SET clause_type = (SELECT value FROM clause_types WHERE id = labels.clause_type_id)"
    )
    op.alter_column("labels", "clause_type", nullable=False)

    op.drop_constraint("uq_label_sentence_clausetype", "labels", type_="unique")
    op.drop_index("ix_labels_clause_type_id", table_name="labels")
    op.drop_constraint("fk_labels_clause_type_id", "labels", type_="foreignkey")
    op.drop_column("labels", "clause_type_id")

    op.create_check_constraint(
        "ck_label_clause_type",
        "labels",
        "clause_type IN ('limitation_of_liability', 'termination_for_convenience', "
        "'non_compete', 'confidentiality', 'governing_law', 'indemnification', 'force_majeure')",
    )
    op.create_unique_constraint(
        "uq_label_sentence_clausetype", "labels", ["sentence_id", "clause_type"]
    )
