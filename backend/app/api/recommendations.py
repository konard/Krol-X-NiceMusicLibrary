"""Recommendations API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.recommendation import (
    DiscoverResponse,
    DiscoverSection,
    DiscoverSectionType,
    MoodType,
    PersonalMixResponse,
    SimilarSongItem,
    SimilarSongsResponse,
)
from app.schemas.song import SongResponse
from app.services.recommendation import (
    RecommendationService,
    SongNotFoundError,
)

router = APIRouter()


# Section titles mapping
SECTION_TITLES = {
    DiscoverSectionType.LONG_TIME_NO_LISTEN: "Давно не слушали",
    DiscoverSectionType.BASED_ON_FAVORITE: "На основе любимого",
    DiscoverSectionType.HIDDEN_GEMS: "Скрытые жемчужины",
}


@router.get(
    "/similar/{song_id}",
    response_model=SimilarSongsResponse,
    summary="Get similar songs",
    description=(
        "Get songs similar to the specified song based on genre, BPM, energy, "
        "valence, and listening history."
    ),
)
async def get_similar_songs(
    song_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50, description="Maximum songs")] = 10,
) -> SimilarSongsResponse:
    """Get similar songs.

    Args:
        song_id: Source song UUID.
        current_user: Current authenticated user.
        db: Database session.
        limit: Maximum number of similar songs to return.

    Returns:
        Similar songs with similarity scores and reasons.

    Raises:
        HTTPException: If song not found.
    """
    recommendation_service = RecommendationService(db)

    try:
        source_song, similar_songs = await recommendation_service.get_similar_songs(
            song_id=song_id,
            user_id=current_user.id,
            limit=limit,
        )

        items = [
            SimilarSongItem(
                song=SongResponse.model_validate(song),
                similarity_score=round(score, 2),
                reasons=reasons if reasons else ["similar characteristics"],
            )
            for song, score, reasons in similar_songs
        ]

        return SimilarSongsResponse(
            source_song=SongResponse.model_validate(source_song),
            items=items,
        )
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


@router.get(
    "/discover",
    response_model=DiscoverResponse,
    summary="Get discovery recommendations",
    description=(
        "Get personalized discovery recommendations organized in sections: "
        "songs you haven't listened to in a while, songs based on your favorites, "
        "and hidden gems from your library."
    ),
)
async def get_discover_recommendations(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=20, description="Songs per section")] = 10,
) -> DiscoverResponse:
    """Get discovery recommendations.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        limit: Maximum songs per section.

    Returns:
        Discovery recommendations organized in sections.
    """
    recommendation_service = RecommendationService(db)

    sections_data = await recommendation_service.get_discover_recommendations(
        user_id=current_user.id,
        limit=limit,
    )

    sections = []
    for section_type, songs in sections_data.items():
        if songs:  # Only include non-empty sections
            sections.append(
                DiscoverSection(
                    type=section_type,
                    title=SECTION_TITLES.get(section_type, section_type.value),
                    items=[SongResponse.model_validate(song) for song in songs],
                )
            )

    return DiscoverResponse(sections=sections)


@router.get(
    "/mix",
    response_model=PersonalMixResponse,
    summary="Get personal mix",
    description=(
        "Generate a personal mix of songs based on mood and target duration. "
        "The mix ensures variety by limiting tracks per artist."
    ),
)
async def get_personal_mix(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    mood: Annotated[
        MoodType | None,
        Query(description="Filter by mood"),
    ] = None,
    duration_minutes: Annotated[
        int,
        Query(ge=5, le=180, description="Target duration in minutes"),
    ] = 60,
) -> PersonalMixResponse:
    """Get personal mix.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        mood: Optional mood filter ('energetic', 'calm', 'focus').
        duration_minutes: Target duration in minutes.

    Returns:
        Personal mix of songs matching the criteria.
    """
    recommendation_service = RecommendationService(db)

    songs, total_duration = await recommendation_service.get_personal_mix(
        user_id=current_user.id,
        mood=mood,
        duration_minutes=duration_minutes,
    )

    return PersonalMixResponse(
        songs=[SongResponse.model_validate(song) for song in songs],
        total_duration_seconds=total_duration,
        mood=mood,
    )
