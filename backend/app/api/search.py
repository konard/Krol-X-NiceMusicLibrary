"""Search API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.recommendation import (
    AlbumSearchResult,
    ArtistSearchResult,
    PlaylistSearchResult,
    SearchResponse,
    SearchType,
)
from app.schemas.song import SongResponse
from app.services.recommendation import SearchService

router = APIRouter()


@router.get(
    "",
    response_model=SearchResponse,
    summary="Global search",
    description=(
        "Search across songs, artists, albums, and playlists. "
        "Results are filtered by the current user's library."
    ),
)
async def search(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[str, Query(min_length=1, description="Search query")],
    type: Annotated[
        SearchType,
        Query(description="Type of results to return"),
    ] = SearchType.ALL,
    limit: Annotated[
        int,
        Query(ge=1, le=50, description="Maximum results per category"),
    ] = 10,
) -> SearchResponse:
    """Perform global search.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        q: Search query string.
        type: Type of search results to return.
        limit: Maximum results per category.

    Returns:
        Search results organized by category.
    """
    search_service = SearchService(db)

    results = await search_service.search(
        user_id=current_user.id,
        query=q,
        search_type=type.value,
        limit=limit,
    )

    # Convert songs to response models
    songs = [SongResponse.model_validate(song) for song in results.get("songs", [])]

    # Convert artists
    artists = [
        ArtistSearchResult(
            name=a["name"],
            song_count=a["song_count"],
            songs=[SongResponse.model_validate(s) for s in a["songs"]],
        )
        for a in results.get("artists", [])
    ]

    # Convert albums
    albums = [
        AlbumSearchResult(
            name=a["name"],
            artist=a["artist"],
            song_count=a["song_count"],
            songs=[SongResponse.model_validate(s) for s in a["songs"]],
        )
        for a in results.get("albums", [])
    ]

    # Convert playlists
    playlists = [
        PlaylistSearchResult(
            id=p["id"],
            name=p["name"],
            song_count=p["song_count"],
        )
        for p in results.get("playlists", [])
    ]

    return SearchResponse(
        query=q,
        songs=songs,
        artists=artists,
        albums=albums,
        playlists=playlists,
    )
