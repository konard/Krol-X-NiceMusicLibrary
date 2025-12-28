"""User model."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.listening_history import ListeningHistory
    from app.models.mood_chain import MoodChain
    from app.models.playlist import Playlist
    from app.models.song import Song
    from app.models.tag import Tag


class UserRole(str, enum.Enum):
    """User roles enum."""

    USER = "user"
    ADMIN = "admin"


class User(Base, UUIDMixin, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    songs: Mapped[list["Song"]] = relationship(
        "Song",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    playlists: Mapped[list["Playlist"]] = relationship(
        "Playlist",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    mood_chains: Mapped[list["MoodChain"]] = relationship(
        "MoodChain",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    listening_history: Mapped[list["ListeningHistory"]] = relationship(
        "ListeningHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
