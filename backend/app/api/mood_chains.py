"""Mood chains API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.mood_chain import MoodChain
from app.schemas.mood_chain import (
    AddSongToMoodChainRequest,
    MoodChainCreate,
    MoodChainDetailResponse,
    MoodChainFromHistoryRequest,
    MoodChainListResponse,
    MoodChainResponse,
    MoodChainSongWithDetailsResponse,
    MoodChainTransitionResponse,
    MoodChainUpdate,
    NextSongResponse,
    NextSongSuggestion,
    ReorderMoodChainSongsRequest,
    TransitionPlayedRequest,
    TransitionPlayedResponse,
    UpdateTransitionsRequest,
)
from app.services.mood_chain import (
    MoodChainNotFoundError,
    MoodChainService,
    SongAlreadyInMoodChainError,
    SongNotFoundError,
    SongNotInMoodChainError,
)

router = APIRouter()


def _convert_mood_chain_songs_to_response(
    mood_chain: MoodChain,
) -> list[MoodChainSongWithDetailsResponse]:
    """Convert mood chain songs to response format with song details."""
    songs = []
    for mcs in sorted(mood_chain.mood_chain_songs, key=lambda x: x.position):
        songs.append(
            MoodChainSongWithDetailsResponse(
                song_id=mcs.song_id,
                position=mcs.position,
                transition_weight=mcs.transition_weight,
                added_at=mcs.added_at,
                title=mcs.song.title,
                artist=mcs.song.artist,
                album=mcs.song.album,
                duration_seconds=mcs.song.duration_seconds,
                cover_art_path=mcs.song.cover_art_path,
                energy=mcs.song.energy,
                valence=mcs.song.valence,
                bpm=mcs.song.bpm,
                genre=mcs.song.genre,
            )
        )
    return songs


def _convert_transitions_to_response(
    mood_chain: MoodChain,
) -> list[MoodChainTransitionResponse]:
    """Convert mood chain transitions to response format."""
    return [
        MoodChainTransitionResponse(
            id=t.id,
            from_song_id=t.from_song_id,
            to_song_id=t.to_song_id,
            weight=t.weight,
            play_count=t.play_count,
        )
        for t in mood_chain.mood_chain_transitions
    ]


@router.get(
    "",
    response_model=MoodChainListResponse,
    summary="List mood chains",
    description="Get a paginated list of user's mood chains.",
)
async def list_mood_chains(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> MoodChainListResponse:
    """List mood chains with pagination.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        page: Page number.
        limit: Items per page.

    Returns:
        Paginated list of mood chains.
    """
    service = MoodChainService(db)
    mood_chains, total = await service.get_mood_chains(
        owner_id=current_user.id,
        page=page,
        limit=limit,
    )

    pages = (total + limit - 1) // limit if limit > 0 else 0

    return MoodChainListResponse(
        items=[MoodChainResponse.model_validate(mc) for mc in mood_chains],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.post(
    "",
    response_model=MoodChainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create mood chain",
    description="Create a new mood chain.",
)
async def create_mood_chain(
    data: MoodChainCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodChainResponse:
    """Create a new mood chain.

    Args:
        data: Mood chain creation data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Created mood chain.
    """
    service = MoodChainService(db)
    mood_chain = await service.create_mood_chain(
        owner_id=current_user.id,
        data=data,
    )
    return MoodChainResponse.model_validate(mood_chain)


@router.get(
    "/{mood_chain_id}",
    response_model=MoodChainDetailResponse,
    summary="Get mood chain",
    description="Get mood chain details with songs and transitions.",
)
async def get_mood_chain(
    mood_chain_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodChainDetailResponse:
    """Get mood chain details with songs and transitions.

    Args:
        mood_chain_id: Mood chain UUID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Mood chain with songs and transitions.

    Raises:
        HTTPException: If mood chain not found.
    """
    service = MoodChainService(db)
    mood_chain = await service.get_mood_chain_with_songs(mood_chain_id, current_user.id)

    if not mood_chain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Mood chain not found"},
        )

    songs = _convert_mood_chain_songs_to_response(mood_chain)
    transitions = _convert_transitions_to_response(mood_chain)

    return MoodChainDetailResponse(
        id=mood_chain.id,
        name=mood_chain.name,
        description=mood_chain.description,
        cover_image_path=mood_chain.cover_image_path,
        transition_style=mood_chain.transition_style,
        auto_advance=mood_chain.auto_advance,
        auto_advance_delay_seconds=mood_chain.auto_advance_delay_seconds,
        is_auto_generated=mood_chain.is_auto_generated,
        song_count=mood_chain.song_count,
        play_count=mood_chain.play_count,
        last_played_at=mood_chain.last_played_at,
        created_at=mood_chain.created_at,
        updated_at=mood_chain.updated_at,
        songs=songs,
        transitions=transitions,
    )


@router.patch(
    "/{mood_chain_id}",
    response_model=MoodChainResponse,
    summary="Update mood chain",
    description="Update mood chain metadata.",
)
async def update_mood_chain(
    mood_chain_id: UUID,
    data: MoodChainUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodChainResponse:
    """Update mood chain metadata.

    Args:
        mood_chain_id: Mood chain UUID.
        data: Update data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated mood chain.

    Raises:
        HTTPException: If mood chain not found.
    """
    service = MoodChainService(db)

    try:
        mood_chain = await service.update_mood_chain(
            mood_chain_id, current_user.id, data
        )
        return MoodChainResponse.model_validate(mood_chain)
    except MoodChainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


@router.delete(
    "/{mood_chain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete mood chain",
    description="Delete a mood chain.",
)
async def delete_mood_chain(
    mood_chain_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a mood chain.

    Args:
        mood_chain_id: Mood chain UUID.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException: If mood chain not found.
    """
    service = MoodChainService(db)

    try:
        await service.delete_mood_chain(mood_chain_id, current_user.id)
    except MoodChainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


@router.post(
    "/{mood_chain_id}/songs",
    response_model=MoodChainDetailResponse,
    summary="Add song to mood chain",
    description="Add a song to a mood chain.",
)
async def add_song_to_mood_chain(
    mood_chain_id: UUID,
    data: AddSongToMoodChainRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodChainDetailResponse:
    """Add a song to a mood chain.

    Args:
        mood_chain_id: Mood chain UUID.
        data: Add song request data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated mood chain with songs.

    Raises:
        HTTPException: If mood chain or song not found, or song already in chain.
    """
    service = MoodChainService(db)

    try:
        mood_chain = await service.add_song_to_mood_chain(
            mood_chain_id=mood_chain_id,
            song_id=data.song_id,
            owner_id=current_user.id,
            position=data.position,
        )
        songs = _convert_mood_chain_songs_to_response(mood_chain)
        transitions = _convert_transitions_to_response(mood_chain)

        return MoodChainDetailResponse(
            id=mood_chain.id,
            name=mood_chain.name,
            description=mood_chain.description,
            cover_image_path=mood_chain.cover_image_path,
            transition_style=mood_chain.transition_style,
            auto_advance=mood_chain.auto_advance,
            auto_advance_delay_seconds=mood_chain.auto_advance_delay_seconds,
            is_auto_generated=mood_chain.is_auto_generated,
            song_count=mood_chain.song_count,
            play_count=mood_chain.play_count,
            last_played_at=mood_chain.last_played_at,
            created_at=mood_chain.created_at,
            updated_at=mood_chain.updated_at,
            songs=songs,
            transitions=transitions,
        )
    except MoodChainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MOOD_CHAIN_NOT_FOUND", "message": str(e)},
        ) from e
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SONG_NOT_FOUND", "message": str(e)},
        ) from e
    except SongAlreadyInMoodChainError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SONG_ALREADY_IN_MOOD_CHAIN", "message": str(e)},
        ) from e


@router.delete(
    "/{mood_chain_id}/songs/{song_id}",
    response_model=MoodChainDetailResponse,
    summary="Remove song from mood chain",
    description="Remove a song from a mood chain.",
)
async def remove_song_from_mood_chain(
    mood_chain_id: UUID,
    song_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodChainDetailResponse:
    """Remove a song from a mood chain.

    Args:
        mood_chain_id: Mood chain UUID.
        song_id: Song UUID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated mood chain with songs.

    Raises:
        HTTPException: If mood chain not found or song not in chain.
    """
    service = MoodChainService(db)

    try:
        mood_chain = await service.remove_song_from_mood_chain(
            mood_chain_id=mood_chain_id,
            song_id=song_id,
            owner_id=current_user.id,
        )
        songs = _convert_mood_chain_songs_to_response(mood_chain)
        transitions = _convert_transitions_to_response(mood_chain)

        return MoodChainDetailResponse(
            id=mood_chain.id,
            name=mood_chain.name,
            description=mood_chain.description,
            cover_image_path=mood_chain.cover_image_path,
            transition_style=mood_chain.transition_style,
            auto_advance=mood_chain.auto_advance,
            auto_advance_delay_seconds=mood_chain.auto_advance_delay_seconds,
            is_auto_generated=mood_chain.is_auto_generated,
            song_count=mood_chain.song_count,
            play_count=mood_chain.play_count,
            last_played_at=mood_chain.last_played_at,
            created_at=mood_chain.created_at,
            updated_at=mood_chain.updated_at,
            songs=songs,
            transitions=transitions,
        )
    except MoodChainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MOOD_CHAIN_NOT_FOUND", "message": str(e)},
        ) from e
    except SongNotInMoodChainError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SONG_NOT_IN_MOOD_CHAIN", "message": str(e)},
        ) from e


@router.put(
    "/{mood_chain_id}/songs/order",
    response_model=MoodChainDetailResponse,
    summary="Reorder mood chain songs",
    description="Reorder songs in a mood chain.",
)
async def reorder_mood_chain_songs(
    mood_chain_id: UUID,
    data: ReorderMoodChainSongsRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodChainDetailResponse:
    """Reorder songs in a mood chain.

    Args:
        mood_chain_id: Mood chain UUID.
        data: Reorder request with song IDs in new order.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated mood chain with songs.

    Raises:
        HTTPException: If mood chain not found or song IDs don't match.
    """
    service = MoodChainService(db)

    try:
        mood_chain = await service.reorder_mood_chain_songs(
            mood_chain_id=mood_chain_id,
            song_ids=data.song_ids,
            owner_id=current_user.id,
        )
        songs = _convert_mood_chain_songs_to_response(mood_chain)
        transitions = _convert_transitions_to_response(mood_chain)

        return MoodChainDetailResponse(
            id=mood_chain.id,
            name=mood_chain.name,
            description=mood_chain.description,
            cover_image_path=mood_chain.cover_image_path,
            transition_style=mood_chain.transition_style,
            auto_advance=mood_chain.auto_advance,
            auto_advance_delay_seconds=mood_chain.auto_advance_delay_seconds,
            is_auto_generated=mood_chain.is_auto_generated,
            song_count=mood_chain.song_count,
            play_count=mood_chain.play_count,
            last_played_at=mood_chain.last_played_at,
            created_at=mood_chain.created_at,
            updated_at=mood_chain.updated_at,
            songs=songs,
            transitions=transitions,
        )
    except MoodChainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MOOD_CHAIN_NOT_FOUND", "message": str(e)},
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_SONG_IDS", "message": str(e)},
        ) from e


@router.put(
    "/{mood_chain_id}/transitions",
    response_model=MoodChainDetailResponse,
    summary="Update transitions",
    description="Update transition weights in a mood chain.",
)
async def update_transitions(
    mood_chain_id: UUID,
    data: UpdateTransitionsRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodChainDetailResponse:
    """Update transition weights in a mood chain.

    Args:
        mood_chain_id: Mood chain UUID.
        data: Transitions update request.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated mood chain with transitions.

    Raises:
        HTTPException: If mood chain not found.
    """
    service = MoodChainService(db)

    try:
        mood_chain = await service.update_transitions(
            mood_chain_id=mood_chain_id,
            transitions=data.transitions,
            owner_id=current_user.id,
        )
        songs = _convert_mood_chain_songs_to_response(mood_chain)
        transitions = _convert_transitions_to_response(mood_chain)

        return MoodChainDetailResponse(
            id=mood_chain.id,
            name=mood_chain.name,
            description=mood_chain.description,
            cover_image_path=mood_chain.cover_image_path,
            transition_style=mood_chain.transition_style,
            auto_advance=mood_chain.auto_advance,
            auto_advance_delay_seconds=mood_chain.auto_advance_delay_seconds,
            is_auto_generated=mood_chain.is_auto_generated,
            song_count=mood_chain.song_count,
            play_count=mood_chain.play_count,
            last_played_at=mood_chain.last_played_at,
            created_at=mood_chain.created_at,
            updated_at=mood_chain.updated_at,
            songs=songs,
            transitions=transitions,
        )
    except MoodChainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MOOD_CHAIN_NOT_FOUND", "message": str(e)},
        ) from e


@router.post(
    "/from-history",
    response_model=MoodChainDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create from history",
    description="Create a mood chain from listening history.",
)
async def create_from_history(
    data: MoodChainFromHistoryRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MoodChainDetailResponse:
    """Create a mood chain from listening history.

    Analyzes sequential listenings and calculates transition weights.

    Args:
        data: Request data with filters.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Created mood chain with songs and transitions.
    """
    service = MoodChainService(db)
    mood_chain = await service.create_from_history(
        owner_id=current_user.id,
        data=data,
    )

    songs = _convert_mood_chain_songs_to_response(mood_chain)
    transitions = _convert_transitions_to_response(mood_chain)

    return MoodChainDetailResponse(
        id=mood_chain.id,
        name=mood_chain.name,
        description=mood_chain.description,
        cover_image_path=mood_chain.cover_image_path,
        transition_style=mood_chain.transition_style,
        auto_advance=mood_chain.auto_advance,
        auto_advance_delay_seconds=mood_chain.auto_advance_delay_seconds,
        is_auto_generated=mood_chain.is_auto_generated,
        song_count=mood_chain.song_count,
        play_count=mood_chain.play_count,
        last_played_at=mood_chain.last_played_at,
        created_at=mood_chain.created_at,
        updated_at=mood_chain.updated_at,
        songs=songs,
        transitions=transitions,
    )


@router.get(
    "/{mood_chain_id}/next",
    response_model=NextSongResponse,
    summary="Get next song suggestions",
    description="Get next song suggestions based on mood chain.",
)
async def get_next_song(
    mood_chain_id: UUID,
    current_song_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    exclude_recent: Annotated[int, Query(ge=0)] = 0,
) -> NextSongResponse:
    """Get next song suggestions.

    Args:
        mood_chain_id: Mood chain UUID.
        current_song_id: Current song UUID.
        current_user: Current authenticated user.
        db: Database session.
        exclude_recent: Number of recent songs to exclude.

    Returns:
        Next song suggestions with weights and reasons.

    Raises:
        HTTPException: If mood chain or song not found.
    """
    service = MoodChainService(db)

    try:
        suggestions = await service.get_next_song_suggestions(
            mood_chain_id=mood_chain_id,
            current_song_id=current_song_id,
            owner_id=current_user.id,
            exclude_recent=exclude_recent,
        )

        return NextSongResponse(
            suggestions=[
                NextSongSuggestion(
                    song_id=s["song_id"],
                    title=s["title"],
                    artist=s["artist"],
                    album=s["album"],
                    duration_seconds=s["duration_seconds"],
                    cover_art_path=s["cover_art_path"],
                    weight=s["weight"],
                    reason=s["reason"],
                )
                for s in suggestions
            ]
        )
    except MoodChainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MOOD_CHAIN_NOT_FOUND", "message": str(e)},
        ) from e
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SONG_NOT_FOUND", "message": str(e)},
        ) from e


@router.post(
    "/{mood_chain_id}/transition-played",
    response_model=TransitionPlayedResponse,
    summary="Record transition played",
    description="Record that a transition was played.",
)
async def record_transition_played(
    mood_chain_id: UUID,
    data: TransitionPlayedRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransitionPlayedResponse:
    """Record that a transition was played.

    Updates play_count for the transition and adjusts weights.

    Args:
        mood_chain_id: Mood chain UUID.
        data: Transition played request.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Success response.

    Raises:
        HTTPException: If mood chain not found.
    """
    service = MoodChainService(db)

    try:
        success = await service.record_transition_played(
            mood_chain_id=mood_chain_id,
            from_song_id=data.from_song_id,
            to_song_id=data.to_song_id,
            owner_id=current_user.id,
        )
        return TransitionPlayedResponse(success=success)
    except MoodChainNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MOOD_CHAIN_NOT_FOUND", "message": str(e)},
        ) from e
