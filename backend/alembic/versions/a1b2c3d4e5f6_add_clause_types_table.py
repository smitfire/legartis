"""add clause_types table and seed the seven existing categories

Revision ID: a1b2c3d4e5f6
Revises: 15b40afa9006
Create Date: 2026-05-26 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "15b40afa9006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SEED_CLAUSE_TYPES: list[tuple[str, str]] = [
    ("limitation_of_liability", "Limitation of Liability"),
    ("termination_for_convenience", "Termination for Convenience"),
    ("non_compete", "Non-Compete"),
    ("confidentiality", "Confidentiality"),
    ("governing_law", "Governing Law"),
    ("indemnification", "Indemnification"),
    ("force_majeure", "Force Majeure"),
]


def upgrade() -> None:
    clause_types = op.create_table(
        "clause_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("value", name="uq_clause_types_value"),
    )
    op.bulk_insert(
        clause_types,
        [{"value": value, "label": label} for value, label in SEED_CLAUSE_TYPES],
    )


def downgrade() -> None:
    op.drop_table("clause_types")
