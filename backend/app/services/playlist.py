"""Playlist service with business logic for playlist management."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.playlist import Playlist, PlaylistSong
from app.models.song import Song
from app.schemas.playlist import PlaylistCreate, PlaylistUpdate


class PlaylistServiceError(Exception):
    """Base exception for playlist service errors."""


class PlaylistNotFoundError(PlaylistServiceError):
    """Raised when playlist is not found."""


class SongNotFoundError(PlaylistServiceError):
    """Raised when song is not found."""


class SongAlreadyInPlaylistError(PlaylistServiceError):
    """Raised when song is already in playlist."""


class SongNotInPlaylistError(PlaylistServiceError):
    """Raised when song is not in playlist."""


class PlaylistService:
    """Service for managing playlists."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize playlist service.

        Args:
            db: Database session.
        """
        self.db = db

    async def get_playlist_by_id(
        self, playlist_id: UUID, owner_id: UUID
    ) -> Playlist | None:
        """Get a playlist by ID.

        Args:
            playlist_id: Playlist UUID.
            owner_id: Owner UUID.

        Returns:
            Playlist if found, None otherwise.
        """
        result = await self.db.execute(
            select(Playlist).where(
                Playlist.id == playlist_id, Playlist.owner_id == owner_id
            )
        )
        return result.scalar_one_or_none()

    async def get_playlist_with_songs(
        self, playlist_id: UUID, owner_id: UUID
    ) -> Playlist | None:
        """Get a playlist with its songs.

        Args:
            playlist_id: Playlist UUID.
            owner_id: Owner UUID.

        Returns:
            Playlist with songs if found, None otherwise.
        """
        result = await self.db.execute(
            select(Playlist)
            .where(Playlist.id == playlist_id, Playlist.owner_id == owner_id)
            .options(
                selectinload(Playlist.playlist_songs).selectinload(PlaylistSong.song)
            )
        )
        return result.scalar_one_or_none()

    async def get_playlists(
        self,
        owner_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Playlist], int]:
        """Get playlists with pagination.

        Args:
            owner_id: Owner UUID.
            page: Page number (1-based).
            limit: Items per page.

        Returns:
            Tuple of (playlists list, total count).
        """
        # Base query
        query = select(Playlist).where(Playlist.owner_id == owner_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting and pagination
        query = query.order_by(Playlist.updated_at.desc())
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        playlists = list(result.scalars().all())

        return playlists, total

    async def create_playlist(self, owner_id: UUID, data: PlaylistCreate) -> Playlist:
        """Create a new playlist.

        Args:
            owner_id: Owner UUID.
            data: Playlist creation data.

        Returns:
            Created playlist.
        """
        playlist = Playlist(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
        )
        self.db.add(playlist)
        await self.db.flush()
        return playlist

    async def update_playlist(
        self, playlist_id: UUID, owner_id: UUID, data: PlaylistUpdate
    ) -> Playlist:
        """Update a playlist.

        Args:
            playlist_id: Playlist UUID.
            owner_id: Owner UUID.
            data: Update data.

        Returns:
            Updated playlist.

        Raises:
            PlaylistNotFoundError: If playlist not found.
        """
        playlist = await self.get_playlist_by_id(playlist_id, owner_id)
        if not playlist:
            raise PlaylistNotFoundError(f"Playlist not found: {playlist_id}")

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(playlist, field, value)

        await self.db.flush()
        return playlist

    async def delete_playlist(self, playlist_id: UUID, owner_id: UUID) -> None:
        """Delete a playlist.

        Args:
            playlist_id: Playlist UUID.
            owner_id: Owner UUID.

        Raises:
            PlaylistNotFoundError: If playlist not found.
        """
        playlist = await self.get_playlist_by_id(playlist_id, owner_id)
        if not playlist:
            raise PlaylistNotFoundError(f"Playlist not found: {playlist_id}")

        await self.db.delete(playlist)
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

    async def _get_playlist_song(
        self, playlist_id: UUID, song_id: UUID
    ) -> PlaylistSong | None:
        """Get a playlist-song association.

        Args:
            playlist_id: Playlist UUID.
            song_id: Song UUID.

        Returns:
            PlaylistSong if found, None otherwise.
        """
        result = await self.db.execute(
            select(PlaylistSong).where(
                PlaylistSong.playlist_id == playlist_id,
                PlaylistSong.song_id == song_id,
            )
        )
        return result.scalar_one_or_none()

    async def _recalculate_playlist_stats(self, playlist: Playlist) -> None:
        """Recalculate playlist song_count and total_duration.

        Args:
            playlist: Playlist to recalculate.
        """
        # Get stats
        result = await self.db.execute(
            select(
                func.count(PlaylistSong.id).label("song_count"),
                func.coalesce(func.sum(Song.duration_seconds), 0).label(
                    "total_duration"
                ),
            )
            .select_from(PlaylistSong)
            .join(Song, PlaylistSong.song_id == Song.id)
            .where(PlaylistSong.playlist_id == playlist.id)
        )
        row = result.one()

        playlist.song_count = row.song_count
        playlist.total_duration_seconds = row.total_duration

    async def add_song_to_playlist(
        self,
        playlist_id: UUID,
        song_id: UUID,
        owner_id: UUID,
        position: int | None = None,
    ) -> Playlist:
        """Add a song to a playlist.

        Args:
            playlist_id: Playlist UUID.
            song_id: Song UUID.
            owner_id: Owner UUID.
            position: Optional position in playlist.

        Returns:
            Updated playlist.

        Raises:
            PlaylistNotFoundError: If playlist not found.
            SongNotFoundError: If song not found.
            SongAlreadyInPlaylistError: If song already in playlist.
        """
        playlist = await self.get_playlist_by_id(playlist_id, owner_id)
        if not playlist:
            raise PlaylistNotFoundError(f"Playlist not found: {playlist_id}")

        song = await self._get_song(song_id, owner_id)
        if not song:
            raise SongNotFoundError(f"Song not found: {song_id}")

        # Check if song is already in playlist
        existing = await self._get_playlist_song(playlist_id, song_id)
        if existing:
            raise SongAlreadyInPlaylistError(
                f"Song {song_id} is already in playlist {playlist_id}"
            )

        # Determine position
        if position is None:
            # Add to end
            position = playlist.song_count

        # Shift positions of songs at or after this position
        result = await self.db.execute(
            select(PlaylistSong)
            .where(
                PlaylistSong.playlist_id == playlist_id,
                PlaylistSong.position >= position,
            )
            .order_by(PlaylistSong.position.desc())
        )
        songs_to_shift = result.scalars().all()
        for ps in songs_to_shift:
            ps.position += 1

        # Add the song
        playlist_song = PlaylistSong(
            playlist_id=playlist_id,
            song_id=song_id,
            position=position,
        )
        self.db.add(playlist_song)

        # Recalculate stats
        await self._recalculate_playlist_stats(playlist)

        await self.db.flush()
        return await self.get_playlist_with_songs(playlist_id, owner_id)  # type: ignore

    async def remove_song_from_playlist(
        self,
        playlist_id: UUID,
        song_id: UUID,
        owner_id: UUID,
    ) -> Playlist:
        """Remove a song from a playlist.

        Args:
            playlist_id: Playlist UUID.
            song_id: Song UUID.
            owner_id: Owner UUID.

        Returns:
            Updated playlist.

        Raises:
            PlaylistNotFoundError: If playlist not found.
            SongNotInPlaylistError: If song not in playlist.
        """
        playlist = await self.get_playlist_by_id(playlist_id, owner_id)
        if not playlist:
            raise PlaylistNotFoundError(f"Playlist not found: {playlist_id}")

        playlist_song = await self._get_playlist_song(playlist_id, song_id)
        if not playlist_song:
            raise SongNotInPlaylistError(
                f"Song {song_id} is not in playlist {playlist_id}"
            )

        removed_position = playlist_song.position
        await self.db.delete(playlist_song)

        # Shift positions of songs after the removed one
        result = await self.db.execute(
            select(PlaylistSong)
            .where(
                PlaylistSong.playlist_id == playlist_id,
                PlaylistSong.position > removed_position,
            )
            .order_by(PlaylistSong.position.asc())
        )
        songs_to_shift = result.scalars().all()
        for ps in songs_to_shift:
            ps.position -= 1

        # Recalculate stats
        await self._recalculate_playlist_stats(playlist)

        await self.db.flush()
        return await self.get_playlist_with_songs(playlist_id, owner_id)  # type: ignore

    async def reorder_playlist_songs(
        self,
        playlist_id: UUID,
        song_ids: list[UUID],
        owner_id: UUID,
    ) -> Playlist:
        """Reorder songs in a playlist.

        Args:
            playlist_id: Playlist UUID.
            song_ids: List of song IDs in new order.
            owner_id: Owner UUID.

        Returns:
            Updated playlist.

        Raises:
            PlaylistNotFoundError: If playlist not found.
            ValueError: If song_ids don't match playlist songs.
        """
        playlist = await self.get_playlist_with_songs(playlist_id, owner_id)
        if not playlist:
            raise PlaylistNotFoundError(f"Playlist not found: {playlist_id}")

        # Verify all songs are in playlist
        current_song_ids = {ps.song_id for ps in playlist.playlist_songs}
        if set(song_ids) != current_song_ids:
            raise ValueError("Provided song IDs don't match songs in playlist")

        # Update positions
        for position, song_id in enumerate(song_ids):
            for ps in playlist.playlist_songs:
                if ps.song_id == song_id:
                    ps.position = position
                    break

        await self.db.flush()
        return await self.get_playlist_with_songs(playlist_id, owner_id)  # type: ignore
