"""Mood chain service with business logic for mood chain management."""

import random
from collections import defaultdict
from datetime import UTC, datetime
from typing import TypedDict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.listening_history import ListeningHistory
from app.models.mood_chain import (
    MoodChain,
    MoodChainSong,
    MoodChainTransition,
    TransitionStyle,
)
from app.models.song import Song
from app.schemas.mood_chain import (
    MoodChainCreate,
    MoodChainFromHistoryRequest,
    MoodChainTransitionBase,
    MoodChainUpdate,
)


class SongSuggestion(TypedDict):
    """Type for song suggestion dictionaries."""

    song_id: UUID
    title: str
    artist: str | None
    album: str | None
    duration_seconds: int
    cover_art_path: str | None
    weight: float
    reason: str


class MoodChainServiceError(Exception):
    """Base exception for mood chain service errors."""


class MoodChainNotFoundError(MoodChainServiceError):
    """Raised when mood chain is not found."""


class SongNotFoundError(MoodChainServiceError):
    """Raised when song is not found."""


class SongAlreadyInMoodChainError(MoodChainServiceError):
    """Raised when song is already in mood chain."""


class SongNotInMoodChainError(MoodChainServiceError):
    """Raised when song is not in mood chain."""


class MoodChainService:
    """Service for managing mood chains."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize mood chain service.

        Args:
            db: Database session.
        """
        self.db = db

    async def get_mood_chain_by_id(
        self, mood_chain_id: UUID, owner_id: UUID
    ) -> MoodChain | None:
        """Get a mood chain by ID.

        Args:
            mood_chain_id: Mood chain UUID.
            owner_id: Owner UUID.

        Returns:
            MoodChain if found, None otherwise.
        """
        result = await self.db.execute(
            select(MoodChain).where(
                MoodChain.id == mood_chain_id, MoodChain.owner_id == owner_id
            )
        )
        return result.scalar_one_or_none()

    async def get_mood_chain_with_songs(
        self, mood_chain_id: UUID, owner_id: UUID, *, refresh: bool = False
    ) -> MoodChain | None:
        """Get a mood chain with its songs and transitions.

        Args:
            mood_chain_id: Mood chain UUID.
            owner_id: Owner UUID.
            refresh: Force fresh data by bypassing identity map cache.

        Returns:
            MoodChain with songs and transitions if found, None otherwise.
        """
        query = (
            select(MoodChain)
            .where(MoodChain.id == mood_chain_id, MoodChain.owner_id == owner_id)
            .options(
                selectinload(MoodChain.mood_chain_songs).selectinload(
                    MoodChainSong.song
                ),
                selectinload(MoodChain.mood_chain_transitions),
            )
        )
        if refresh:
            query = query.execution_options(populate_existing=True)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_mood_chains(
        self,
        owner_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[MoodChain], int]:
        """Get mood chains with pagination.

        Args:
            owner_id: Owner UUID.
            page: Page number (1-based).
            limit: Items per page.

        Returns:
            Tuple of (mood chains list, total count).
        """
        # Base query
        query = select(MoodChain).where(MoodChain.owner_id == owner_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting and pagination
        query = query.order_by(MoodChain.updated_at.desc())
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        mood_chains = list(result.scalars().all())

        return mood_chains, total

    async def create_mood_chain(
        self, owner_id: UUID, data: MoodChainCreate
    ) -> MoodChain:
        """Create a new mood chain.

        Args:
            owner_id: Owner UUID.
            data: Mood chain creation data.

        Returns:
            Created mood chain.
        """
        mood_chain = MoodChain(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            transition_style=data.transition_style,
            auto_advance=data.auto_advance,
            auto_advance_delay_seconds=data.auto_advance_delay_seconds,
        )
        self.db.add(mood_chain)
        await self.db.flush()

        # Add songs if provided
        if data.song_ids:
            for position, song_id in enumerate(data.song_ids):
                # Verify song exists and belongs to user
                song = await self._get_song(song_id, owner_id)
                if song:
                    mood_chain_song = MoodChainSong(
                        mood_chain_id=mood_chain.id,
                        song_id=song_id,
                        position=position,
                    )
                    self.db.add(mood_chain_song)

            await self.db.flush()
            await self._recalculate_mood_chain_stats(mood_chain)
            await self.db.flush()

        return mood_chain

    async def update_mood_chain(
        self, mood_chain_id: UUID, owner_id: UUID, data: MoodChainUpdate
    ) -> MoodChain:
        """Update a mood chain.

        Args:
            mood_chain_id: Mood chain UUID.
            owner_id: Owner UUID.
            data: Update data.

        Returns:
            Updated mood chain.

        Raises:
            MoodChainNotFoundError: If mood chain not found.
        """
        mood_chain = await self.get_mood_chain_by_id(mood_chain_id, owner_id)
        if not mood_chain:
            raise MoodChainNotFoundError(f"Mood chain not found: {mood_chain_id}")

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(mood_chain, field, value)

        await self.db.flush()
        # Refresh to get server-side updated_at value
        await self.db.refresh(mood_chain)
        return mood_chain

    async def delete_mood_chain(self, mood_chain_id: UUID, owner_id: UUID) -> None:
        """Delete a mood chain.

        Args:
            mood_chain_id: Mood chain UUID.
            owner_id: Owner UUID.

        Raises:
            MoodChainNotFoundError: If mood chain not found.
        """
        mood_chain = await self.get_mood_chain_by_id(mood_chain_id, owner_id)
        if not mood_chain:
            raise MoodChainNotFoundError(f"Mood chain not found: {mood_chain_id}")

        await self.db.delete(mood_chain)
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

    async def _get_mood_chain_song(
        self, mood_chain_id: UUID, song_id: UUID
    ) -> MoodChainSong | None:
        """Get a mood chain-song association.

        Args:
            mood_chain_id: Mood chain UUID.
            song_id: Song UUID.

        Returns:
            MoodChainSong if found, None otherwise.
        """
        result = await self.db.execute(
            select(MoodChainSong).where(
                MoodChainSong.mood_chain_id == mood_chain_id,
                MoodChainSong.song_id == song_id,
            )
        )
        return result.scalar_one_or_none()

    async def _recalculate_mood_chain_stats(self, mood_chain: MoodChain) -> None:
        """Recalculate mood chain song_count.

        Args:
            mood_chain: Mood chain to recalculate.
        """
        result = await self.db.execute(
            select(func.count(MoodChainSong.id)).where(
                MoodChainSong.mood_chain_id == mood_chain.id
            )
        )
        mood_chain.song_count = result.scalar() or 0

    async def add_song_to_mood_chain(
        self,
        mood_chain_id: UUID,
        song_id: UUID,
        owner_id: UUID,
        position: int | None = None,
    ) -> MoodChain:
        """Add a song to a mood chain.

        Args:
            mood_chain_id: Mood chain UUID.
            song_id: Song UUID.
            owner_id: Owner UUID.
            position: Optional position in mood chain.

        Returns:
            Updated mood chain.

        Raises:
            MoodChainNotFoundError: If mood chain not found.
            SongNotFoundError: If song not found.
            SongAlreadyInMoodChainError: If song already in mood chain.
        """
        mood_chain = await self.get_mood_chain_by_id(mood_chain_id, owner_id)
        if not mood_chain:
            raise MoodChainNotFoundError(f"Mood chain not found: {mood_chain_id}")

        song = await self._get_song(song_id, owner_id)
        if not song:
            raise SongNotFoundError(f"Song not found: {song_id}")

        # Check if song is already in mood chain
        existing = await self._get_mood_chain_song(mood_chain_id, song_id)
        if existing:
            raise SongAlreadyInMoodChainError(
                f"Song {song_id} is already in mood chain {mood_chain_id}"
            )

        # Determine position
        if position is None:
            # Add to end
            position = mood_chain.song_count

        # Shift positions of songs at or after this position
        result = await self.db.execute(
            select(MoodChainSong)
            .where(
                MoodChainSong.mood_chain_id == mood_chain_id,
                MoodChainSong.position >= position,
            )
            .order_by(MoodChainSong.position.desc())
        )
        songs_to_shift = result.scalars().all()
        for mcs in songs_to_shift:
            mcs.position += 1

        # Add the song
        mood_chain_song = MoodChainSong(
            mood_chain_id=mood_chain_id,
            song_id=song_id,
            position=position,
        )
        self.db.add(mood_chain_song)

        await self.db.flush()

        # Recalculate stats (after flush to get correct data)
        await self._recalculate_mood_chain_stats(mood_chain)
        await self.db.flush()

        # Fetch fresh data with refresh=True to bypass identity map cache
        return await self.get_mood_chain_with_songs(
            mood_chain_id, owner_id, refresh=True
        )  # type: ignore

    async def remove_song_from_mood_chain(
        self,
        mood_chain_id: UUID,
        song_id: UUID,
        owner_id: UUID,
    ) -> MoodChain:
        """Remove a song from a mood chain.

        Args:
            mood_chain_id: Mood chain UUID.
            song_id: Song UUID.
            owner_id: Owner UUID.

        Returns:
            Updated mood chain.

        Raises:
            MoodChainNotFoundError: If mood chain not found.
            SongNotInMoodChainError: If song not in mood chain.
        """
        mood_chain = await self.get_mood_chain_by_id(mood_chain_id, owner_id)
        if not mood_chain:
            raise MoodChainNotFoundError(f"Mood chain not found: {mood_chain_id}")

        mood_chain_song = await self._get_mood_chain_song(mood_chain_id, song_id)
        if not mood_chain_song:
            raise SongNotInMoodChainError(
                f"Song {song_id} is not in mood chain {mood_chain_id}"
            )

        removed_position = mood_chain_song.position
        await self.db.delete(mood_chain_song)

        # Also remove transitions involving this song
        await self.db.execute(
            select(MoodChainTransition)
            .where(
                MoodChainTransition.mood_chain_id == mood_chain_id,
                (MoodChainTransition.from_song_id == song_id)
                | (MoodChainTransition.to_song_id == song_id),
            )
            .execution_options(synchronize_session="fetch")
        )

        # Shift positions of songs after the removed one
        result = await self.db.execute(
            select(MoodChainSong)
            .where(
                MoodChainSong.mood_chain_id == mood_chain_id,
                MoodChainSong.position > removed_position,
            )
            .order_by(MoodChainSong.position.asc())
        )
        songs_to_shift = result.scalars().all()
        for mcs in songs_to_shift:
            mcs.position -= 1

        await self.db.flush()

        # Recalculate stats (after flush to get correct data)
        await self._recalculate_mood_chain_stats(mood_chain)
        await self.db.flush()

        # Fetch fresh data with refresh=True to bypass identity map cache
        return await self.get_mood_chain_with_songs(
            mood_chain_id, owner_id, refresh=True
        )  # type: ignore

    async def reorder_mood_chain_songs(
        self,
        mood_chain_id: UUID,
        song_ids: list[UUID],
        owner_id: UUID,
    ) -> MoodChain:
        """Reorder songs in a mood chain.

        Args:
            mood_chain_id: Mood chain UUID.
            song_ids: List of song IDs in new order.
            owner_id: Owner UUID.

        Returns:
            Updated mood chain.

        Raises:
            MoodChainNotFoundError: If mood chain not found.
            ValueError: If song_ids don't match mood chain songs.
        """
        mood_chain = await self.get_mood_chain_with_songs(mood_chain_id, owner_id)
        if not mood_chain:
            raise MoodChainNotFoundError(f"Mood chain not found: {mood_chain_id}")

        # Verify all songs are in mood chain
        current_song_ids = {mcs.song_id for mcs in mood_chain.mood_chain_songs}
        if set(song_ids) != current_song_ids:
            raise ValueError("Provided song IDs don't match songs in mood chain")

        # Update positions
        for position, song_id in enumerate(song_ids):
            for mcs in mood_chain.mood_chain_songs:
                if mcs.song_id == song_id:
                    mcs.position = position
                    break

        await self.db.flush()

        # Fetch fresh data with refresh=True to bypass identity map cache
        return await self.get_mood_chain_with_songs(
            mood_chain_id, owner_id, refresh=True
        )  # type: ignore

    async def update_transitions(
        self,
        mood_chain_id: UUID,
        transitions: list[MoodChainTransitionBase],
        owner_id: UUID,
    ) -> MoodChain:
        """Update transitions in a mood chain.

        Args:
            mood_chain_id: Mood chain UUID.
            transitions: List of transitions to update.
            owner_id: Owner UUID.

        Returns:
            Updated mood chain.

        Raises:
            MoodChainNotFoundError: If mood chain not found.
        """
        mood_chain = await self.get_mood_chain_with_songs(mood_chain_id, owner_id)
        if not mood_chain:
            raise MoodChainNotFoundError(f"Mood chain not found: {mood_chain_id}")

        # Get all song IDs in the mood chain
        song_ids_in_chain = {mcs.song_id for mcs in mood_chain.mood_chain_songs}

        for transition_data in transitions:
            # Verify both songs are in the mood chain
            if (
                transition_data.from_song_id not in song_ids_in_chain
                or transition_data.to_song_id not in song_ids_in_chain
            ):
                continue  # Skip invalid transitions

            # Check if transition exists
            result = await self.db.execute(
                select(MoodChainTransition).where(
                    MoodChainTransition.mood_chain_id == mood_chain_id,
                    MoodChainTransition.from_song_id == transition_data.from_song_id,
                    MoodChainTransition.to_song_id == transition_data.to_song_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.weight = transition_data.weight
            else:
                new_transition = MoodChainTransition(
                    mood_chain_id=mood_chain_id,
                    from_song_id=transition_data.from_song_id,
                    to_song_id=transition_data.to_song_id,
                    weight=transition_data.weight,
                )
                self.db.add(new_transition)

        await self.db.flush()

        return await self.get_mood_chain_with_songs(
            mood_chain_id, owner_id, refresh=True
        )  # type: ignore

    async def create_from_history(
        self,
        owner_id: UUID,
        data: MoodChainFromHistoryRequest,
    ) -> MoodChain:
        """Create a mood chain from listening history.

        Analyzes sequential listenings and calculates transition weights
        based on how often songs were played in sequence.

        Args:
            owner_id: Owner UUID.
            data: Request data with filters.

        Returns:
            Created mood chain.
        """
        # Query listening history
        query = (
            select(ListeningHistory)
            .where(ListeningHistory.user_id == owner_id)
            .order_by(ListeningHistory.played_at.asc())
        )

        if data.from_date:
            query = query.where(ListeningHistory.played_at >= data.from_date)
        if data.to_date:
            query = query.where(ListeningHistory.played_at <= data.to_date)

        result = await self.db.execute(query)
        history_entries = list(result.scalars().all())

        # Count play counts for each song
        song_play_counts: dict[UUID, int] = defaultdict(int)
        for entry in history_entries:
            song_play_counts[entry.song_id] += 1

        # Filter songs by minimum plays
        valid_songs = {
            song_id
            for song_id, count in song_play_counts.items()
            if count >= data.min_plays
        }

        if not valid_songs:
            # Create empty mood chain
            mood_chain = MoodChain(
                owner_id=owner_id,
                name=data.name,
                description=data.description,
                is_auto_generated=True,
                source_history_start=data.from_date,
                source_history_end=data.to_date,
            )
            self.db.add(mood_chain)
            await self.db.flush()
            return mood_chain

        # Count transitions
        transition_counts: dict[tuple[UUID, UUID], int] = defaultdict(int)
        prev_song_id: UUID | None = None

        for entry in history_entries:
            if entry.song_id in valid_songs:
                if prev_song_id is not None and prev_song_id in valid_songs:
                    transition_counts[(prev_song_id, entry.song_id)] += 1
                prev_song_id = entry.song_id

        # Normalize weights (0.0-1.0) per source song
        from_song_totals: dict[UUID, int] = defaultdict(int)
        for (from_id, _), count in transition_counts.items():
            from_song_totals[from_id] += count

        transition_weights: dict[tuple[UUID, UUID], float] = {}
        for (from_id, to_id), count in transition_counts.items():
            if from_song_totals[from_id] > 0:
                transition_weights[(from_id, to_id)] = count / from_song_totals[from_id]

        # Create mood chain
        mood_chain = MoodChain(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            is_auto_generated=True,
            source_history_start=data.from_date,
            source_history_end=data.to_date,
        )
        self.db.add(mood_chain)
        await self.db.flush()

        # Add songs (ordered by play count, most played first)
        sorted_songs = sorted(
            valid_songs,
            key=lambda x: song_play_counts[x],
            reverse=True,
        )

        for position, song_id in enumerate(sorted_songs):
            mood_chain_song = MoodChainSong(
                mood_chain_id=mood_chain.id,
                song_id=song_id,
                position=position,
            )
            self.db.add(mood_chain_song)

        # Add transitions
        for (from_id, to_id), weight in transition_weights.items():
            transition = MoodChainTransition(
                mood_chain_id=mood_chain.id,
                from_song_id=from_id,
                to_song_id=to_id,
                weight=weight,
            )
            self.db.add(transition)

        await self.db.flush()
        await self._recalculate_mood_chain_stats(mood_chain)
        await self.db.flush()

        return await self.get_mood_chain_with_songs(
            mood_chain.id, owner_id, refresh=True
        )  # type: ignore

    async def get_next_song_suggestions(
        self,
        mood_chain_id: UUID,
        current_song_id: UUID,
        owner_id: UUID,
        exclude_recent: int = 0,
    ) -> list[SongSuggestion]:
        """Get next song suggestions based on mood chain.

        Args:
            mood_chain_id: Mood chain UUID.
            current_song_id: Current song UUID.
            owner_id: Owner UUID.
            exclude_recent: Number of recent songs to exclude.

        Returns:
            List of song suggestions with weights and reasons.
        """
        mood_chain = await self.get_mood_chain_with_songs(mood_chain_id, owner_id)
        if not mood_chain:
            raise MoodChainNotFoundError(f"Mood chain not found: {mood_chain_id}")

        # Get all songs in the chain
        song_ids_in_chain = [mcs.song_id for mcs in mood_chain.mood_chain_songs]
        if not song_ids_in_chain:
            return []

        # Get the current song
        current_song = await self._get_song(current_song_id, owner_id)
        if not current_song:
            raise SongNotFoundError(f"Song not found: {current_song_id}")

        # Get transitions from current song
        result = await self.db.execute(
            select(MoodChainTransition).where(
                MoodChainTransition.mood_chain_id == mood_chain_id,
                MoodChainTransition.from_song_id == current_song_id,
            )
        )
        transitions = {t.to_song_id: t for t in result.scalars().all()}

        # Build suggestions
        suggestions = []
        for mcs in mood_chain.mood_chain_songs:
            if mcs.song_id == current_song_id:
                continue  # Skip current song

            song = mcs.song

            # Calculate weight based on transition style
            weight = 0.5  # Default weight
            reason = "default suggestion"

            if mcs.song_id in transitions:
                weight = transitions[mcs.song_id].weight
                reason = "high transition weight"
            elif mood_chain.transition_style == TransitionStyle.SMOOTH:
                # Calculate similarity based on energy and valence
                if (
                    song.energy is not None
                    and song.valence is not None
                    and current_song.energy is not None
                    and current_song.valence is not None
                ):
                    energy_diff = abs(song.energy - current_song.energy)
                    valence_diff = abs(song.valence - current_song.valence)
                    similarity = 1.0 - (energy_diff + valence_diff) / 2.0
                    weight = max(0.0, similarity)
                    reason = "similar energy/valence"
            elif mood_chain.transition_style == TransitionStyle.ENERGY_FLOW:
                # Prefer songs with slightly higher energy
                if song.energy is not None and current_song.energy is not None:
                    if song.energy >= current_song.energy:
                        weight = 0.7 + (song.energy - current_song.energy) * 0.3
                        reason = "increasing energy"
                    else:
                        weight = 0.3
                        reason = "lower energy"
            elif mood_chain.transition_style == TransitionStyle.GENRE_MATCH:
                # Prefer songs with same genre
                if song.genre and current_song.genre:
                    if song.genre == current_song.genre:
                        weight = 0.9
                        reason = "same genre"
                    else:
                        weight = 0.3
                        reason = "different genre"
            elif mood_chain.transition_style == TransitionStyle.RANDOM:
                weight = random.random()
                reason = "random selection"

            suggestions.append(
                SongSuggestion(
                    song_id=song.id,
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    duration_seconds=song.duration_seconds,
                    cover_art_path=song.cover_art_path,
                    weight=weight,
                    reason=reason,
                )
            )

        # Sort by weight descending
        suggestions.sort(key=lambda x: x["weight"], reverse=True)

        # Exclude recent if specified (just limit the results)
        if exclude_recent > 0 and len(suggestions) > exclude_recent:
            suggestions = suggestions[:exclude_recent]

        return suggestions

    async def record_transition_played(
        self,
        mood_chain_id: UUID,
        from_song_id: UUID,
        to_song_id: UUID,
        owner_id: UUID,
    ) -> bool:
        """Record that a transition was played.

        Updates the play_count for the transition and adjusts weights.

        Args:
            mood_chain_id: Mood chain UUID.
            from_song_id: From song UUID.
            to_song_id: To song UUID.
            owner_id: Owner UUID.

        Returns:
            True if successful.
        """
        mood_chain = await self.get_mood_chain_by_id(mood_chain_id, owner_id)
        if not mood_chain:
            raise MoodChainNotFoundError(f"Mood chain not found: {mood_chain_id}")

        # Check if transition exists
        result = await self.db.execute(
            select(MoodChainTransition).where(
                MoodChainTransition.mood_chain_id == mood_chain_id,
                MoodChainTransition.from_song_id == from_song_id,
                MoodChainTransition.to_song_id == to_song_id,
            )
        )
        transition = result.scalar_one_or_none()

        if transition:
            transition.play_count += 1
            # Increase weight slightly with each play (capped at 1.0)
            transition.weight = min(1.0, transition.weight + 0.05)
        else:
            # Create new transition with initial weight
            transition = MoodChainTransition(
                mood_chain_id=mood_chain_id,
                from_song_id=from_song_id,
                to_song_id=to_song_id,
                weight=0.6,  # Slightly above default
                play_count=1,
            )
            self.db.add(transition)

        # Update mood chain play stats
        mood_chain.play_count += 1
        mood_chain.last_played_at = datetime.now(UTC)

        await self.db.flush()
        return True
