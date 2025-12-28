"""Recommendation service with intelligent music recommendations."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.listening_history import ListeningHistory
from app.models.playlist import Playlist
from app.models.song import Song
from app.schemas.recommendation import DiscoverSectionType, MoodType
from app.services.cache import CacheService, get_cache_service

logger = logging.getLogger(__name__)

# Cache TTL in seconds
CACHE_TTL_SIMILAR = 600  # 10 minutes
CACHE_TTL_DISCOVER = 300  # 5 minutes
CACHE_TTL_MIX = 300  # 5 minutes
CACHE_TTL_SEARCH = 60  # 1 minute


class RecommendationServiceError(Exception):
    """Base exception for recommendation service errors."""


class SongNotFoundError(RecommendationServiceError):
    """Raised when song is not found."""


class RecommendationService:
    """Service for generating music recommendations."""

    def __init__(
        self,
        db: AsyncSession,
        cache: CacheService | None = None,
    ) -> None:
        """Initialize recommendation service.

        Args:
            db: Database session.
            cache: Cache service for Redis caching. If None, uses global instance.
        """
        self.db = db
        self.cache = cache or get_cache_service()

    def _calculate_similarity(
        self,
        source: Song,
        candidate: Song,
    ) -> tuple[float, list[str]]:
        """Calculate similarity between two songs.

        Uses content-based filtering based on:
        - Genre match
        - BPM similarity
        - Energy similarity
        - Valence similarity
        - Same artist boost

        Args:
            source: Source song to compare from.
            candidate: Candidate song to compare to.

        Returns:
            Tuple of (similarity_score, reasons).
        """
        score = 0.0
        reasons: list[str] = []
        weights_sum = 0.0

        # Genre match (weight: 0.3)
        if source.genre and candidate.genre:
            weights_sum += 0.3
            if source.genre.lower() == candidate.genre.lower():
                score += 0.3
                reasons.append("same genre")

        # BPM similarity (weight: 0.2)
        if source.bpm and candidate.bpm:
            weights_sum += 0.2
            bpm_diff = abs(source.bpm - candidate.bpm)
            if bpm_diff <= 10:
                score += 0.2
                reasons.append("similar BPM")
            elif bpm_diff <= 20:
                score += 0.15
                reasons.append("close BPM")
            elif bpm_diff <= 30:
                score += 0.1

        # Energy similarity (weight: 0.2)
        if source.energy is not None and candidate.energy is not None:
            weights_sum += 0.2
            energy_diff = abs(source.energy - candidate.energy)
            if energy_diff <= 0.1:
                score += 0.2
                reasons.append("similar energy")
            elif energy_diff <= 0.2:
                score += 0.15
            elif energy_diff <= 0.3:
                score += 0.1

        # Valence similarity (weight: 0.15)
        if source.valence is not None and candidate.valence is not None:
            weights_sum += 0.15
            valence_diff = abs(source.valence - candidate.valence)
            if valence_diff <= 0.1:
                score += 0.15
                reasons.append("similar mood")
            elif valence_diff <= 0.2:
                score += 0.1
            elif valence_diff <= 0.3:
                score += 0.05

        # Same artist boost (weight: 0.15)
        weights_sum += 0.15
        if (
            source.artist
            and candidate.artist
            and source.artist.lower() == candidate.artist.lower()
        ):
            score += 0.15
            reasons.append("same artist")

        # Normalize score if we have any weights
        # Use 0.3 as fallback when no parameters available for comparison
        score = score / weights_sum if weights_sum > 0 else 0.3

        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))

        return score, reasons

    async def get_similar_songs(
        self,
        song_id: UUID,
        user_id: UUID,
        limit: int = 10,
    ) -> tuple[Song, list[tuple[Song, float, list[str]]]]:
        """Get similar songs based on content-based filtering.

        Args:
            song_id: Source song UUID.
            user_id: User UUID.
            limit: Maximum number of similar songs to return.

        Returns:
            Tuple of (source_song, list of (song, similarity_score, reasons)).

        Raises:
            SongNotFoundError: If source song not found.
        """
        # Get source song
        result = await self.db.execute(
            select(Song).where(Song.id == song_id, Song.owner_id == user_id)
        )
        source_song = result.scalar_one_or_none()
        if not source_song:
            raise SongNotFoundError(f"Song not found: {song_id}")

        # Try cache
        cache_key = f"recommendations:similar:{user_id}:{song_id}:{limit}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            # Rebuild from cache - fetch songs by IDs
            song_ids = [UUID(item["song_id"]) for item in cached]
            if song_ids:
                songs_result = await self.db.execute(
                    select(Song).where(Song.id.in_(song_ids))
                )
                songs_map = {s.id: s for s in songs_result.scalars().all()}

                similar_songs = []
                for item in cached:
                    song = songs_map.get(UUID(item["song_id"]))
                    if song:
                        similar_songs.append((song, item["score"], item["reasons"]))
                return source_song, similar_songs

        # Get all other songs from user's library
        result = await self.db.execute(
            select(Song).where(Song.owner_id == user_id, Song.id != song_id)
        )
        candidate_songs = list(result.scalars().all())

        # Calculate similarity for each candidate
        scored_songs: list[tuple[Song, float, list[str]]] = []
        for candidate in candidate_songs:
            score, reasons = self._calculate_similarity(source_song, candidate)
            if score > 0:
                scored_songs.append((candidate, score, reasons))

        # Sort by similarity score and take top N
        scored_songs.sort(key=lambda x: x[1], reverse=True)
        similar_songs = scored_songs[:limit]

        # Cache the results
        cache_data = [
            {"song_id": str(song.id), "score": score, "reasons": reasons}
            for song, score, reasons in similar_songs
        ]
        await self.cache.set(cache_key, cache_data, CACHE_TTL_SIMILAR)

        return source_song, similar_songs

    async def get_frequently_played_together(
        self,
        song_id: UUID,
        user_id: UUID,
        limit: int = 5,
    ) -> list[tuple[Song, int]]:
        """Get songs that are frequently played after the given song.

        Args:
            song_id: Source song UUID.
            user_id: User UUID.
            limit: Maximum number of songs to return.

        Returns:
            List of (song, transition_count) tuples.
        """
        # Find songs that were played after this song
        query = (
            select(
                ListeningHistory.song_id,
                func.count().label("transition_count"),
            )
            .where(
                ListeningHistory.user_id == user_id,
                ListeningHistory.previous_song_id == song_id,
            )
            .group_by(ListeningHistory.song_id)
            .order_by(func.count().desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        transition_rows = result.fetchall()

        if not transition_rows:
            return []

        # Get song details
        song_ids = [row[0] for row in transition_rows]
        songs_result = await self.db.execute(select(Song).where(Song.id.in_(song_ids)))
        songs_map = {s.id: s for s in songs_result.scalars().all()}

        return [
            (songs_map[row[0]], row[1])
            for row in transition_rows
            if row[0] in songs_map
        ]

    async def get_discover_recommendations(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> dict[DiscoverSectionType, list[Song]]:
        """Get discovery recommendations in multiple sections.

        Sections:
        - long_time_no_listen: Songs with high play_count but old last_played_at
        - based_on_favorite: Similar to user's top 5 songs by play_count
        - hidden_gems: Low play_count songs similar to favorites

        Args:
            user_id: User UUID.
            limit: Maximum songs per section.

        Returns:
            Dict mapping section type to list of songs.
        """
        # Try cache
        cache_key = f"recommendations:discover:{user_id}:{limit}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            # Rebuild from cache
            all_song_ids: list[UUID] = []
            for section_data in cached.values():
                all_song_ids.extend([UUID(sid) for sid in section_data])

            if all_song_ids:
                songs_result = await self.db.execute(
                    select(Song).where(Song.id.in_(all_song_ids))
                )
                songs_map = {s.id: s for s in songs_result.scalars().all()}

                cached_sections: dict[DiscoverSectionType, list[Song]] = {}
                for section_type_str, song_ids_list in cached.items():
                    section_type = DiscoverSectionType(section_type_str)
                    cached_sections[section_type] = [
                        songs_map[UUID(sid)]
                        for sid in song_ids_list
                        if UUID(sid) in songs_map
                    ]
                return cached_sections

        sections: dict[DiscoverSectionType, list[Song]] = {}

        # Long time no listen: high play_count, old last_played_at
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        long_time_query = (
            select(Song)
            .where(
                Song.owner_id == user_id,
                Song.play_count >= 5,
                or_(
                    Song.last_played_at.is_(None),
                    Song.last_played_at < thirty_days_ago,
                ),
            )
            .order_by(Song.play_count.desc())
            .limit(limit)
        )
        result = await self.db.execute(long_time_query)
        sections[DiscoverSectionType.LONG_TIME_NO_LISTEN] = list(result.scalars().all())

        # Get user's top 5 favorite songs by play_count
        top_songs_query = (
            select(Song)
            .where(Song.owner_id == user_id)
            .order_by(Song.play_count.desc())
            .limit(5)
        )
        result = await self.db.execute(top_songs_query)
        top_songs = list(result.scalars().all())

        # Based on favorite: songs similar to top songs
        if top_songs:
            # Get all other songs
            top_song_ids = [s.id for s in top_songs]
            result = await self.db.execute(
                select(Song).where(
                    Song.owner_id == user_id,
                    ~Song.id.in_(top_song_ids),
                )
            )
            candidate_songs = list(result.scalars().all())

            # Calculate average similarity to top songs
            scored_candidates: list[tuple[Song, float]] = []
            for candidate in candidate_songs:
                total_score = 0.0
                for top_song in top_songs:
                    score, _ = self._calculate_similarity(top_song, candidate)
                    total_score += score
                avg_score = total_score / len(top_songs)
                scored_candidates.append((candidate, avg_score))

            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            sections[DiscoverSectionType.BASED_ON_FAVORITE] = [
                s[0] for s in scored_candidates[:limit]
            ]
        else:
            sections[DiscoverSectionType.BASED_ON_FAVORITE] = []

        # Hidden gems: low play_count but similar to favorites
        if top_songs:
            low_play_query = select(Song).where(
                Song.owner_id == user_id,
                Song.play_count <= 3,
                ~Song.id.in_(top_song_ids),
            )
            result = await self.db.execute(low_play_query)
            low_play_songs = list(result.scalars().all())

            scored_gems: list[tuple[Song, float]] = []
            for candidate in low_play_songs:
                total_score = 0.0
                for top_song in top_songs:
                    score, _ = self._calculate_similarity(top_song, candidate)
                    total_score += score
                avg_score = total_score / len(top_songs)
                if avg_score > 0.3:  # Only include if reasonably similar
                    scored_gems.append((candidate, avg_score))

            scored_gems.sort(key=lambda x: x[1], reverse=True)
            sections[DiscoverSectionType.HIDDEN_GEMS] = [
                s[0] for s in scored_gems[:limit]
            ]
        else:
            sections[DiscoverSectionType.HIDDEN_GEMS] = []

        # Cache results
        cache_data = {
            section_type.value: [str(s.id) for s in songs]
            for section_type, songs in sections.items()
        }
        await self.cache.set(cache_key, cache_data, CACHE_TTL_DISCOVER)

        return sections

    async def get_personal_mix(
        self,
        user_id: UUID,
        mood: MoodType | None = None,
        duration_minutes: int = 60,
    ) -> tuple[list[Song], int]:
        """Generate a personal mix of songs.

        Args:
            user_id: User UUID.
            mood: Optional mood filter.
            duration_minutes: Target duration in minutes.

        Returns:
            Tuple of (songs list, total_duration_seconds).
        """
        # Try cache
        cache_key = f"recommendations:mix:{user_id}:{mood}:{duration_minutes}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            song_ids = [UUID(sid) for sid in cached["song_ids"]]
            if song_ids:
                songs_result = await self.db.execute(
                    select(Song).where(Song.id.in_(song_ids))
                )
                songs_map = {s.id: s for s in songs_result.scalars().all()}
                songs = [songs_map[sid] for sid in song_ids if sid in songs_map]
                return songs, cached["total_duration"]
            return [], 0

        target_duration = duration_minutes * 60  # Convert to seconds

        # Base query
        query = select(Song).where(Song.owner_id == user_id)

        # Apply mood filter based on energy/valence
        if mood == MoodType.ENERGETIC:
            query = query.where(or_(Song.energy.is_(None), Song.energy >= 0.6))
        elif mood == MoodType.CALM:
            query = query.where(or_(Song.energy.is_(None), Song.energy <= 0.4))
        elif mood == MoodType.FOCUS:
            # Focus: moderate energy, lower valence (less emotional)
            query = query.where(
                or_(
                    Song.energy.is_(None),
                    (Song.energy >= 0.3) & (Song.energy <= 0.7),
                )
            )

        # Order by mix of play_count and randomness
        # Prioritize well-liked songs but add variety
        query = query.order_by(func.random() * 0.5 + (Song.play_count / 100.0) * 0.5)

        result = await self.db.execute(query)
        all_songs = list(result.scalars().all())

        # Select songs to fill the duration
        # Ensure variety: max 3 tracks per artist
        selected_songs: list[Song] = []
        artist_counts: dict[str, int] = {}
        current_duration = 0

        for song in all_songs:
            if current_duration >= target_duration:
                break

            # Check artist limit
            artist = song.artist or "Unknown"
            if artist_counts.get(artist, 0) >= 3:
                continue

            selected_songs.append(song)
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
            current_duration += song.duration_seconds

        total_duration = sum(s.duration_seconds for s in selected_songs)

        # Cache results
        cache_data = {
            "song_ids": [str(s.id) for s in selected_songs],
            "total_duration": total_duration,
        }
        await self.cache.set(cache_key, cache_data, CACHE_TTL_MIX)

        return selected_songs, total_duration

    async def _invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate all cached recommendations for a user.

        Args:
            user_id: User UUID.
        """
        await self.cache.delete_pattern(f"recommendations:{user_id}:*")


class SearchService:
    """Service for global search functionality."""

    def __init__(
        self,
        db: AsyncSession,
        cache: CacheService | None = None,
    ) -> None:
        """Initialize search service.

        Args:
            db: Database session.
            cache: Cache service for Redis caching. If None, uses global instance.
        """
        self.db = db
        self.cache = cache or get_cache_service()

    async def search(
        self,
        user_id: UUID,
        query: str,
        search_type: str = "all",
        limit: int = 10,
    ) -> dict[str, list[Any]]:
        """Perform global search across songs, artists, albums, and playlists.

        Args:
            user_id: User UUID.
            query: Search query string.
            search_type: Type of search ('all', 'songs', 'artists', 'albums', 'playlists').
            limit: Maximum results per category.

        Returns:
            Dict with search results by category.
        """
        if not query or len(query.strip()) < 1:
            return {"songs": [], "artists": [], "albums": [], "playlists": []}

        search_term = f"%{query.strip()}%"

        results: dict[str, list[Any]] = {
            "songs": [],
            "artists": [],
            "albums": [],
            "playlists": [],
        }

        # Search songs
        if search_type in ("all", "songs"):
            songs_query = (
                select(Song)
                .where(
                    Song.owner_id == user_id,
                    or_(
                        Song.title.ilike(search_term),
                        Song.artist.ilike(search_term),
                        Song.album.ilike(search_term),
                    ),
                )
                .order_by(Song.play_count.desc())
                .limit(limit)
            )
            result = await self.db.execute(songs_query)
            results["songs"] = list(result.scalars().all())

        # Search artists (aggregate songs by artist)
        if search_type in ("all", "artists"):
            artists_query = (
                select(
                    Song.artist,
                    func.count().label("song_count"),
                )
                .where(
                    Song.owner_id == user_id,
                    Song.artist.ilike(search_term),
                    Song.artist.isnot(None),
                )
                .group_by(Song.artist)
                .order_by(func.count().desc())
                .limit(limit)
            )
            result = await self.db.execute(artists_query)
            artist_rows = result.fetchall()

            artists_result = []
            for artist_name, song_count in artist_rows:
                # Get top songs for this artist
                songs_result = await self.db.execute(
                    select(Song)
                    .where(Song.owner_id == user_id, Song.artist == artist_name)
                    .order_by(Song.play_count.desc())
                    .limit(5)
                )
                songs = list(songs_result.scalars().all())
                artists_result.append(
                    {
                        "name": artist_name,
                        "song_count": song_count,
                        "songs": songs,
                    }
                )
            results["artists"] = artists_result

        # Search albums (aggregate songs by album)
        if search_type in ("all", "albums"):
            albums_query = (
                select(
                    Song.album,
                    Song.artist,
                    func.count().label("song_count"),
                )
                .where(
                    Song.owner_id == user_id,
                    Song.album.ilike(search_term),
                    Song.album.isnot(None),
                )
                .group_by(Song.album, Song.artist)
                .order_by(func.count().desc())
                .limit(limit)
            )
            result = await self.db.execute(albums_query)
            album_rows = result.fetchall()

            albums_result = []
            for album_name, artist_name, song_count in album_rows:
                # Get songs from this album
                songs_result = await self.db.execute(
                    select(Song)
                    .where(
                        Song.owner_id == user_id,
                        Song.album == album_name,
                    )
                    .order_by(Song.track_number)
                    .limit(10)
                )
                songs = list(songs_result.scalars().all())
                albums_result.append(
                    {
                        "name": album_name,
                        "artist": artist_name,
                        "song_count": song_count,
                        "songs": songs,
                    }
                )
            results["albums"] = albums_result

        # Search playlists
        if search_type in ("all", "playlists"):
            playlists_query = (
                select(Playlist)
                .options(selectinload(Playlist.playlist_songs))
                .where(
                    Playlist.owner_id == user_id,
                    Playlist.name.ilike(search_term),
                )
                .order_by(Playlist.name)
                .limit(limit)
            )
            result = await self.db.execute(playlists_query)
            playlists = cast(list[Playlist], list(result.scalars().all()))
            results["playlists"] = [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "song_count": len(p.playlist_songs),
                }
                for p in playlists
            ]

        return results
