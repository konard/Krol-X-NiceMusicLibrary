"""Playlists API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.playlist import Playlist
from app.schemas.playlist import (
    AddSongToPlaylistRequest,
    PlaylistCreate,
    PlaylistDetailResponse,
    PlaylistListResponse,
    PlaylistResponse,
    PlaylistSongWithDetailsResponse,
    PlaylistUpdate,
    ReorderPlaylistSongsRequest,
)
from app.services.playlist import (
    PlaylistNotFoundError,
    PlaylistService,
    SongAlreadyInPlaylistError,
    SongNotFoundError,
    SongNotInPlaylistError,
)

router = APIRouter()


def _convert_playlist_songs_to_response(
    playlist: Playlist,
) -> list[PlaylistSongWithDetailsResponse]:
    """Convert playlist songs to response format with song details."""
    songs = []
    for ps in sorted(playlist.playlist_songs, key=lambda x: x.position):
        songs.append(
            PlaylistSongWithDetailsResponse(
                song_id=ps.song_id,
                position=ps.position,
                added_at=ps.added_at,
                title=ps.song.title,
                artist=ps.song.artist,
                album=ps.song.album,
                duration_seconds=ps.song.duration_seconds,
                cover_art_path=ps.song.cover_art_path,
            )
        )
    return songs


@router.get(
    "",
    response_model=PlaylistListResponse,
    summary="List playlists",
    description="Get a paginated list of user's playlists.",
)
async def list_playlists(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PlaylistListResponse:
    """List playlists with pagination.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        page: Page number.
        limit: Items per page.

    Returns:
        Paginated list of playlists.
    """
    playlist_service = PlaylistService(db)
    playlists, total = await playlist_service.get_playlists(
        owner_id=current_user.id,
        page=page,
        limit=limit,
    )

    pages = (total + limit - 1) // limit if limit > 0 else 0

    return PlaylistListResponse(
        items=[PlaylistResponse.model_validate(p) for p in playlists],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.post(
    "",
    response_model=PlaylistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create playlist",
    description="Create a new playlist.",
)
async def create_playlist(
    data: PlaylistCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaylistResponse:
    """Create a new playlist.

    Args:
        data: Playlist creation data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Created playlist.
    """
    playlist_service = PlaylistService(db)
    playlist = await playlist_service.create_playlist(
        owner_id=current_user.id,
        data=data,
    )
    return PlaylistResponse.model_validate(playlist)


@router.get(
    "/{playlist_id}",
    response_model=PlaylistDetailResponse,
    summary="Get playlist",
    description="Get playlist details with songs.",
)
async def get_playlist(
    playlist_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaylistDetailResponse:
    """Get playlist details with songs.

    Args:
        playlist_id: Playlist UUID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Playlist with songs.

    Raises:
        HTTPException: If playlist not found.
    """
    playlist_service = PlaylistService(db)
    playlist = await playlist_service.get_playlist_with_songs(
        playlist_id, current_user.id
    )

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Playlist not found"},
        )

    songs = _convert_playlist_songs_to_response(playlist)
    return PlaylistDetailResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        cover_image_path=playlist.cover_image_path,
        is_public=playlist.is_public,
        song_count=playlist.song_count,
        total_duration_seconds=playlist.total_duration_seconds,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
        songs=songs,
    )


@router.patch(
    "/{playlist_id}",
    response_model=PlaylistResponse,
    summary="Update playlist",
    description="Update playlist metadata.",
)
async def update_playlist(
    playlist_id: UUID,
    data: PlaylistUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaylistResponse:
    """Update playlist metadata.

    Args:
        playlist_id: Playlist UUID.
        data: Update data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated playlist.

    Raises:
        HTTPException: If playlist not found.
    """
    playlist_service = PlaylistService(db)

    try:
        playlist = await playlist_service.update_playlist(
            playlist_id, current_user.id, data
        )
        return PlaylistResponse.model_validate(playlist)
    except PlaylistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


@router.delete(
    "/{playlist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete playlist",
    description="Delete a playlist.",
)
async def delete_playlist(
    playlist_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a playlist.

    Args:
        playlist_id: Playlist UUID.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException: If playlist not found.
    """
    playlist_service = PlaylistService(db)

    try:
        await playlist_service.delete_playlist(playlist_id, current_user.id)
    except PlaylistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


@router.post(
    "/{playlist_id}/songs",
    response_model=PlaylistDetailResponse,
    summary="Add song to playlist",
    description="Add a song to a playlist.",
)
async def add_song_to_playlist(
    playlist_id: UUID,
    data: AddSongToPlaylistRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaylistDetailResponse:
    """Add a song to a playlist.

    Args:
        playlist_id: Playlist UUID.
        data: Add song request data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated playlist with songs.

    Raises:
        HTTPException: If playlist or song not found, or song already in playlist.
    """
    playlist_service = PlaylistService(db)

    try:
        playlist = await playlist_service.add_song_to_playlist(
            playlist_id=playlist_id,
            song_id=data.song_id,
            owner_id=current_user.id,
            position=data.position,
        )
        songs = _convert_playlist_songs_to_response(playlist)
        return PlaylistDetailResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            cover_image_path=playlist.cover_image_path,
            is_public=playlist.is_public,
            song_count=playlist.song_count,
            total_duration_seconds=playlist.total_duration_seconds,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
            songs=songs,
        )
    except PlaylistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PLAYLIST_NOT_FOUND", "message": str(e)},
        ) from e
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SONG_NOT_FOUND", "message": str(e)},
        ) from e
    except SongAlreadyInPlaylistError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SONG_ALREADY_IN_PLAYLIST", "message": str(e)},
        ) from e


@router.delete(
    "/{playlist_id}/songs/{song_id}",
    response_model=PlaylistDetailResponse,
    summary="Remove song from playlist",
    description="Remove a song from a playlist.",
)
async def remove_song_from_playlist(
    playlist_id: UUID,
    song_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaylistDetailResponse:
    """Remove a song from a playlist.

    Args:
        playlist_id: Playlist UUID.
        song_id: Song UUID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated playlist with songs.

    Raises:
        HTTPException: If playlist not found or song not in playlist.
    """
    playlist_service = PlaylistService(db)

    try:
        playlist = await playlist_service.remove_song_from_playlist(
            playlist_id=playlist_id,
            song_id=song_id,
            owner_id=current_user.id,
        )
        songs = _convert_playlist_songs_to_response(playlist)
        return PlaylistDetailResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            cover_image_path=playlist.cover_image_path,
            is_public=playlist.is_public,
            song_count=playlist.song_count,
            total_duration_seconds=playlist.total_duration_seconds,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
            songs=songs,
        )
    except PlaylistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PLAYLIST_NOT_FOUND", "message": str(e)},
        ) from e
    except SongNotInPlaylistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SONG_NOT_IN_PLAYLIST", "message": str(e)},
        ) from e


@router.put(
    "/{playlist_id}/songs/order",
    response_model=PlaylistDetailResponse,
    summary="Reorder playlist songs",
    description="Reorder songs in a playlist.",
)
async def reorder_playlist_songs(
    playlist_id: UUID,
    data: ReorderPlaylistSongsRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlaylistDetailResponse:
    """Reorder songs in a playlist.

    Args:
        playlist_id: Playlist UUID.
        data: Reorder request with song IDs in new order.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated playlist with songs.

    Raises:
        HTTPException: If playlist not found or song IDs don't match.
    """
    playlist_service = PlaylistService(db)

    try:
        playlist = await playlist_service.reorder_playlist_songs(
            playlist_id=playlist_id,
            song_ids=data.song_ids,
            owner_id=current_user.id,
        )
        songs = _convert_playlist_songs_to_response(playlist)
        return PlaylistDetailResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            cover_image_path=playlist.cover_image_path,
            is_public=playlist.is_public,
            song_count=playlist.song_count,
            total_duration_seconds=playlist.total_duration_seconds,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
            songs=songs,
        )
    except PlaylistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PLAYLIST_NOT_FOUND", "message": str(e)},
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_SONG_IDS", "message": str(e)},
        ) from e
