"""Mood chain schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.mood_chain import TransitionStyle


class MoodChainSongBase(BaseModel):
    """Base schema for mood chain song association."""

    song_id: UUID
    position: int | None = None


class MoodChainSongResponse(BaseModel):
    """Schema for mood chain song response."""

    model_config = ConfigDict(from_attributes=True)

    song_id: UUID
    position: int
    transition_weight: float
    added_at: datetime


class MoodChainSongWithDetailsResponse(MoodChainSongResponse):
    """Schema for mood chain song with song details."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    artist: str | None
    album: str | None
    duration_seconds: int
    cover_art_path: str | None
    energy: float | None = None
    valence: float | None = None
    bpm: int | None = None
    genre: str | None = None


class MoodChainTransitionBase(BaseModel):
    """Base schema for mood chain transition."""

    from_song_id: UUID
    to_song_id: UUID
    weight: float = Field(ge=0.0, le=1.0, default=0.5)


class MoodChainTransitionResponse(MoodChainTransitionBase):
    """Schema for mood chain transition response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    play_count: int


class MoodChainBase(BaseModel):
    """Base mood chain schema with common fields."""

    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    transition_style: TransitionStyle = TransitionStyle.SMOOTH
    auto_advance: bool = True
    auto_advance_delay_seconds: int = Field(default=10, ge=1, le=60)


class MoodChainCreate(MoodChainBase):
    """Schema for creating a mood chain."""

    song_ids: list[UUID] | None = Field(default=None)


class MoodChainUpdate(BaseModel):
    """Schema for updating a mood chain."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    transition_style: TransitionStyle | None = None
    auto_advance: bool | None = None
    auto_advance_delay_seconds: int | None = Field(default=None, ge=1, le=60)
    cover_image_path: str | None = Field(default=None, max_length=500)


class MoodChainResponse(BaseModel):
    """Schema for mood chain response (list view)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    cover_image_path: str | None
    transition_style: TransitionStyle
    auto_advance: bool
    auto_advance_delay_seconds: int
    is_auto_generated: bool
    song_count: int
    play_count: int
    last_played_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MoodChainDetailResponse(MoodChainResponse):
    """Schema for detailed mood chain response with songs and transitions."""

    model_config = ConfigDict(from_attributes=True)

    songs: list[MoodChainSongWithDetailsResponse] = []
    transitions: list[MoodChainTransitionResponse] = []


class MoodChainListResponse(BaseModel):
    """Schema for paginated mood chain list response."""

    items: list[MoodChainResponse]
    total: int
    page: int
    limit: int
    pages: int


class AddSongToMoodChainRequest(BaseModel):
    """Schema for adding a song to a mood chain."""

    song_id: UUID
    position: int | None = Field(
        default=None, ge=0, description="Position in mood chain (0-indexed)"
    )


class ReorderMoodChainSongsRequest(BaseModel):
    """Schema for reordering songs in a mood chain."""

    song_ids: list[UUID] = Field(description="List of song IDs in the new order")


class UpdateTransitionsRequest(BaseModel):
    """Schema for updating transitions in a mood chain."""

    transitions: list[MoodChainTransitionBase] = Field(
        description="List of transitions to update"
    )


class MoodChainFromHistoryRequest(BaseModel):
    """Schema for creating a mood chain from listening history."""

    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    from_date: datetime | None = None
    to_date: datetime | None = None
    min_plays: int = Field(default=1, ge=1, description="Minimum plays to include song")


class NextSongSuggestion(BaseModel):
    """Schema for next song suggestion."""

    model_config = ConfigDict(from_attributes=True)

    song_id: UUID
    title: str
    artist: str | None
    album: str | None
    duration_seconds: int
    cover_art_path: str | None
    weight: float
    reason: str


class NextSongResponse(BaseModel):
    """Schema for next song suggestions response."""

    suggestions: list[NextSongSuggestion]


class TransitionPlayedRequest(BaseModel):
    """Schema for recording a transition play."""

    from_song_id: UUID
    to_song_id: UUID


class TransitionPlayedResponse(BaseModel):
    """Schema for transition played response."""

    success: bool
