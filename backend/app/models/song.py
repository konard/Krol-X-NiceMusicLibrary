"""Song model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.listening_history import ListeningHistory
    from app.models.mood_chain import MoodChainSong
    from app.models.playlist import PlaylistSong
    from app.models.tag import SongTag
    from app.models.user import User


class Song(Base, UUIDMixin, TimestampMixin):
    """Song model."""

    __tablename__ = "songs"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    artist: Mapped[str | None] = mapped_column(String(255), nullable=True)
    album: Mapped[str | None] = mapped_column(String(255), nullable=True)
    album_artist: Mapped[str | None] = mapped_column(String(255), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    track_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disc_number: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)

    # Audio info
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    bitrate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_art_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Extended metadata
    lyrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    energy: Mapped[float | None] = mapped_column(Float, nullable=True)
    valence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Playback stats
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_played_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="songs")
    playlist_songs: Mapped[list["PlaylistSong"]] = relationship(
        "PlaylistSong",
        back_populates="song",
        cascade="all, delete-orphan",
    )
    mood_chain_songs: Mapped[list["MoodChainSong"]] = relationship(
        "MoodChainSong",
        back_populates="song",
        cascade="all, delete-orphan",
    )
    listening_history: Mapped[list["ListeningHistory"]] = relationship(
        "ListeningHistory",
        back_populates="song",
        cascade="all, delete-orphan",
        foreign_keys="ListeningHistory.song_id",
    )
    song_tags: Mapped[list["SongTag"]] = relationship(
        "SongTag",
        back_populates="song",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_songs_owner_artist", "owner_id", "artist"),
        Index("ix_songs_owner_album", "owner_id", "album"),
        Index("ix_songs_owner_genre", "owner_id", "genre"),
        Index("ix_songs_owner_play_count", "owner_id", "play_count"),
        Index("ix_songs_owner_last_played", "owner_id", "last_played_at"),
        Index("ix_songs_owner_favorite", "owner_id", "is_favorite"),
    )
