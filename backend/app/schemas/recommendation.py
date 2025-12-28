"""Recommendation schemas for request/response validation."""

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.song import SongResponse


class MoodType(str, Enum):
    """Mood types for personal mix."""

    ENERGETIC = "energetic"
    CALM = "calm"
    FOCUS = "focus"


class DiscoverSectionType(str, Enum):
    """Types of discover sections."""

    LONG_TIME_NO_LISTEN = "long_time_no_listen"
    BASED_ON_FAVORITE = "based_on_favorite"
    HIDDEN_GEMS = "hidden_gems"


class SearchType(str, Enum):
    """Search result types."""

    ALL = "all"
    SONGS = "songs"
    ARTISTS = "artists"
    ALBUMS = "albums"
    PLAYLISTS = "playlists"


# Response schemas


class SimilarSongItem(BaseModel):
    """Schema for a similar song with similarity score."""

    song: SongResponse
    similarity_score: float = Field(ge=0.0, le=1.0)
    reasons: list[str]


class SimilarSongsResponse(BaseModel):
    """Schema for similar songs response."""

    source_song: SongResponse
    items: list[SimilarSongItem]


class DiscoverSection(BaseModel):
    """Schema for a discover section."""

    type: DiscoverSectionType
    title: str
    items: list[SongResponse]


class DiscoverResponse(BaseModel):
    """Schema for discover recommendations response."""

    sections: list[DiscoverSection]


class PersonalMixResponse(BaseModel):
    """Schema for personal mix response."""

    songs: list[SongResponse]
    total_duration_seconds: int
    mood: MoodType | None = None


class ArtistSearchResult(BaseModel):
    """Schema for artist search result."""

    name: str
    song_count: int
    songs: list[SongResponse]


class AlbumSearchResult(BaseModel):
    """Schema for album search result."""

    name: str
    artist: str | None
    song_count: int
    songs: list[SongResponse]


class PlaylistSearchResult(BaseModel):
    """Schema for playlist search result."""

    id: str
    name: str
    song_count: int


class SearchResponse(BaseModel):
    """Schema for global search response."""

    query: str
    songs: list[SongResponse] = Field(default_factory=list)
    artists: list[ArtistSearchResult] = Field(default_factory=list)
    albums: list[AlbumSearchResult] = Field(default_factory=list)
    playlists: list[PlaylistSearchResult] = Field(default_factory=list)
