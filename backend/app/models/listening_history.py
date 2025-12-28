"""Listening history model."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
    from app.models.song import Song
    from app.models.user import User


class ContextType(str, enum.Enum):
    """Context type enum."""

    LIBRARY = "library"
    PLAYLIST = "playlist"
    MOOD_CHAIN = "mood_chain"
    SEARCH = "search"
    RECOMMENDATION = "recommendation"


class ListeningHistory(Base, UUIDMixin):
    """Listening history model."""

    __tablename__ = "listening_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    song_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("songs.id", ondelete="CASCADE"),
        nullable=False,
    )
    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    played_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    context_type: Mapped[ContextType | None] = mapped_column(
        Enum(ContextType),
        nullable=True,
    )
    context_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    previous_song_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("songs.id", ondelete="SET NULL"),
        nullable=True,
    )
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="listening_history")
    song: Mapped["Song"] = relationship(
        "Song",
        back_populates="listening_history",
        foreign_keys=[song_id],
    )
    previous_song: Mapped["Song | None"] = relationship(
        "Song",
        foreign_keys=[previous_song_id],
    )

    __table_args__ = (
        Index("ix_listening_history_user_played", "user_id", "played_at"),
        Index("ix_listening_history_user_song", "user_id", "song_id"),
        Index("ix_listening_history_song_played", "song_id", "played_at"),
        Index(
            "ix_listening_history_user_context",
            "user_id",
            "context_type",
            "context_id",
        ),
        Index(
            "ix_listening_history_transitions",
            "previous_song_id",
            "song_id",
        ),
    )
