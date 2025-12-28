"""Statistics API endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.song import SongResponse
from app.schemas.stats import (
    ContextType,
    ListeningHistoryItemResponse,
    ListeningHistoryResponse,
    PlayRecordRequest,
    PlayRecordResponse,
    StatsOverviewResponse,
    StatsPeriod,
    TopArtistItem,
    TopArtistsResponse,
    TopSongItem,
    TopSongsResponse,
)
from app.services.stats import SongNotFoundError, StatsService

router = APIRouter()


@router.post(
    "/play",
    response_model=PlayRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a play event",
    description="Record a song play event. Updates play_count and last_played_at.",
)
async def record_play(
    play_data: PlayRecordRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayRecordResponse:
    """Record a song play event.

    Args:
        play_data: Play event data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Play record confirmation.

    Raises:
        HTTPException: If song not found.
    """
    stats_service = StatsService(db)

    try:
        history = await stats_service.record_play(
            user_id=current_user.id,
            song_id=play_data.song_id,
            duration_listened_seconds=play_data.duration_listened_seconds,
            completed=play_data.completed,
            context_type=play_data.context_type,
            context_id=play_data.context_id,
            device_type=play_data.device_type,
        )
        return PlayRecordResponse(
            success=True,
            id=history.id,
            played_at=history.played_at,
        )
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


@router.get(
    "/history",
    response_model=ListeningHistoryResponse,
    summary="Get listening history",
    description="Get paginated listening history with optional date filters.",
)
async def get_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    from_date: Annotated[datetime | None, Query(description="Filter from date")] = None,
    to_date: Annotated[datetime | None, Query(description="Filter to date")] = None,
) -> ListeningHistoryResponse:
    """Get listening history with pagination.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        page: Page number.
        limit: Items per page.
        from_date: Filter from date.
        to_date: Filter to date.

    Returns:
        Paginated listening history.
    """
    stats_service = StatsService(db)

    history, total = await stats_service.get_history(
        user_id=current_user.id,
        page=page,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
    )

    pages = (total + limit - 1) // limit if limit > 0 else 0

    items = []
    for h in history:
        item = ListeningHistoryItemResponse(
            id=h.id,
            song_id=h.song_id,
            played_at=h.played_at,
            played_duration_seconds=h.played_duration_seconds,
            completed=h.completed,
            skipped=h.skipped,
            context_type=ContextType(h.context_type.value) if h.context_type else None,
            context_id=h.context_id,
            device_type=h.device_type,
            song=SongResponse.model_validate(h.song),
        )
        items.append(item)

    return ListeningHistoryResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get(
    "/overview",
    response_model=StatsOverviewResponse,
    summary="Get statistics overview",
    description="Get aggregated statistics for the specified period.",
)
async def get_overview(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    period: Annotated[
        StatsPeriod,
        Query(description="Statistics period"),
    ] = StatsPeriod.ALL,
) -> StatsOverviewResponse:
    """Get statistics overview.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        period: Statistics period (day, week, month, year, all).

    Returns:
        Statistics overview.
    """
    stats_service = StatsService(db)
    overview = await stats_service.get_overview(
        user_id=current_user.id,
        period=period,
    )
    return StatsOverviewResponse(**overview)


@router.get(
    "/top-songs",
    response_model=TopSongsResponse,
    summary="Get top songs",
    description="Get most played songs for the specified period.",
)
async def get_top_songs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    period: Annotated[
        StatsPeriod,
        Query(description="Statistics period"),
    ] = StatsPeriod.ALL,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of songs"),
    ] = 10,
) -> TopSongsResponse:
    """Get top songs by play count.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        period: Statistics period (day, week, month, year, all).
        limit: Maximum number of songs to return.

    Returns:
        Top songs list.
    """
    stats_service = StatsService(db)
    top_songs = await stats_service.get_top_songs(
        user_id=current_user.id,
        period=period,
        limit=limit,
    )

    items = [
        TopSongItem(
            song=SongResponse.model_validate(item["song"]),
            play_count=item["play_count"],
        )
        for item in top_songs
    ]

    return TopSongsResponse(items=items)


@router.get(
    "/top-artists",
    response_model=TopArtistsResponse,
    summary="Get top artists",
    description="Get most played artists for the specified period.",
)
async def get_top_artists(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    period: Annotated[
        StatsPeriod,
        Query(description="Statistics period"),
    ] = StatsPeriod.ALL,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of artists"),
    ] = 10,
) -> TopArtistsResponse:
    """Get top artists by play count.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        period: Statistics period (day, week, month, year, all).
        limit: Maximum number of artists to return.

    Returns:
        Top artists list.
    """
    stats_service = StatsService(db)
    top_artists = await stats_service.get_top_artists(
        user_id=current_user.id,
        period=period,
        limit=limit,
    )

    items = [
        TopArtistItem(
            artist=item["artist"],
            play_count=item["play_count"],
            songs=[SongResponse.model_validate(song) for song in item["songs"]],
        )
        for item in top_artists
    ]

    return TopArtistsResponse(items=items)
