"""Tag service with business logic for tag management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.song import Song
from app.models.tag import SongTag, Tag
from app.schemas.tag import TagCreate, TagUpdate


class TagServiceError(Exception):
    """Base exception for tag service errors."""


class TagNotFoundError(TagServiceError):
    """Raised when tag is not found."""


class SongNotFoundError(TagServiceError):
    """Raised when song is not found."""


class TagAlreadyExistsError(TagServiceError):
    """Raised when tag with the same name already exists for user."""


class TagAlreadyOnSongError(TagServiceError):
    """Raised when tag is already on song."""


class TagNotOnSongError(TagServiceError):
    """Raised when tag is not on song."""


class TagService:
    """Service for managing tags."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize tag service.

        Args:
            db: Database session.
        """
        self.db = db

    async def get_tag_by_id(self, tag_id: UUID, owner_id: UUID) -> Tag | None:
        """Get a tag by ID.

        Args:
            tag_id: Tag UUID.
            owner_id: Owner UUID.

        Returns:
            Tag if found, None otherwise.
        """
        result = await self.db.execute(
            select(Tag).where(Tag.id == tag_id, Tag.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_tag_by_name(self, name: str, owner_id: UUID) -> Tag | None:
        """Get a tag by name.

        Args:
            name: Tag name.
            owner_id: Owner UUID.

        Returns:
            Tag if found, None otherwise.
        """
        result = await self.db.execute(
            select(Tag).where(Tag.name == name, Tag.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_tags(self, owner_id: UUID) -> list[Tag]:
        """Get all tags for a user.

        Args:
            owner_id: Owner UUID.

        Returns:
            List of tags.
        """
        result = await self.db.execute(
            select(Tag).where(Tag.owner_id == owner_id).order_by(Tag.name.asc())
        )
        return list(result.scalars().all())

    async def create_tag(self, owner_id: UUID, data: TagCreate) -> Tag:
        """Create a new tag.

        Args:
            owner_id: Owner UUID.
            data: Tag creation data.

        Returns:
            Created tag.

        Raises:
            TagAlreadyExistsError: If tag with name already exists.
        """
        # Check for existing tag with same name
        existing = await self.get_tag_by_name(data.name, owner_id)
        if existing:
            raise TagAlreadyExistsError(f"Tag with name '{data.name}' already exists")

        tag = Tag(
            owner_id=owner_id,
            name=data.name,
            color=data.color,
        )
        self.db.add(tag)
        await self.db.flush()
        return tag

    async def update_tag(self, tag_id: UUID, owner_id: UUID, data: TagUpdate) -> Tag:
        """Update a tag.

        Args:
            tag_id: Tag UUID.
            owner_id: Owner UUID.
            data: Update data.

        Returns:
            Updated tag.

        Raises:
            TagNotFoundError: If tag not found.
            TagAlreadyExistsError: If new name conflicts with existing tag.
        """
        tag = await self.get_tag_by_id(tag_id, owner_id)
        if not tag:
            raise TagNotFoundError(f"Tag not found: {tag_id}")

        # Check for name conflict if name is being updated
        if data.name and data.name != tag.name:
            existing = await self.get_tag_by_name(data.name, owner_id)
            if existing:
                raise TagAlreadyExistsError(
                    f"Tag with name '{data.name}' already exists"
                )

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(tag, field, value)

        await self.db.flush()
        return tag

    async def delete_tag(self, tag_id: UUID, owner_id: UUID) -> None:
        """Delete a tag.

        Args:
            tag_id: Tag UUID.
            owner_id: Owner UUID.

        Raises:
            TagNotFoundError: If tag not found.
        """
        tag = await self.get_tag_by_id(tag_id, owner_id)
        if not tag:
            raise TagNotFoundError(f"Tag not found: {tag_id}")

        await self.db.delete(tag)
        await self.db.flush()

    async def _get_song(self, song_id: UUID, owner_id: UUID) -> Song | None:
        """Get a song by ID.

        Args:
            song_id: Song UUID.
            owner_id: Owner UUID.

        Returns:
            Song if found, None otherwise.
        """
        result = await self.db.execute(
            select(Song).where(Song.id == song_id, Song.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def _get_song_with_tags(self, song_id: UUID, owner_id: UUID) -> Song | None:
        """Get a song with its tags.

        Args:
            song_id: Song UUID.
            owner_id: Owner UUID.

        Returns:
            Song with tags if found, None otherwise.
        """
        result = await self.db.execute(
            select(Song)
            .where(Song.id == song_id, Song.owner_id == owner_id)
            .options(selectinload(Song.song_tags).selectinload(SongTag.tag))
        )
        return result.scalar_one_or_none()

    async def _get_song_tag(self, song_id: UUID, tag_id: UUID) -> SongTag | None:
        """Get a song-tag association.

        Args:
            song_id: Song UUID.
            tag_id: Tag UUID.

        Returns:
            SongTag if found, None otherwise.
        """
        result = await self.db.execute(
            select(SongTag).where(
                SongTag.song_id == song_id,
                SongTag.tag_id == tag_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_tag_to_song(
        self,
        song_id: UUID,
        tag_id: UUID,
        owner_id: UUID,
    ) -> Song:
        """Add a tag to a song.

        Args:
            song_id: Song UUID.
            tag_id: Tag UUID.
            owner_id: Owner UUID.

        Returns:
            Updated song with tags.

        Raises:
            SongNotFoundError: If song not found.
            TagNotFoundError: If tag not found.
            TagAlreadyOnSongError: If tag already on song.
        """
        song = await self._get_song(song_id, owner_id)
        if not song:
            raise SongNotFoundError(f"Song not found: {song_id}")

        tag = await self.get_tag_by_id(tag_id, owner_id)
        if not tag:
            raise TagNotFoundError(f"Tag not found: {tag_id}")

        # Check if tag is already on song
        existing = await self._get_song_tag(song_id, tag_id)
        if existing:
            raise TagAlreadyOnSongError(f"Tag {tag_id} is already on song {song_id}")

        song_tag = SongTag(song_id=song_id, tag_id=tag_id)
        self.db.add(song_tag)
        await self.db.flush()

        return await self._get_song_with_tags(song_id, owner_id)  # type: ignore

    async def remove_tag_from_song(
        self,
        song_id: UUID,
        tag_id: UUID,
        owner_id: UUID,
    ) -> Song:
        """Remove a tag from a song.

        Args:
            song_id: Song UUID.
            tag_id: Tag UUID.
            owner_id: Owner UUID.

        Returns:
            Updated song with tags.

        Raises:
            SongNotFoundError: If song not found.
            TagNotOnSongError: If tag not on song.
        """
        song = await self._get_song(song_id, owner_id)
        if not song:
            raise SongNotFoundError(f"Song not found: {song_id}")

        song_tag = await self._get_song_tag(song_id, tag_id)
        if not song_tag:
            raise TagNotOnSongError(f"Tag {tag_id} is not on song {song_id}")

        await self.db.delete(song_tag)
        await self.db.flush()

        return await self._get_song_with_tags(song_id, owner_id)  # type: ignore

    async def get_song_with_tags(self, song_id: UUID, owner_id: UUID) -> Song | None:
        """Get a song with its tags (public method).

        Args:
            song_id: Song UUID.
            owner_id: Owner UUID.

        Returns:
            Song with tags if found, None otherwise.
        """
        return await self._get_song_with_tags(song_id, owner_id)

    async def get_songs_by_tag(
        self,
        tag_id: UUID,
        owner_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Song], int]:
        """Get songs with a specific tag.

        Args:
            tag_id: Tag UUID.
            owner_id: Owner UUID.
            page: Page number (1-based).
            limit: Items per page.

        Returns:
            Tuple of (songs list, total count).

        Raises:
            TagNotFoundError: If tag not found.
        """
        tag = await self.get_tag_by_id(tag_id, owner_id)
        if not tag:
            raise TagNotFoundError(f"Tag not found: {tag_id}")

        # Count total
        count_result = await self.db.execute(
            select(SongTag).where(SongTag.tag_id == tag_id)
        )
        total = len(count_result.scalars().all())

        # Get songs
        offset = (page - 1) * limit
        result = await self.db.execute(
            select(Song)
            .join(SongTag, Song.id == SongTag.song_id)
            .where(SongTag.tag_id == tag_id, Song.owner_id == owner_id)
            .order_by(Song.title.asc())
            .offset(offset)
            .limit(limit)
        )
        songs = list(result.scalars().all())

        return songs, total
