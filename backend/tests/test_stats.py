"""Tests for stats service and endpoints."""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.listening_history import ContextType, ListeningHistory
from app.models.song import Song
from app.models.user import User
from app.schemas.stats import ContextType as SchemaContextType
from app.schemas.stats import StatsPeriod
from app.services.cache import CacheService
from app.services.stats import SongNotFoundError, StatsService


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
    """Create a test song."""
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
    )
    db_session.add(song)
    await db_session.flush()
    return song


@pytest.fixture
async def test_songs(db_session: AsyncSession, test_user: User) -> list[Song]:
    """Create multiple test songs."""
    songs = []
    for i in range(5):
        song = Song(
            owner_id=test_user.id,
            title=f"Song {i}",
            artist=f"Artist {i % 2}",  # Only 2 unique artists
            album=f"Album {i}",
            genre="Rock" if i % 2 == 0 else "Pop",
            year=2023,
            duration_seconds=180 + i * 10,
            file_path=f"/tmp/song_{i}.mp3",
            file_size_bytes=5000000,
            file_format="mp3",
        )
        songs.append(song)
        db_session.add(song)
    await db_session.flush()
    return songs


@pytest.fixture
def mock_cache():
    """Create a mock cache service."""
    cache = MagicMock(spec=CacheService)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.delete_pattern = AsyncMock(return_value=True)
    return cache


class TestStatsService:
    """Tests for StatsService."""

    async def test_record_play(
        self, db_session: AsyncSession, test_song: Song, test_user: User, mock_cache
    ):
        """Test recording a play event."""
        stats_service = StatsService(db_session, cache=mock_cache)

        history = await stats_service.record_play(
            user_id=test_user.id,
            song_id=test_song.id,
            duration_listened_seconds=120,
            completed=True,
            context_type=SchemaContextType.LIBRARY,
        )

        assert history is not None
        assert history.user_id == test_user.id
        assert history.song_id == test_song.id
        assert history.played_duration_seconds == 120
        assert history.completed is True
        assert history.context_type == ContextType.LIBRARY

        # Song play_count should be incremented
        assert test_song.play_count == 1
        assert test_song.last_played_at is not None

        # Cache should be invalidated
        mock_cache.delete_pattern.assert_called_once()

    async def test_record_play_song_not_found(
        self, db_session: AsyncSession, test_user: User, mock_cache
    ):
        """Test recording play for non-existent song raises error."""
        stats_service = StatsService(db_session, cache=mock_cache)

        with pytest.raises(SongNotFoundError):
            await stats_service.record_play(
                user_id=test_user.id,
                song_id=uuid4(),
                duration_listened_seconds=120,
            )

    async def test_record_play_wrong_owner(
        self, db_session: AsyncSession, test_song: Song, mock_cache
    ):
        """Test recording play for song with wrong owner raises error."""
        stats_service = StatsService(db_session, cache=mock_cache)

        with pytest.raises(SongNotFoundError):
            await stats_service.record_play(
                user_id=uuid4(),  # Different user
                song_id=test_song.id,
                duration_listened_seconds=120,
            )

    async def test_get_history_empty(
        self, db_session: AsyncSession, test_user: User, mock_cache
    ):
        """Test getting history when empty."""
        stats_service = StatsService(db_session, cache=mock_cache)

        history, total = await stats_service.get_history(user_id=test_user.id)

        assert history == []
        assert total == 0

    async def test_get_history_with_records(
        self, db_session: AsyncSession, test_song: Song, test_user: User, mock_cache
    ):
        """Test getting history with records."""
        stats_service = StatsService(db_session, cache=mock_cache)

        # Record some plays
        await stats_service.record_play(
            user_id=test_user.id,
            song_id=test_song.id,
            duration_listened_seconds=120,
        )
        await stats_service.record_play(
            user_id=test_user.id,
            song_id=test_song.id,
            duration_listened_seconds=180,
            completed=True,
        )

        history, total = await stats_service.get_history(user_id=test_user.id)

        assert len(history) == 2
        assert total == 2
        # Check both records are present
        durations = {h.played_duration_seconds for h in history}
        assert durations == {120, 180}

    async def test_get_history_pagination(
        self, db_session: AsyncSession, test_song: Song, test_user: User, mock_cache
    ):
        """Test history pagination."""
        stats_service = StatsService(db_session, cache=mock_cache)

        # Record 5 plays
        for _ in range(5):
            await stats_service.record_play(
                user_id=test_user.id,
                song_id=test_song.id,
                duration_listened_seconds=120,
            )

        # Get first page
        history, total = await stats_service.get_history(
            user_id=test_user.id, page=1, limit=2
        )

        assert len(history) == 2
        assert total == 5

        # Get second page
        history, total = await stats_service.get_history(
            user_id=test_user.id, page=2, limit=2
        )

        assert len(history) == 2
        assert total == 5

    async def test_get_history_date_filter(
        self, db_session: AsyncSession, test_song: Song, test_user: User, mock_cache
    ):
        """Test history date filtering."""
        stats_service = StatsService(db_session, cache=mock_cache)

        # Record a play
        await stats_service.record_play(
            user_id=test_user.id,
            song_id=test_song.id,
            duration_listened_seconds=120,
        )

        # Filter with future date
        future = datetime.now(UTC) + timedelta(days=1)
        history, total = await stats_service.get_history(
            user_id=test_user.id, from_date=future
        )

        assert len(history) == 0
        assert total == 0

    async def test_get_overview_empty(
        self, db_session: AsyncSession, test_user: User, mock_cache
    ):
        """Test getting overview with no data."""
        stats_service = StatsService(db_session, cache=mock_cache)

        overview = await stats_service.get_overview(user_id=test_user.id)

        assert overview["total_plays"] == 0
        assert overview["total_duration_seconds"] == 0
        assert overview["unique_songs"] == 0
        assert overview["unique_artists"] == 0
        assert overview["most_played_genre"] is None

    async def test_get_overview_with_data(
        self,
        db_session: AsyncSession,
        test_songs: list[Song],
        test_user: User,
        mock_cache,
    ):
        """Test getting overview with data."""
        stats_service = StatsService(db_session, cache=mock_cache)

        # Record plays for different songs
        for song in test_songs[:3]:
            await stats_service.record_play(
                user_id=test_user.id,
                song_id=song.id,
                duration_listened_seconds=100,
            )

        # Record extra plays for first song
        await stats_service.record_play(
            user_id=test_user.id,
            song_id=test_songs[0].id,
            duration_listened_seconds=100,
        )

        overview = await stats_service.get_overview(user_id=test_user.id)

        assert overview["total_plays"] == 4
        assert overview["total_duration_seconds"] == 400
        assert overview["unique_songs"] == 3
        assert overview["unique_artists"] == 2  # Artist 0 and Artist 1
        assert overview["most_played_genre"] in ["Rock", "Pop"]

    async def test_get_overview_with_period(
        self, db_session: AsyncSession, test_song: Song, test_user: User, mock_cache
    ):
        """Test getting overview with period filter."""
        stats_service = StatsService(db_session, cache=mock_cache)

        await stats_service.record_play(
            user_id=test_user.id,
            song_id=test_song.id,
            duration_listened_seconds=100,
        )

        # Test with day period
        overview = await stats_service.get_overview(
            user_id=test_user.id, period=StatsPeriod.DAY
        )

        assert overview["total_plays"] == 1

    async def test_get_top_songs_empty(
        self, db_session: AsyncSession, test_user: User, mock_cache
    ):
        """Test getting top songs when empty."""
        stats_service = StatsService(db_session, cache=mock_cache)

        top_songs = await stats_service.get_top_songs(user_id=test_user.id)

        assert top_songs == []

    async def test_get_top_songs_with_data(
        self,
        db_session: AsyncSession,
        test_songs: list[Song],
        test_user: User,
        mock_cache,
    ):
        """Test getting top songs with data."""
        stats_service = StatsService(db_session, cache=mock_cache)

        # Record plays - more for first song
        for _ in range(3):
            await stats_service.record_play(
                user_id=test_user.id,
                song_id=test_songs[0].id,
                duration_listened_seconds=100,
            )
        await stats_service.record_play(
            user_id=test_user.id,
            song_id=test_songs[1].id,
            duration_listened_seconds=100,
        )

        top_songs = await stats_service.get_top_songs(user_id=test_user.id, limit=2)

        assert len(top_songs) == 2
        assert top_songs[0]["play_count"] == 3
        assert top_songs[0]["song"].id == test_songs[0].id
        assert top_songs[1]["play_count"] == 1

    async def test_get_top_artists_empty(
        self, db_session: AsyncSession, test_user: User, mock_cache
    ):
        """Test getting top artists when empty."""
        stats_service = StatsService(db_session, cache=mock_cache)

        top_artists = await stats_service.get_top_artists(user_id=test_user.id)

        assert top_artists == []

    async def test_get_top_artists_with_data(
        self,
        db_session: AsyncSession,
        test_songs: list[Song],
        test_user: User,
        mock_cache,
    ):
        """Test getting top artists with data."""
        stats_service = StatsService(db_session, cache=mock_cache)

        # Record plays for Artist 0 songs (songs 0, 2, 4)
        for i in [0, 2, 4]:
            await stats_service.record_play(
                user_id=test_user.id,
                song_id=test_songs[i].id,
                duration_listened_seconds=100,
            )

        # Record one play for Artist 1 (songs 1, 3)
        await stats_service.record_play(
            user_id=test_user.id,
            song_id=test_songs[1].id,
            duration_listened_seconds=100,
        )

        top_artists = await stats_service.get_top_artists(user_id=test_user.id, limit=2)

        assert len(top_artists) == 2
        assert top_artists[0]["artist"] == "Artist 0"
        assert top_artists[0]["play_count"] == 3
        assert len(top_artists[0]["songs"]) > 0


class TestStatsEndpoints:
    """Tests for stats API endpoints."""

    async def test_record_play(
        self, client: AsyncClient, auth_headers: dict, test_song: Song
    ):
        """Test POST /stats/play endpoint."""
        with patch("app.services.stats.get_cache_service") as mock_get_cache:
            mock_cache = MagicMock(spec=CacheService)
            mock_cache.delete_pattern = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache

            response = await client.post(
                "/api/v1/stats/play",
                headers=auth_headers,
                json={
                    "song_id": str(test_song.id),
                    "duration_listened_seconds": 120,
                    "completed": True,
                    "context_type": "library",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data
        assert "played_at" in data

    async def test_record_play_song_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test POST /stats/play with non-existent song."""
        with patch("app.services.stats.get_cache_service") as mock_get_cache:
            mock_cache = MagicMock(spec=CacheService)
            mock_cache.delete_pattern = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache

            response = await client.post(
                "/api/v1/stats/play",
                headers=auth_headers,
                json={
                    "song_id": str(uuid4()),
                    "duration_listened_seconds": 120,
                },
            )

        assert response.status_code == 404

    async def test_get_history_empty(self, client: AsyncClient, auth_headers: dict):
        """Test GET /stats/history when empty."""
        response = await client.get("/api/v1/stats/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_get_history_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_song: Song,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test GET /stats/history with data."""
        # Create a history record directly
        history = ListeningHistory(
            user_id=test_user.id,
            song_id=test_song.id,
            played_duration_seconds=120,
            completed=True,
        )
        db_session.add(history)
        await db_session.flush()

        response = await client.get("/api/v1/stats/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1

    async def test_get_overview(self, client: AsyncClient, auth_headers: dict):
        """Test GET /stats/overview endpoint."""
        with patch("app.services.stats.get_cache_service") as mock_get_cache:
            mock_cache = MagicMock(spec=CacheService)
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache

            response = await client.get("/api/v1/stats/overview", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_plays" in data
        assert "total_duration_seconds" in data
        assert "unique_songs" in data
        assert "unique_artists" in data

    async def test_get_overview_with_period(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test GET /stats/overview with period parameter."""
        with patch("app.services.stats.get_cache_service") as mock_get_cache:
            mock_cache = MagicMock(spec=CacheService)
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache

            response = await client.get(
                "/api/v1/stats/overview?period=week", headers=auth_headers
            )

        assert response.status_code == 200

    async def test_get_top_songs(self, client: AsyncClient, auth_headers: dict):
        """Test GET /stats/top-songs endpoint."""
        response = await client.get("/api/v1/stats/top-songs", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_get_top_artists(self, client: AsyncClient, auth_headers: dict):
        """Test GET /stats/top-artists endpoint."""
        response = await client.get("/api/v1/stats/top-artists", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/v1/stats/play",
            "/api/v1/stats/history",
            "/api/v1/stats/overview",
            "/api/v1/stats/top-songs",
            "/api/v1/stats/top-artists",
        ]

        for endpoint in endpoints:
            if endpoint == "/api/v1/stats/play":
                response = await client.post(endpoint, json={})
            else:
                response = await client.get(endpoint)

            assert response.status_code in (401, 403)
