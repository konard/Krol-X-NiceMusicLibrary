"""Playlist schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlaylistSongBase(BaseModel):
    """Base schema for playlist song association."""

    song_id: UUID
    position: int | None = None


class PlaylistSongResponse(BaseModel):
    """Schema for playlist song response."""

    model_config = ConfigDict(from_attributes=True)

    song_id: UUID
    position: int
    added_at: datetime


class PlaylistSongWithDetailsResponse(PlaylistSongResponse):
    """Schema for playlist song with song details."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    artist: str | None
    album: str | None
    duration_seconds: int
    cover_art_path: str | None


class PlaylistBase(BaseModel):
    """Base playlist schema with common fields."""

    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=5000)


class PlaylistCreate(PlaylistBase):
    """Schema for creating a playlist."""

    pass


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    is_public: bool | None = None
    cover_image_path: str | None = Field(default=None, max_length=500)


class PlaylistResponse(BaseModel):
    """Schema for playlist response (list view)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    cover_image_path: str | None
    is_public: bool
    song_count: int
    total_duration_seconds: int
    created_at: datetime
    updated_at: datetime


class PlaylistDetailResponse(PlaylistResponse):
    """Schema for detailed playlist response with songs."""

    model_config = ConfigDict(from_attributes=True)

    songs: list[PlaylistSongWithDetailsResponse] = []


class PlaylistListResponse(BaseModel):
    """Schema for paginated playlist list response."""

    items: list[PlaylistResponse]
    total: int
    page: int
    limit: int
    pages: int


class AddSongToPlaylistRequest(BaseModel):
    """Schema for adding a song to a playlist."""

    song_id: UUID
    position: int | None = Field(
        default=None, ge=0, description="Position in playlist (0-indexed)"
    )


class ReorderPlaylistSongsRequest(BaseModel):
    """Schema for reordering songs in a playlist."""

    song_ids: list[UUID] = Field(description="List of song IDs in the new order")
