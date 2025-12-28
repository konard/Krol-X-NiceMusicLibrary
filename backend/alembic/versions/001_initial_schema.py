"""Initial schema with all entities.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'admin')")
    op.execute(
        "CREATE TYPE transitionstyle AS ENUM ('smooth', 'random', 'energy_flow', 'genre_match')"
    )
    op.execute(
        "CREATE TYPE contexttype AS ENUM ('library', 'playlist', 'mood_chain', 'search', 'recommendation')"
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column(
            "preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "role",
            postgresql.ENUM("user", "admin", name="userrole", create_type=False),
            nullable=False,
            server_default="user",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "last_login_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # Create songs table
    op.create_table(
        "songs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("artist", sa.String(255), nullable=True),
        sa.Column("album", sa.String(255), nullable=True),
        sa.Column("album_artist", sa.String(255), nullable=True),
        sa.Column("genre", sa.String(100), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("track_number", sa.Integer(), nullable=True),
        sa.Column("disc_number", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file_format", sa.String(20), nullable=False),
        sa.Column("bitrate", sa.Integer(), nullable=True),
        sa.Column("sample_rate", sa.Integer(), nullable=True),
        sa.Column("cover_art_path", sa.String(500), nullable=True),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("bpm", sa.Integer(), nullable=True),
        sa.Column("energy", sa.Float(), nullable=True),
        sa.Column("valence", sa.Float(), nullable=True),
        sa.Column("play_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_played_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_songs_owner_id", "songs", ["owner_id"])
    op.create_index("ix_songs_owner_artist", "songs", ["owner_id", "artist"])
    op.create_index("ix_songs_owner_album", "songs", ["owner_id", "album"])
    op.create_index("ix_songs_owner_genre", "songs", ["owner_id", "genre"])
    op.create_index("ix_songs_owner_play_count", "songs", ["owner_id", "play_count"])
    op.create_index("ix_songs_owner_last_played", "songs", ["owner_id", "last_played_at"])
    op.create_index("ix_songs_owner_favorite", "songs", ["owner_id", "is_favorite"])

    # Create playlists table
    op.create_table(
        "playlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_image_path", sa.String(500), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("song_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "total_duration_seconds", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_playlists_owner_id", "playlists", ["owner_id"])
    op.create_index("ix_playlists_owner_name", "playlists", ["owner_id", "name"])

    # Create playlist_songs table
    op.create_table(
        "playlist_songs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "playlist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("playlists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("playlist_id", "song_id", name="uq_playlist_song"),
    )
    op.create_index(
        "ix_playlist_songs_position", "playlist_songs", ["playlist_id", "position"]
    )

    # Create mood_chains table
    op.create_table(
        "mood_chains",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mood_tags", postgresql.ARRAY(sa.String(255)), nullable=True),
        sa.Column("cover_image_path", sa.String(500), nullable=True),
        sa.Column(
            "is_auto_generated", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("source_history_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_history_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "transition_style",
            postgresql.ENUM(
                "smooth",
                "random",
                "energy_flow",
                "genre_match",
                name="transitionstyle",
                create_type=False,
            ),
            nullable=False,
            server_default="smooth",
        ),
        sa.Column("song_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("play_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_played_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_mood_chains_owner_id", "mood_chains", ["owner_id"])
    op.create_index(
        "ix_mood_chains_owner_play_count", "mood_chains", ["owner_id", "play_count"]
    )

    # Create mood_chain_songs table
    op.create_table(
        "mood_chain_songs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mood_chain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mood_chains.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "transition_weight", sa.Float(), nullable=False, server_default="1.0"
        ),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_mood_chain_songs_position", "mood_chain_songs", ["mood_chain_id", "position"]
    )
    op.create_index(
        "ix_mood_chain_songs_chain_song",
        "mood_chain_songs",
        ["mood_chain_id", "song_id"],
    )

    # Create listening_history table
    op.create_table(
        "listening_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "played_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("played_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("skipped", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "context_type",
            postgresql.ENUM(
                "library",
                "playlist",
                "mood_chain",
                "search",
                "recommendation",
                name="contexttype",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("context_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "previous_song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("device_type", sa.String(50), nullable=True),
    )
    op.create_index(
        "ix_listening_history_user_played",
        "listening_history",
        ["user_id", "played_at"],
    )
    op.create_index(
        "ix_listening_history_user_song", "listening_history", ["user_id", "song_id"]
    )
    op.create_index(
        "ix_listening_history_song_played",
        "listening_history",
        ["song_id", "played_at"],
    )
    op.create_index(
        "ix_listening_history_user_context",
        "listening_history",
        ["user_id", "context_type", "context_id"],
    )
    op.create_index(
        "ix_listening_history_transitions",
        "listening_history",
        ["previous_song_id", "song_id"],
    )

    # Create tags table
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),
    )
    op.create_index("ix_tags_owner_name", "tags", ["owner_id", "name"])

    # Create song_tags table
    op.create_table(
        "song_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("song_id", "tag_id", name="uq_song_tag"),
    )
    op.create_index("ix_song_tags_tag", "song_tags", ["tag_id"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("song_tags")
    op.drop_table("tags")
    op.drop_table("listening_history")
    op.drop_table("mood_chain_songs")
    op.drop_table("mood_chains")
    op.drop_table("playlist_songs")
    op.drop_table("playlists")
    op.drop_table("songs")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS contexttype")
    op.execute("DROP TYPE IF EXISTS transitionstyle")
    op.execute("DROP TYPE IF EXISTS userrole")
