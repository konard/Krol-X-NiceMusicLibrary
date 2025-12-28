"""Statistics service with business logic for listening history and analytics."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.listening_history import ContextType, ListeningHistory
from app.models.song import Song
from app.schemas.stats import ContextType as SchemaContextType
from app.schemas.stats import (
    DailyListeningCount,
    HourlyListeningCount,
    StatsPeriod,
)
from app.services.cache import CacheService, get_cache_service


class StatsServiceError(Exception):
    """Base exception for stats service errors."""


class SongNotFoundError(StatsServiceError):
    """Raised when song is not found."""


# Cache TTL in seconds
CACHE_TTL_OVERVIEW = 300  # 5 minutes
CACHE_TTL_TOP_SONGS = 300  # 5 minutes
CACHE_TTL_TOP_ARTISTS = 300  # 5 minutes


class StatsService:
    """Service for managing listening statistics."""

    def __init__(
        self,
        db: AsyncSession,
        cache: CacheService | None = None,
    ) -> None:
        """Initialize stats service.

        Args:
            db: Database session.
            cache: Cache service for Redis caching. If None, uses global instance.
        """
        self.db = db
        self.cache = cache or get_cache_service()

    def _get_period_start(self, period: StatsPeriod) -> datetime | None:
        """Get the start datetime for a given period.

        Args:
            period: The statistics period.

        Returns:
            Start datetime for the period, or None for 'all'.
        """
        now = datetime.now(UTC)
        if period == StatsPeriod.DAY:
            return now - timedelta(days=1)
        elif period == StatsPeriod.WEEK:
            return now - timedelta(weeks=1)
        elif period == StatsPeriod.MONTH:
            return now - timedelta(days=30)
        elif period == StatsPeriod.YEAR:
            return now - timedelta(days=365)
        else:  # ALL
            return None

    def _map_context_type(
        self, schema_context_type: SchemaContextType | None
    ) -> ContextType | None:
        """Map schema context type to model context type.

        Args:
            schema_context_type: Context type from schema.

        Returns:
            Model context type.
        """
        if schema_context_type is None:
            return None
        return ContextType(schema_context_type.value)

    async def record_play(
        self,
        user_id: UUID,
        song_id: UUID,
        duration_listened_seconds: int,
        completed: bool = False,
        context_type: SchemaContextType | None = None,
        context_id: UUID | None = None,
        device_type: str | None = None,
    ) -> ListeningHistory:
        """Record a play event.

        Args:
            user_id: User UUID.
            song_id: Song UUID.
            duration_listened_seconds: Duration listened in seconds.
            completed: Whether playback was completed.
            context_type: Context of playback (library, playlist, etc.).
            context_id: ID of the context (playlist ID, etc.).
            device_type: Type of device used for playback.

        Returns:
            Created listening history record.

        Raises:
            SongNotFoundError: If song not found.
        """
        # Verify song exists and belongs to user
        result = await self.db.execute(
            select(Song).where(Song.id == song_id, Song.owner_id == user_id)
        )
        song = result.scalar_one_or_none()
        if not song:
            raise SongNotFoundError(f"Song not found: {song_id}")

        # Create listening history record
        history = ListeningHistory(
            user_id=user_id,
            song_id=song_id,
            played_duration_seconds=duration_listened_seconds,
            completed=completed,
            skipped=False,
            context_type=self._map_context_type(context_type),
            context_id=context_id,
            device_type=device_type,
        )
        self.db.add(history)

        # Update song play_count and last_played_at
        song.play_count += 1
        song.last_played_at = datetime.now(UTC)

        await self.db.flush()

        # Invalidate cache for this user's stats
        await self._invalidate_user_cache(user_id)

        return history

    async def _invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate all cached stats for a user.

        Args:
            user_id: User UUID.
        """
        await self.cache.delete_pattern(f"stats:{user_id}:*")

    async def get_history(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[ListeningHistory], int]:
        """Get listening history with pagination.

        Args:
            user_id: User UUID.
            page: Page number (1-based).
            limit: Items per page.
            from_date: Filter from date.
            to_date: Filter to date.

        Returns:
            Tuple of (history list, total count).
        """
        # Base query with song relationship loaded
        query = (
            select(ListeningHistory)
            .options(selectinload(ListeningHistory.song))
            .where(ListeningHistory.user_id == user_id)
        )

        # Apply date filters
        if from_date:
            query = query.where(ListeningHistory.played_at >= from_date)
        if to_date:
            query = query.where(ListeningHistory.played_at <= to_date)

        # Count total
        count_query = (
            select(func.count())
            .select_from(ListeningHistory)
            .where(ListeningHistory.user_id == user_id)
        )
        if from_date:
            count_query = count_query.where(ListeningHistory.played_at >= from_date)
        if to_date:
            count_query = count_query.where(ListeningHistory.played_at <= to_date)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting and pagination
        query = query.order_by(ListeningHistory.played_at.desc())
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        history = list(result.scalars().all())

        return history, total

    async def get_overview(
        self,
        user_id: UUID,
        period: StatsPeriod = StatsPeriod.ALL,
    ) -> dict[str, object]:
        """Get statistics overview.

        Args:
            user_id: User UUID.
            period: Statistics period.

        Returns:
            Statistics overview dictionary.
        """
        # Try to get from cache
        cache_key = f"stats:{user_id}:overview:{period.value}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            # Reconstruct the response objects from cached data
            cached["listening_by_hour"] = [
                HourlyListeningCount(**h) for h in cached.get("listening_by_hour", [])
            ]
            cached["listening_by_day"] = [
                DailyListeningCount(**d) for d in cached.get("listening_by_day", [])
            ]
            return dict(cached)

        period_start = self._get_period_start(period)

        # Base filter for period
        base_filter = [ListeningHistory.user_id == user_id]
        if period_start:
            base_filter.append(ListeningHistory.played_at >= period_start)

        # Total plays
        total_plays_query = select(func.count()).select_from(ListeningHistory)
        for f in base_filter:
            total_plays_query = total_plays_query.where(f)
        result = await self.db.execute(total_plays_query)
        total_plays = result.scalar() or 0

        # Total duration
        total_duration_query = select(
            func.coalesce(func.sum(ListeningHistory.played_duration_seconds), 0)
        ).select_from(ListeningHistory)
        for f in base_filter:
            total_duration_query = total_duration_query.where(f)
        result = await self.db.execute(total_duration_query)
        total_duration_seconds = result.scalar() or 0

        # Unique songs
        unique_songs_query = select(
            func.count(distinct(ListeningHistory.song_id))
        ).select_from(ListeningHistory)
        for f in base_filter:
            unique_songs_query = unique_songs_query.where(f)
        result = await self.db.execute(unique_songs_query)
        unique_songs = result.scalar() or 0

        # Unique artists (join with songs)
        unique_artists_query = (
            select(func.count(distinct(Song.artist)))
            .select_from(ListeningHistory)
            .join(Song, ListeningHistory.song_id == Song.id)
        )
        for f in base_filter:
            unique_artists_query = unique_artists_query.where(f)
        result = await self.db.execute(unique_artists_query)
        unique_artists = result.scalar() or 0

        # Most played genre
        genre_query = (
            select(Song.genre, func.count().label("cnt"))
            .select_from(ListeningHistory)
            .join(Song, ListeningHistory.song_id == Song.id)
            .where(Song.genre.isnot(None))
        )
        for f in base_filter:
            genre_query = genre_query.where(f)
        genre_query = (
            genre_query.group_by(Song.genre).order_by(func.count().desc()).limit(1)
        )
        result = await self.db.execute(genre_query)
        genre_row = result.first()
        most_played_genre = genre_row[0] if genre_row else None

        # Listening by hour
        hour_query = select(
            func.extract("hour", ListeningHistory.played_at).label("hour"),
            func.count().label("cnt"),
        ).select_from(ListeningHistory)
        for f in base_filter:
            hour_query = hour_query.where(f)
        hour_query = hour_query.group_by("hour").order_by("hour")
        result = await self.db.execute(hour_query)
        hourly_rows = result.fetchall()
        listening_by_hour = [
            HourlyListeningCount(hour=int(row[0]), count=row[1]) for row in hourly_rows
        ]

        # Listening by day (last 7/30 days depending on period)
        days_to_show = 7 if period in (StatsPeriod.DAY, StatsPeriod.WEEK) else 30
        day_cutoff = datetime.now(UTC) - timedelta(days=days_to_show)

        day_query = (
            select(
                func.date(ListeningHistory.played_at).label("day"),
                func.count().label("cnt"),
            )
            .select_from(ListeningHistory)
            .where(ListeningHistory.user_id == user_id)
            .where(ListeningHistory.played_at >= day_cutoff)
        )
        day_query = day_query.group_by("day").order_by("day")
        result = await self.db.execute(day_query)
        daily_rows = result.fetchall()
        listening_by_day = [
            DailyListeningCount(day=str(row[0]), count=row[1]) for row in daily_rows
        ]

        result_data = {
            "total_plays": total_plays,
            "total_duration_seconds": total_duration_seconds,
            "unique_songs": unique_songs,
            "unique_artists": unique_artists,
            "most_played_genre": most_played_genre,
            "listening_by_hour": listening_by_hour,
            "listening_by_day": listening_by_day,
        }

        # Cache the result
        cache_data = {
            **result_data,
            "listening_by_hour": [h.model_dump() for h in listening_by_hour],
            "listening_by_day": [d.model_dump() for d in listening_by_day],
        }
        await self.cache.set(cache_key, cache_data, CACHE_TTL_OVERVIEW)

        return result_data

    async def get_top_songs(
        self,
        user_id: UUID,
        period: StatsPeriod = StatsPeriod.ALL,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """Get top songs by play count.

        Args:
            user_id: User UUID.
            period: Statistics period.
            limit: Maximum number of songs to return.

        Returns:
            List of top songs with play counts.
        """
        period_start = self._get_period_start(period)

        query = (
            select(Song, func.count().label("play_count"))
            .select_from(ListeningHistory)
            .join(Song, ListeningHistory.song_id == Song.id)
            .where(ListeningHistory.user_id == user_id)
        )

        if period_start:
            query = query.where(ListeningHistory.played_at >= period_start)

        query = query.group_by(Song.id).order_by(func.count().desc()).limit(limit)

        result = await self.db.execute(query)
        rows = result.fetchall()

        return [{"song": row[0], "play_count": row[1]} for row in rows]

    async def get_top_artists(
        self,
        user_id: UUID,
        period: StatsPeriod = StatsPeriod.ALL,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """Get top artists by play count.

        Args:
            user_id: User UUID.
            period: Statistics period.
            limit: Maximum number of artists to return.

        Returns:
            List of top artists with play counts and their songs.
        """
        period_start = self._get_period_start(period)

        # Get top artists with play counts
        query = (
            select(Song.artist, func.count().label("play_count"))
            .select_from(ListeningHistory)
            .join(Song, ListeningHistory.song_id == Song.id)
            .where(ListeningHistory.user_id == user_id)
            .where(Song.artist.isnot(None))
        )

        if period_start:
            query = query.where(ListeningHistory.played_at >= period_start)

        query = query.group_by(Song.artist).order_by(func.count().desc()).limit(limit)

        result = await self.db.execute(query)
        artist_rows = result.fetchall()

        # For each artist, get their songs
        top_artists = []
        for artist_row in artist_rows:
            artist_name = artist_row[0]
            play_count = artist_row[1]

            # Get songs for this artist (ordered by play count in the period)
            songs_query = (
                select(Song, func.count().label("song_plays"))
                .select_from(ListeningHistory)
                .join(Song, ListeningHistory.song_id == Song.id)
                .where(ListeningHistory.user_id == user_id)
                .where(Song.artist == artist_name)
            )
            if period_start:
                songs_query = songs_query.where(
                    ListeningHistory.played_at >= period_start
                )
            songs_query = (
                songs_query.group_by(Song.id).order_by(func.count().desc()).limit(5)
            )

            songs_result = await self.db.execute(songs_query)
            songs = [row[0] for row in songs_result.fetchall()]

            top_artists.append(
                {
                    "artist": artist_name,
                    "play_count": play_count,
                    "songs": songs,
                }
            )

        return top_artists
