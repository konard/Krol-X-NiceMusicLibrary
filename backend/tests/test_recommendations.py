"""Tests for recommendations service and endpoints."""

import os
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.playlist import Playlist
from app.models.song import Song
from app.models.user import User
from app.schemas.recommendation import DiscoverSectionType, MoodType
from app.services.cache import CacheService
from app.services.recommendation import (
    RecommendationService,
    SearchService,
    SongNotFoundError,
)


def get_test_database_url() -> str:
    """Get database URL for testing."""
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_user = os.getenv("POSTGRES_USER", "test")
    pg_password = os.getenv("POSTGRES_PASSWORD", "test")
    pg_db = os.getenv("POSTGRES_DB", "test")
    return f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"


TEST_DATABASE_URL = get_test_database_url()


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    """Create a test client with overridden database dependency."""

    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("SecurePass123"),
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create auth token for test user."""
    return create_access_token(str(test_user.id))


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create auth headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def test_song(db_session: AsyncSession, test_user: User) -> Song:
    """Create a test song with audio parameters."""
    song = Song(
        owner_id=test_user.id,
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        genre="Rock",
        year=2023,
        duration_seconds=180,
        file_path="/tmp/test_song.mp3",
        file_size_bytes=5000000,
        file_format="mp3",
        bitrate=320,
        sample_rate=44100,
        bpm=120,
        energy=0.7,
        valence=0.6,
        play_count=10,
    )
    db_session.add(song)
    await db_session.flush()
    return song


@pytest.fixture
async def test_songs_with_variety(
    db_session: AsyncSession, test_user: User
) -> list[Song]:
    """Create multiple test songs with varying parameters for similarity testing."""
    songs_data = [
        {
            "title": "Rock Song 1",
            "artist": "Rock Artist",
            "genre": "Rock",
            "bpm": 120,
            "energy": 0.8,
            "valence": 0.7,
            "play_count": 20,
        },
        {
            "title": "Rock Song 2",
            "artist": "Rock Artist",
            "genre": "Rock",
            "bpm": 125,
            "energy": 0.75,
            "valence": 0.65,
            "play_count": 15,
        },
        {
            "title": "Pop Song 1",
            "artist": "Pop Artist",
            "genre": "Pop",
            "bpm": 100,
            "energy": 0.6,
            "valence": 0.8,
            "play_count": 5,
        },
        {
            "title": "Jazz Song 1",
            "artist": "Jazz Artist",
            "genre": "Jazz",
            "bpm": 90,
            "energy": 0.4,
            "valence": 0.5,
            "play_count": 8,
        },
        {
            "title": "Electronic Song 1",
            "artist": "Electronic Artist",
            "genre": "Electronic",
            "bpm": 128,
            "energy": 0.9,
            "valence": 0.6,
            "play_count": 2,
        },
        {
            "title": "Calm Song",
            "artist": "Calm Artist",
            "genre": "Ambient",
            "bpm": 60,
            "energy": 0.2,
            "valence": 0.4,
            "play_count": 1,
        },
    ]

    songs = []
    for i, data in enumerate(songs_data):
        song = Song(
            owner_id=test_user.id,
            title=data["title"],
            artist=data["artist"],
            album=f"Album {i}",
            genre=data["genre"],
            year=2023,
            duration_seconds=180 + i * 30,
            file_path=f"/tmp/song_{i}.mp3",
            file_size_bytes=5000000,
            file_format="mp3",
            bpm=data["bpm"],
            energy=data["energy"],
            valence=data["valence"],
            play_count=data["play_count"],
        )
        songs.append(song)
        db_session.add(song)

    await db_session.flush()
    return songs


@pytest.fixture
async def test_playlist(db_session: AsyncSession, test_user: User) -> Playlist:
    """Create a test playlist."""
    playlist = Playlist(
        owner_id=test_user.id,
        name="Test Playlist",
        description="A test playlist",
    )
    db_session.add(playlist)
    await db_session.flush()
    return playlist


@pytest.fixture
def mock_cache():
    """Create a mock cache service."""
    cache = MagicMock(spec=CacheService)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.delete_pattern = AsyncMock(return_value=True)
    return cache


class TestRecommendationService:
    """Tests for RecommendationService."""

    async def test_calculate_similarity_same_genre(
        self,
        db_session: AsyncSession,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test similarity calculation for songs with same genre."""
        service = RecommendationService(db_session, cache=mock_cache)

        # Rock Song 1 and Rock Song 2 should have high similarity
        song1 = test_songs_with_variety[0]  # Rock Song 1
        song2 = test_songs_with_variety[1]  # Rock Song 2

        score, reasons = service._calculate_similarity(song1, song2)

        assert score > 0.6  # Should have high similarity
        assert "same genre" in reasons
        assert "similar BPM" in reasons or "close BPM" in reasons

    async def test_calculate_similarity_different_genre(
        self,
        db_session: AsyncSession,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test similarity calculation for songs with different genres."""
        service = RecommendationService(db_session, cache=mock_cache)

        # Rock Song 1 and Jazz Song should have lower similarity
        rock_song = test_songs_with_variety[0]  # Rock
        jazz_song = test_songs_with_variety[3]  # Jazz

        score, reasons = service._calculate_similarity(rock_song, jazz_song)

        assert score < 0.5  # Should have lower similarity
        assert "same genre" not in reasons

    async def test_get_similar_songs(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test getting similar songs."""
        service = RecommendationService(db_session, cache=mock_cache)

        source_song = test_songs_with_variety[0]  # Rock Song 1

        source, similar = await service.get_similar_songs(
            song_id=source_song.id,
            user_id=test_user.id,
            limit=3,
        )

        assert source.id == source_song.id
        assert len(similar) <= 3
        # First similar song should be Rock Song 2 (same genre and artist)
        if similar:
            top_similar_song = similar[0][0]
            assert top_similar_song.genre == "Rock"

    async def test_get_similar_songs_not_found(
        self, db_session: AsyncSession, test_user: User, mock_cache
    ):
        """Test getting similar songs for non-existent song."""
        service = RecommendationService(db_session, cache=mock_cache)

        with pytest.raises(SongNotFoundError):
            await service.get_similar_songs(
                song_id=uuid4(),
                user_id=test_user.id,
                limit=10,
            )

    async def test_get_discover_recommendations(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test getting discover recommendations."""
        service = RecommendationService(db_session, cache=mock_cache)

        sections = await service.get_discover_recommendations(
            user_id=test_user.id,
            limit=5,
        )

        assert DiscoverSectionType.LONG_TIME_NO_LISTEN in sections
        assert DiscoverSectionType.BASED_ON_FAVORITE in sections
        assert DiscoverSectionType.HIDDEN_GEMS in sections

    async def test_get_personal_mix(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test getting personal mix."""
        service = RecommendationService(db_session, cache=mock_cache)

        songs, total_duration = await service.get_personal_mix(
            user_id=test_user.id,
            mood=None,
            duration_minutes=30,
        )

        assert len(songs) > 0
        assert total_duration > 0

    async def test_get_personal_mix_energetic(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test getting personal mix with energetic mood."""
        service = RecommendationService(db_session, cache=mock_cache)

        songs, total_duration = await service.get_personal_mix(
            user_id=test_user.id,
            mood=MoodType.ENERGETIC,
            duration_minutes=30,
        )

        # All songs should have high energy or no energy value
        for song in songs:
            if song.energy is not None:
                assert song.energy >= 0.6 or song.energy is None

    async def test_get_personal_mix_calm(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test getting personal mix with calm mood."""
        service = RecommendationService(db_session, cache=mock_cache)

        songs, total_duration = await service.get_personal_mix(
            user_id=test_user.id,
            mood=MoodType.CALM,
            duration_minutes=30,
        )

        # All songs should have low energy or no energy value
        for song in songs:
            if song.energy is not None:
                assert song.energy <= 0.4 or song.energy is None


class TestSearchService:
    """Tests for SearchService."""

    async def test_search_songs(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test searching for songs."""
        service = SearchService(db_session, cache=mock_cache)

        results = await service.search(
            user_id=test_user.id,
            query="Rock",
            search_type="songs",
            limit=10,
        )

        assert len(results["songs"]) > 0
        for song in results["songs"]:
            assert "Rock" in song.title or "Rock" in (song.artist or "")

    async def test_search_artists(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test searching for artists."""
        service = SearchService(db_session, cache=mock_cache)

        results = await service.search(
            user_id=test_user.id,
            query="Rock Artist",
            search_type="artists",
            limit=10,
        )

        assert len(results["artists"]) > 0
        assert results["artists"][0]["name"] == "Rock Artist"

    async def test_search_albums(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        mock_cache,
    ):
        """Test searching for albums."""
        service = SearchService(db_session, cache=mock_cache)

        results = await service.search(
            user_id=test_user.id,
            query="Album",
            search_type="albums",
            limit=10,
        )

        assert len(results["albums"]) > 0

    async def test_search_playlists(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_playlist: Playlist,
        mock_cache,
    ):
        """Test searching for playlists."""
        service = SearchService(db_session, cache=mock_cache)

        results = await service.search(
            user_id=test_user.id,
            query="Test Playlist",
            search_type="playlists",
            limit=10,
        )

        assert len(results["playlists"]) > 0
        assert results["playlists"][0]["name"] == "Test Playlist"

    async def test_search_all(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_songs_with_variety: list[Song],
        test_playlist: Playlist,
        mock_cache,
    ):
        """Test global search across all categories."""
        service = SearchService(db_session, cache=mock_cache)

        results = await service.search(
            user_id=test_user.id,
            query="Test",
            search_type="all",
            limit=10,
        )

        # Should return results from multiple categories
        assert "songs" in results
        assert "artists" in results
        assert "albums" in results
        assert "playlists" in results

    async def test_search_empty_query(
        self, db_session: AsyncSession, test_user: User, mock_cache
    ):
        """Test search with empty query."""
        service = SearchService(db_session, cache=mock_cache)

        results = await service.search(
            user_id=test_user.id,
            query="",
            search_type="all",
            limit=10,
        )

        assert results["songs"] == []
        assert results["artists"] == []
        assert results["albums"] == []
        assert results["playlists"] == []


class TestRecommendationsEndpoints:
    """Tests for recommendations API endpoints."""

    async def test_get_similar_songs_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /recommendations/similar/{song_id} endpoint."""
        song_id = test_songs_with_variety[0].id

        response = await client.get(
            f"/api/v1/recommendations/similar/{song_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "source_song" in data
        assert "items" in data
        assert data["source_song"]["id"] == str(song_id)

    async def test_get_similar_songs_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test GET /recommendations/similar/{song_id} with non-existent song."""
        response = await client.get(
            f"/api/v1/recommendations/similar/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_similar_songs_with_limit(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /recommendations/similar/{song_id} with limit parameter."""
        song_id = test_songs_with_variety[0].id

        response = await client.get(
            f"/api/v1/recommendations/similar/{song_id}?limit=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2

    async def test_get_discover_recommendations_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /recommendations/discover endpoint."""
        response = await client.get(
            "/api/v1/recommendations/discover",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "sections" in data
        assert isinstance(data["sections"], list)

    async def test_get_personal_mix_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /recommendations/mix endpoint."""
        response = await client.get(
            "/api/v1/recommendations/mix",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "songs" in data
        assert "total_duration_seconds" in data

    async def test_get_personal_mix_with_mood(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /recommendations/mix with mood parameter."""
        response = await client.get(
            "/api/v1/recommendations/mix?mood=energetic",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mood"] == "energetic"

    async def test_get_personal_mix_with_duration(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /recommendations/mix with duration parameter."""
        response = await client.get(
            "/api/v1/recommendations/mix?duration_minutes=30",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Total duration should be approximately 30 minutes
        assert data["total_duration_seconds"] <= 30 * 60 + 300  # Allow some margin


class TestSearchEndpoints:
    """Tests for search API endpoints."""

    async def test_search_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /search endpoint."""
        response = await client.get(
            "/api/v1/search?q=Rock",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Rock"
        assert "songs" in data
        assert "artists" in data
        assert "albums" in data
        assert "playlists" in data

    async def test_search_songs_only(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /search with type=songs."""
        response = await client.get(
            "/api/v1/search?q=Rock&type=songs",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["songs"]) > 0

    async def test_search_with_limit(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_songs_with_variety: list[Song],
    ):
        """Test GET /search with limit parameter."""
        response = await client.get(
            "/api/v1/search?q=Song&limit=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["songs"]) <= 2

    async def test_search_unauthorized(self, client: AsyncClient):
        """Test that search endpoint requires authentication."""
        response = await client.get("/api/v1/search?q=test")

        assert response.status_code in (401, 403)

    async def test_recommendations_unauthorized(self, client: AsyncClient):
        """Test that recommendations endpoints require authentication."""
        endpoints = [
            f"/api/v1/recommendations/similar/{uuid4()}",
            "/api/v1/recommendations/discover",
            "/api/v1/recommendations/mix",
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code in (401, 403)
