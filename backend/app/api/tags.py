"""Tags API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.tag import (
    SongTagRequest,
    SongWithTagsResponse,
    TagCreate,
    TagListResponse,
    TagResponse,
    TagUpdate,
)
from app.services.tag import (
    SongNotFoundError,
    TagAlreadyExistsError,
    TagAlreadyOnSongError,
    TagNotFoundError,
    TagNotOnSongError,
    TagService,
)

router = APIRouter()


def _convert_song_with_tags(song) -> SongWithTagsResponse:
    """Convert song with tags to response format."""
    tags = [
        TagResponse(
            id=st.tag.id,
            name=st.tag.name,
            color=st.tag.color,
            created_at=st.tag.created_at,
        )
        for st in song.song_tags
    ]
    return SongWithTagsResponse(
        id=song.id,
        title=song.title,
        artist=song.artist,
        album=song.album,
        tags=tags,
    )


@router.get(
    "",
    response_model=TagListResponse,
    summary="List tags",
    description="Get all tags for the current user.",
)
async def list_tags(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TagListResponse:
    """List all tags.

    Args:
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        List of tags.
    """
    tag_service = TagService(db)
    tags = await tag_service.get_tags(owner_id=current_user.id)

    return TagListResponse(items=[TagResponse.model_validate(t) for t in tags])


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
    description="Create a new tag.",
)
async def create_tag(
    data: TagCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TagResponse:
    """Create a new tag.

    Args:
        data: Tag creation data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Created tag.

    Raises:
        HTTPException: If tag with name already exists.
    """
    tag_service = TagService(db)

    try:
        tag = await tag_service.create_tag(owner_id=current_user.id, data=data)
        return TagResponse.model_validate(tag)
    except TagAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "TAG_ALREADY_EXISTS", "message": str(e)},
        ) from e


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Update tag",
    description="Update a tag.",
)
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TagResponse:
    """Update a tag.

    Args:
        tag_id: Tag UUID.
        data: Update data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated tag.

    Raises:
        HTTPException: If tag not found or name conflict.
    """
    tag_service = TagService(db)

    try:
        tag = await tag_service.update_tag(tag_id, current_user.id, data)
        return TagResponse.model_validate(tag)
    except TagNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e
    except TagAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "TAG_ALREADY_EXISTS", "message": str(e)},
        ) from e


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
    description="Delete a tag.",
)
async def delete_tag(
    tag_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a tag.

    Args:
        tag_id: Tag UUID.
        current_user: Current authenticated user.
        db: Database session.

    Raises:
        HTTPException: If tag not found.
    """
    tag_service = TagService(db)

    try:
        await tag_service.delete_tag(tag_id, current_user.id)
    except TagNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": str(e)},
        ) from e


# Song-tag endpoints are in a separate router included in songs.py
song_tags_router = APIRouter()


@song_tags_router.post(
    "/{song_id}/tags",
    response_model=SongWithTagsResponse,
    summary="Add tag to song",
    description="Add a tag to a song.",
)
async def add_tag_to_song(
    song_id: UUID,
    data: SongTagRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SongWithTagsResponse:
    """Add a tag to a song.

    Args:
        song_id: Song UUID.
        data: Tag request data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated song with tags.

    Raises:
        HTTPException: If song or tag not found, or tag already on song.
    """
    tag_service = TagService(db)

    try:
        song = await tag_service.add_tag_to_song(
            song_id=song_id,
            tag_id=data.tag_id,
            owner_id=current_user.id,
        )
        return _convert_song_with_tags(song)
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SONG_NOT_FOUND", "message": str(e)},
        ) from e
    except TagNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TAG_NOT_FOUND", "message": str(e)},
        ) from e
    except TagAlreadyOnSongError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "TAG_ALREADY_ON_SONG", "message": str(e)},
        ) from e


@song_tags_router.delete(
    "/{song_id}/tags/{tag_id}",
    response_model=SongWithTagsResponse,
    summary="Remove tag from song",
    description="Remove a tag from a song.",
)
async def remove_tag_from_song(
    song_id: UUID,
    tag_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SongWithTagsResponse:
    """Remove a tag from a song.

    Args:
        song_id: Song UUID.
        tag_id: Tag UUID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        Updated song with tags.

    Raises:
        HTTPException: If song not found or tag not on song.
    """
    tag_service = TagService(db)

    try:
        song = await tag_service.remove_tag_from_song(
            song_id=song_id,
            tag_id=tag_id,
            owner_id=current_user.id,
        )
        return _convert_song_with_tags(song)
    except SongNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SONG_NOT_FOUND", "message": str(e)},
        ) from e
    except TagNotOnSongError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TAG_NOT_ON_SONG", "message": str(e)},
        ) from e
