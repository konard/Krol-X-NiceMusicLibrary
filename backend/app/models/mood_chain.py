"""Mood chain models."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.song import Song
    from app.models.user import User


class TransitionStyle(str, enum.Enum):
    """Transition style enum."""

    SMOOTH = "smooth"
    RANDOM = "random"
    ENERGY_FLOW = "energy_flow"
    GENRE_MATCH = "genre_match"


class MoodChain(Base, UUIDMixin, TimestampMixin):
    """Mood chain model."""

    __tablename__ = "mood_chains"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mood_tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(255)),
        nullable=True,
    )
    cover_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_auto_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    source_history_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    source_history_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    transition_style: Mapped[TransitionStyle] = mapped_column(
        Enum(TransitionStyle),
        default=TransitionStyle.SMOOTH,
        nullable=False,
    )
    song_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_played_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="mood_chains")
    mood_chain_songs: Mapped[list["MoodChainSong"]] = relationship(
        "MoodChainSong",
        back_populates="mood_chain",
        cascade="all, delete-orphan",
        order_by="MoodChainSong.position",
    )

    __table_args__ = (
        Index("ix_mood_chains_owner_play_count", "owner_id", "play_count"),
    )


class MoodChainSong(Base, UUIDMixin):
    """Mood chain-Song association model."""

    __tablename__ = "mood_chain_songs"

    mood_chain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mood_chains.id", ondelete="CASCADE"),
        nullable=False,
    )
    song_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("songs.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    transition_weight: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    mood_chain: Mapped["MoodChain"] = relationship(
        "MoodChain", back_populates="mood_chain_songs"
    )
    song: Mapped["Song"] = relationship("Song", back_populates="mood_chain_songs")

    __table_args__ = (
        Index("ix_mood_chain_songs_position", "mood_chain_id", "position"),
        Index("ix_mood_chain_songs_chain_song", "mood_chain_id", "song_id"),
    )
