"""Songs API endpoints."""

import re
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.song import (
    SongBatchUploadResponse,
    SongDetailResponse,
    SongFilters,
    SongListResponse,
    SongResponse,
    SongUpdate,
    SongUploadResponse,
)
from app.services.music import MusicService, SongNotFoundError, UploadError
from app.services.storage import (
    FileNotFoundError as StorageFileNotFoundError,
)
from app.services.storage import (
    StorageService,
    UnsupportedFormatError,
)

router = APIRouter()


def get_storage_service() -> StorageService:
    """Get storage service instance."""
    return StorageService()


@router.post(
    "",
    response_model=SongUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a song",
    description="Upload a new audio file. Metadata is automatically extracted.",
)
async def upload_song(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File(description="Audio file to upload")],
    title: Annotated[str | None, Form(description="Override song title")] = None,
    artist: Annotated[str | None, Form(description="Override artist name")] = None,
    album: Annotated[str | None, Form(description="Override album name")] = None,
) -> SongUploadResponse:
    """Upload a new song.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        file: Audio file to upload.
        title: Optional title override.
        artist: Optional artist override.
        album: Optional album override.

    Returns:
        Uploaded song info.

    Raises:
        HTTPException: If upload fails.
    """
    music_service = MusicService(db)

    try:
        song = await music_service.upload_song(
            owner_id=current_user.id,
            file=file.file,
            filename=file.filename or "unknown.mp3",
            content_type=file.content_type,
            override_title=title,
            override_artist=artist,
            override_album=album,
        )
        return SongUploadResponse(
            id=song.id,
            title=song.title,
            artist=song.artist,
        )
    except UnsupportedFormatError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE", "message": str(e)},
        ) from e
    except UploadError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UPLOAD_ERROR", "message": str(e)},
        ) from e


@router.post(
    "/batch",
    response_model=SongBatchUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload multiple songs",
    description="Upload multiple audio files at once.",
)
async def upload_songs_batch(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    files: Annotated[list[UploadFile], File(description="Audio files to upload")],
) -> SongBatchUploadResponse:
    """Upload multiple songs.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        files: List of audio files to upload.

    Returns:
        Batch upload results.
    """
    music_service = MusicService(db)
    songs: list[SongUploadResponse] = []
    errors: list[dict[str, str]] = []

    for file in files:
        try:
            song = await music_service.upload_song(
                owner_id=current_user.id,
                file=file.file,
                filename=file.filename or "unknown.mp3",
                content_type=file.content_type,
            )
            songs.append(
                SongUploadResponse(
                    id=song.id,
                    title=song.title,
                    artist=song.artist,
                )
            )
        except (UnsupportedFormatError, UploadError) as e:
            errors.append(
                {
                    "filename": file.filename or "unknown",
                    "error": str(e),
                }
            )

    return SongBatchUploadResponse(
        songs=songs,
        errors=errors,
        total_files=len(files),
        successful=len(songs),
        failed=len(errors),
    )


@router.get(
    "",
    response_model=SongListResponse,
    summary="List songs",
    description="Get a paginated list of songs with optional filters.",
)
async def list_songs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[
        str | None, Query(description="Search in title, artist, album")
    ] = None,
    artist: Annotated[str | None, Query(description="Filter by artist")] = None,
    album: Annotated[str | None, Query(description="Filter by album")] = None,
    genre: Annotated[str | None, Query(description="Filter by genre")] = None,
    is_favorite: Annotated[bool | None, Query(description="Filter by favorite")] = None,
    year_from: Annotated[int | None, Query(description="Year from")] = None,
    year_to: Annotated[int | None, Query(description="Year to")] = None,
    sort: Annotated[
        str,
        Query(
            description="Sort by field",
            pattern=r"^(title|artist|album|created_at|play_count|last_played_at)$",
        ),
    ] = "created_at",
    order: Annotated[
        str, Query(description="Sort order", pattern=r"^(asc|desc)$")
    ] = "desc",
) -> SongListResponse:
    """List songs with pagination and filters.

    Args:
        current_user: Current authenticated user.
        db: Database session.
        page: Page number.
        limit: Items per page.
        search: Search term.
        artist: Artist filter.
        album: Album filter.
        genre: Genre filter.
        is_favorite: Favorite filter.
        year_from: Year from filter.
        year_to: Year to filter.
        sort: Sort field.
        order: Sort order.

    Returns:
        Paginated list of songs.
    """
    music_service = MusicService(db)

    filters = SongFilters(
        search=search,
        artist=artist,
        album=album,
        genre=genre,
        is_favorite=is_favorite,
        year_from=year_from,
        year_to=year_to,
        sort=sort,
        order=order,
    )

    songs, total = await music_service.get_songs(
        owner_id=current_user.id,
        filters=filters,
        page=page,
        limit=limit,
    )

    pages = (total + limit - 1) // limit if limit > 0 else 0

    return SongListResponse(
        items=[SongResponse.model_validate(song) for song in songs],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get(
    "/{song_id}",
    response_model=SongDetailResponse,
    summary="Get song details",
    description="Get detailed information about a specific song.",
)
async def get_song(
    song_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SongDetailResponse:
    """Get song details.

    Args:
        song_id: Song UUID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Song details.

    Raises:
        HTTPException: If song not found.
    """
    music_service = MusicService(db)
    song = await music_service.get_song_by_id(song_id, current_user.id)

    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Song not found"},
        )

    return SongDetailResponse.model_validate(song)


@router.patch(
    "/{song_id}",
    response_model=SongResponse,
    summary="Update song",
    description="Update song metadata.",
)
async def update_song(
    song_id: UUID,
    update_data: SongUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SongResponse:
    """Update song metadata.

    Args:
        song_id: Song UUID.
        update_data: Update data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated song.

    Raises:
        HTTPException: If song not found.
    """
    music_service = MusicService(db)

    try:
        song = await music_service.update_song(song_id, current_user.id, update_data)
        return SongResponse.model_validate(song)
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


@router.delete(
    "/{song_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete song",
    description="Delete a song and its files.",
)
async def delete_song(
    song_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a song.

    Args:
        song_id: Song UUID.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException: If song not found.
    """
    music_service = MusicService(db)

    try:
        await music_service.delete_song(song_id, current_user.id)
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


@router.get(
    "/{song_id}/stream",
    summary="Stream song",
    description="Stream audio file with support for range requests.",
    responses={
        200: {"content": {"audio/*": {}}},
        206: {"content": {"audio/*": {}}},
    },
)
async def stream_song(
    song_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    range: Annotated[str | None, Query(alias="Range")] = None,
) -> Response:
    """Stream song audio.

    Args:
        song_id: Song UUID.
        current_user: Current authenticated user.
        db: Database session.
        range: HTTP Range header for partial content.

    Returns:
        Audio stream response.

    Raises:
        HTTPException: If song not found.
    """
    music_service = MusicService(db)
    storage = StorageService()

    song = await music_service.get_song_by_id(song_id, current_user.id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Song not found"},
        )

    try:
        file_size = await storage.get_file_size(song.file_path)
        content_type = storage.get_mime_type(song.file_format)

        # Parse range header
        if range:
            range_match = re.match(r"bytes=(\d+)-(\d*)", range)
            if range_match:
                start = int(range_match.group(1))
                end_str = range_match.group(2)
                end = int(end_str) if end_str else file_size - 1

                # Ensure valid range
                if start >= file_size:
                    raise HTTPException(
                        status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                        headers={"Content-Range": f"bytes */{file_size}"},
                    )

                end = min(end, file_size - 1)
                content_length = end - start + 1

                content = await storage.read_file_range(song.file_path, start, end + 1)

                return Response(
                    content=content,
                    status_code=status.HTTP_206_PARTIAL_CONTENT,
                    headers={
                        "Content-Type": content_type,
                        "Content-Length": str(content_length),
                        "Content-Range": f"bytes {start}-{end}/{file_size}",
                        "Accept-Ranges": "bytes",
                    },
                )

        # Full file response
        content = await storage.read_file(song.file_path)
        return Response(
            content=content,
            status_code=status.HTTP_200_OK,
            headers={
                "Content-Type": content_type,
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
            },
        )

    except StorageFileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_NOT_FOUND", "message": str(e)},
        ) from e


@router.get(
    "/{song_id}/cover",
    summary="Get song cover art",
    description="Get the cover art image for a song.",
    responses={
        200: {"content": {"image/*": {}}},
    },
)
async def get_song_cover(
    song_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Get song cover art.

    Args:
        song_id: Song UUID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Cover art image.

    Raises:
        HTTPException: If song or cover not found.
    """
    music_service = MusicService(db)
    storage = StorageService()

    song = await music_service.get_song_by_id(song_id, current_user.id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Song not found"},
        )

    if not song.cover_art_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NO_COVER", "message": "Song has no cover art"},
        )

    try:
        content = await storage.read_file(song.cover_art_path)

        # Determine content type from file extension
        if song.cover_art_path.endswith(".png"):
            content_type = "image/png"
        else:
            content_type = "image/jpeg"

        return Response(
            content=content,
            status_code=status.HTTP_200_OK,
            headers={
                "Content-Type": content_type,
                "Content-Length": str(len(content)),
                "Cache-Control": "public, max-age=86400",
            },
        )

    except StorageFileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_NOT_FOUND", "message": str(e)},
        ) from e
