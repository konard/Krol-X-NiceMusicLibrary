"""Add mood chain transitions table and auto_advance fields.

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 00:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add auto_advance fields to mood_chains table
    op.add_column(
        "mood_chains",
        sa.Column("auto_advance", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "mood_chains",
        sa.Column(
            "auto_advance_delay_seconds",
            sa.Integer(),
            nullable=False,
            server_default="10",
        ),
    )

    # Create mood_chain_transitions table
    op.create_table(
        "mood_chain_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mood_chain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mood_chains.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("play_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # Create indexes
    op.create_index(
        "ix_mood_chain_transitions_chain_from",
        "mood_chain_transitions",
        ["mood_chain_id", "from_song_id"],
    )
    op.create_index(
        "ix_mood_chain_transitions_chain_from_to",
        "mood_chain_transitions",
        ["mood_chain_id", "from_song_id", "to_song_id"],
        unique=True,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "ix_mood_chain_transitions_chain_from_to", table_name="mood_chain_transitions"
    )
    op.drop_index(
        "ix_mood_chain_transitions_chain_from", table_name="mood_chain_transitions"
    )

    # Drop table
    op.drop_table("mood_chain_transitions")

    # Remove columns from mood_chains
    op.drop_column("mood_chains", "auto_advance_delay_seconds")
    op.drop_column("mood_chains", "auto_advance")
