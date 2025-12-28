"""Statistics schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.song import SongResponse


class ContextType(str, Enum):
    """Context type for listening history."""

    LIBRARY = "library"
    PLAYLIST = "playlist"
    MOOD_CHAIN = "mood_chain"
    SEARCH = "search"
    RECOMMENDATION = "recommendation"


class StatsPeriod(str, Enum):
    """Period for statistics aggregation."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


# Request schemas


class PlayRecordRequest(BaseModel):
    """Schema for recording a play event."""

    song_id: UUID
    duration_listened_seconds: int = Field(ge=0)
    completed: bool = False
    context_type: ContextType | None = None
    context_id: UUID | None = None
    device_type: str | None = Field(default=None, max_length=50)


class HistoryFilters(BaseModel):
    """Schema for history filtering parameters."""

    from_date: datetime | None = None
    to_date: datetime | None = None


# Response schemas


class PlayRecordResponse(BaseModel):
    """Schema for play record response."""

    success: bool = True
    id: UUID
    played_at: datetime


class ListeningHistoryItemResponse(BaseModel):
    """Schema for a single listening history item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    song_id: UUID
    played_at: datetime
    played_duration_seconds: int | None
    completed: bool
    skipped: bool
    context_type: ContextType | None
    context_id: UUID | None
    device_type: str | None
    song: SongResponse


class ListeningHistoryResponse(BaseModel):
    """Schema for paginated listening history response."""

    items: list[ListeningHistoryItemResponse]
    total: int
    page: int
    limit: int
    pages: int


class HourlyListeningCount(BaseModel):
    """Schema for hourly listening count."""

    hour: int = Field(ge=0, le=23)
    count: int


class DailyListeningCount(BaseModel):
    """Schema for daily listening count."""

    day: str  # ISO format date string (YYYY-MM-DD)
    count: int


class StatsOverviewResponse(BaseModel):
    """Schema for statistics overview response."""

    total_plays: int
    total_duration_seconds: int
    unique_songs: int
    unique_artists: int
    most_played_genre: str | None
    listening_by_hour: list[HourlyListeningCount]
    listening_by_day: list[DailyListeningCount]


class TopSongItem(BaseModel):
    """Schema for a top song item."""

    song: SongResponse
    play_count: int


class TopSongsResponse(BaseModel):
    """Schema for top songs response."""

    items: list[TopSongItem]


class TopArtistItem(BaseModel):
    """Schema for a top artist item."""

    artist: str
    play_count: int
    songs: list[SongResponse]


class TopArtistsResponse(BaseModel):
    """Schema for top artists response."""

    items: list[TopArtistItem]
