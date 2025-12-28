"""Tag models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.song import Song
    from app.models.user import User


class Tag(Base, UUIDMixin, TimestampMixin):
    """Tag model."""

    __tablename__ = "tags"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="tags")
    song_tags: Mapped[list["SongTag"]] = relationship(
        "SongTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),
        Index("ix_tags_owner_name", "owner_id", "name"),
    )


class SongTag(Base, UUIDMixin):
    """Song-Tag association model."""

    __tablename__ = "song_tags"

    song_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("songs.id", ondelete="CASCADE"),
        nullable=False,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    song: Mapped["Song"] = relationship("Song", back_populates="song_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="song_tags")

    __table_args__ = (
        UniqueConstraint("song_id", "tag_id", name="uq_song_tag"),
        Index("ix_song_tags_tag", "tag_id"),
    )
