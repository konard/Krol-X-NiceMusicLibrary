"""Tests for songs service and endpoints."""

import io
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.song import Song
from app.models.user import User
from app.schemas.song import SongFilters, SongUpdate
from app.services.metadata import MetadataExtractor
from app.services.music import MusicService, SongNotFoundError
from app.services.storage import StorageService, UnsupportedFormatError


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
def temp_upload_dir():
    """Create a temporary upload directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestStorageService:
    """Tests for StorageService."""

    def test_get_format_from_content_type(self):
        """Test content type to format conversion."""
        storage = StorageService()
        assert storage.get_format_from_content_type("audio/mpeg") == "mp3"
        assert storage.get_format_from_content_type("audio/flac") == "flac"
        assert storage.get_format_from_content_type("audio/ogg") == "ogg"
        assert storage.get_format_from_content_type("audio/wav") == "wav"
        assert storage.get_format_from_content_type("audio/mp4") == "m4a"
        assert storage.get_format_from_content_type("application/pdf") is None

    def test_get_format_from_filename(self):
        """Test filename to format conversion."""
        storage = StorageService()
        assert storage.get_format_from_filename("song.mp3") == "mp3"
        assert storage.get_format_from_filename("song.FLAC") == "flac"
        assert storage.get_format_from_filename("song.ogg") == "ogg"
        assert storage.get_format_from_filename("song.wav") == "wav"
        assert storage.get_format_from_filename("song.m4a") == "m4a"
        assert storage.get_format_from_filename("document.pdf") is None

    def test_get_mime_type(self):
        """Test format to MIME type conversion."""
        storage = StorageService()
        assert storage.get_mime_type("mp3") == "audio/mpeg"
        assert storage.get_mime_type("flac") == "audio/flac"
        assert storage.get_mime_type("ogg") == "audio/ogg"
        assert storage.get_mime_type("wav") == "audio/wav"
        assert storage.get_mime_type("m4a") == "audio/mp4"
        assert storage.get_mime_type("unknown") == "application/octet-stream"

    async def test_save_audio_file(self, temp_upload_dir):
        """Test saving audio file."""
        storage = StorageService(upload_dir=temp_upload_dir)
        owner_id = uuid4()
        content = b"fake audio content"
        file = io.BytesIO(content)

        file_path, file_format, file_size = await storage.save_audio_file(
            file, owner_id, "test.mp3", "audio/mpeg"
        )

        assert file_format == "mp3"
        assert file_size == len(content)
        assert Path(file_path).exists()

    async def test_save_audio_file_unsupported_format(self, temp_upload_dir):
        """Test saving unsupported file format raises error."""
        storage = StorageService(upload_dir=temp_upload_dir)
        owner_id = uuid4()
        file = io.BytesIO(b"fake content")

        with pytest.raises(UnsupportedFormatError):
            await storage.save_audio_file(file, owner_id, "test.txt", "text/plain")

    async def test_save_cover_art(self, temp_upload_dir):
        """Test saving cover art."""
        storage = StorageService(upload_dir=temp_upload_dir)
        owner_id = uuid4()
        content = b"fake image content"

        file_path = await storage.save_cover_art(content, owner_id, "jpg")

        assert Path(file_path).exists()

    async def test_delete_file(self, temp_upload_dir):
        """Test file deletion."""
        storage = StorageService(upload_dir=temp_upload_dir)

        # Create a file
        file_path = Path(temp_upload_dir) / "test.txt"
        file_path.write_bytes(b"test content")

        await storage.delete_file(str(file_path))

        assert not file_path.exists()

    async def test_read_file_range(self, temp_upload_dir):
        """Test reading file range."""
        storage = StorageService(upload_dir=temp_upload_dir)

        # Create a file
        file_path = Path(temp_upload_dir) / "test.txt"
        content = b"0123456789"
        file_path.write_bytes(content)

        result = await storage.read_file_range(str(file_path), 2, 5)

        assert result == b"234"


class TestMetadataExtractor:
    """Tests for MetadataExtractor."""

    def test_extract_returns_metadata(self):
        """Test metadata extraction with mock."""
        extractor = MetadataExtractor()

        # Create a mock for mutagen.File
        with patch("app.services.metadata.MutagenFile") as mock_file:
            mock_audio = MagicMock()
            mock_audio.info.length = 180
            mock_audio.info.bitrate = 320000
            mock_audio.info.sample_rate = 44100
            mock_audio.tags = {}
            mock_file.return_value = mock_audio

            # We need to test with a supported format
            with patch("app.services.metadata.MP3") as mock_mp3:
                mock_mp3_instance = MagicMock()
                mock_mp3_instance.info.length = 180
                mock_mp3_instance.info.bitrate = 320000
                mock_mp3_instance.info.sample_rate = 44100
                mock_mp3_instance.tags = {}
                mock_mp3.return_value = mock_mp3_instance

                metadata = extractor._extract_mp3("/fake/path.mp3")

                assert metadata.duration_seconds == 180
                assert metadata.bitrate == 320
                assert metadata.sample_rate == 44100


class TestMusicService:
    """Tests for MusicService."""

    async def test_get_song_by_id(
        self, db_session: AsyncSession, test_song: Song, test_user: User
    ):
        """Test getting song by ID."""
        music_service = MusicService(db_session)
        song = await music_service.get_song_by_id(test_song.id, test_user.id)

        assert song is not None
        assert song.id == test_song.id
        assert song.title == "Test Song"

    async def test_get_song_by_id_wrong_owner(
        self, db_session: AsyncSession, test_song: Song
    ):
        """Test getting song by ID with wrong owner returns None."""
        music_service = MusicService(db_session)
        wrong_owner_id = uuid4()
        song = await music_service.get_song_by_id(test_song.id, wrong_owner_id)

        assert song is None

    async def test_get_songs_empty(self, db_session: AsyncSession, test_user: User):
        """Test getting songs when none exist."""
        music_service = MusicService(db_session)
        filters = SongFilters()
        songs, total = await music_service.get_songs(test_user.id, filters)

        assert songs == []
        assert total == 0

    async def test_get_songs_with_song(
        self, db_session: AsyncSession, test_song: Song, test_user: User
    ):
        """Test getting songs when one exists."""
        music_service = MusicService(db_session)
        filters = SongFilters()
        songs, total = await music_service.get_songs(test_user.id, filters)

        assert len(songs) == 1
        assert total == 1
        assert songs[0].id == test_song.id

    async def test_get_songs_with_search(
        self, db_session: AsyncSession, test_song: Song, test_user: User
    ):
        """Test getting songs with search filter."""
        music_service = MusicService(db_session)

        # Search by title
        filters = SongFilters(search="Test Song")
        songs, total = await music_service.get_songs(test_user.id, filters)
        assert len(songs) == 1

        # Search by artist
        filters = SongFilters(search="Test Artist")
        songs, total = await music_service.get_songs(test_user.id, filters)
        assert len(songs) == 1

        # Search with no match
        filters = SongFilters(search="nonexistent")
        songs, total = await music_service.get_songs(test_user.id, filters)
        assert len(songs) == 0

    async def test_get_songs_with_artist_filter(
        self, db_session: AsyncSession, test_song: Song, test_user: User
    ):
        """Test getting songs with artist filter."""
        music_service = MusicService(db_session)

        filters = SongFilters(artist="Test Artist")
        songs, total = await music_service.get_songs(test_user.id, filters)
        assert len(songs) == 1

        filters = SongFilters(artist="Other Artist")
        songs, total = await music_service.get_songs(test_user.id, filters)
        assert len(songs) == 0

    async def test_update_song(
        self, db_session: AsyncSession, test_song: Song, test_user: User
    ):
        """Test updating song metadata."""
        music_service = MusicService(db_session)
        update_data = SongUpdate(title="Updated Title", artist="Updated Artist")

        updated_song = await music_service.update_song(
            test_song.id, test_user.id, update_data
        )

        assert updated_song.title == "Updated Title"
        assert updated_song.artist == "Updated Artist"

    async def test_update_song_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating non-existent song raises error."""
        music_service = MusicService(db_session)
        update_data = SongUpdate(title="Updated Title")

        with pytest.raises(SongNotFoundError):
            await music_service.update_song(uuid4(), test_user.id, update_data)

    async def test_delete_song(
        self,
        db_session: AsyncSession,
        test_song: Song,
        test_user: User,
        temp_upload_dir,
    ):
        """Test deleting a song."""
        # Create a fake file
        test_song.file_path = str(Path(temp_upload_dir) / "test.mp3")
        Path(test_song.file_path).write_bytes(b"fake audio")

        storage = StorageService(upload_dir=temp_upload_dir)
        music_service = MusicService(db_session, storage=storage)

        await music_service.delete_song(test_song.id, test_user.id)

        # Song should be gone
        song = await music_service.get_song_by_id(test_song.id, test_user.id)
        assert song is None

    async def test_delete_song_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test deleting non-existent song raises error."""
        music_service = MusicService(db_session)

        with pytest.raises(SongNotFoundError):
            await music_service.delete_song(uuid4(), test_user.id)

    async def test_increment_play_count(
        self, db_session: AsyncSession, test_song: Song, test_user: User
    ):
        """Test incrementing play count."""
        music_service = MusicService(db_session)
        initial_count = test_song.play_count

        song = await music_service.increment_play_count(test_song.id, test_user.id)

        assert song.play_count == initial_count + 1
        assert song.last_played_at is not None


class TestSongsEndpoints:
    """Tests for songs API endpoints."""

    async def test_list_songs_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test listing songs when none exist."""
        response = await client.get("/api/v1/songs", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_songs_with_song(
        self, client: AsyncClient, auth_headers: dict, test_song: Song
    ):
        """Test listing songs when one exists."""
        response = await client.get("/api/v1/songs", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test Song"

    async def test_list_songs_unauthorized(self, client: AsyncClient):
        """Test listing songs without auth fails."""
        response = await client.get("/api/v1/songs")

        assert response.status_code in (401, 403)

    async def test_get_song(
        self, client: AsyncClient, auth_headers: dict, test_song: Song
    ):
        """Test getting song details."""
        response = await client.get(
            f"/api/v1/songs/{test_song.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Song"
        assert data["artist"] == "Test Artist"

    async def test_get_song_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent song returns 404."""
        fake_id = uuid4()
        response = await client.get(f"/api/v1/songs/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    async def test_update_song(
        self, client: AsyncClient, auth_headers: dict, test_song: Song
    ):
        """Test updating song metadata."""
        response = await client.patch(
            f"/api/v1/songs/{test_song.id}",
            headers=auth_headers,
            json={"title": "Updated Title", "artist": "Updated Artist"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["artist"] == "Updated Artist"

    async def test_update_song_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test updating non-existent song returns 404."""
        fake_id = uuid4()
        response = await client.patch(
            f"/api/v1/songs/{fake_id}",
            headers=auth_headers,
            json={"title": "Updated Title"},
        )

        assert response.status_code == 404

    async def test_delete_song(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_song: Song,
        temp_upload_dir,
        db_session: AsyncSession,
    ):
        """Test deleting a song."""
        # Create a fake file for the song
        test_song.file_path = str(Path(temp_upload_dir) / "test.mp3")
        Path(test_song.file_path).write_bytes(b"fake audio")
        await db_session.flush()

        with (
            patch.object(StorageService, "__init__", lambda *args, **kwargs: None),
            patch.object(StorageService, "delete_file", new_callable=AsyncMock),
        ):
            response = await client.delete(
                f"/api/v1/songs/{test_song.id}", headers=auth_headers
            )

        assert response.status_code == 204

    async def test_delete_song_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent song returns 404."""
        fake_id = uuid4()
        response = await client.delete(f"/api/v1/songs/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    async def test_list_songs_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test songs pagination."""
        # Create multiple songs
        for i in range(25):
            song = Song(
                owner_id=test_user.id,
                title=f"Song {i}",
                artist="Artist",
                duration_seconds=180,
                file_path=f"/tmp/song_{i}.mp3",
                file_size_bytes=5000000,
                file_format="mp3",
            )
            db_session.add(song)
        await db_session.flush()

        # Get first page
        response = await client.get(
            "/api/v1/songs?page=1&limit=10", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["pages"] == 3

        # Get second page
        response = await client.get(
            "/api/v1/songs?page=2&limit=10", headers=auth_headers
        )
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2

    async def test_list_songs_with_filters(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test songs filtering."""
        # Create songs with different attributes
        song1 = Song(
            owner_id=test_user.id,
            title="Rock Song",
            artist="Rock Band",
            genre="Rock",
            year=2020,
            duration_seconds=180,
            file_path="/tmp/rock.mp3",
            file_size_bytes=5000000,
            file_format="mp3",
            is_favorite=True,
        )
        song2 = Song(
            owner_id=test_user.id,
            title="Pop Song",
            artist="Pop Star",
            genre="Pop",
            year=2023,
            duration_seconds=200,
            file_path="/tmp/pop.mp3",
            file_size_bytes=6000000,
            file_format="mp3",
            is_favorite=False,
        )
        db_session.add_all([song1, song2])
        await db_session.flush()

        # Filter by genre
        response = await client.get("/api/v1/songs?genre=Rock", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["genre"] == "Rock"

        # Filter by favorite
        response = await client.get(
            "/api/v1/songs?is_favorite=true", headers=auth_headers
        )
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["is_favorite"] is True

        # Search
        response = await client.get("/api/v1/songs?search=Pop", headers=auth_headers)
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Pop Song"

    async def test_get_song_cover_not_found(
        self, client: AsyncClient, auth_headers: dict, test_song: Song
    ):
        """Test getting song cover when song has no cover."""
        response = await client.get(
            f"/api/v1/songs/{test_song.id}/cover", headers=auth_headers
        )

        assert response.status_code == 404

    async def test_stream_song_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test streaming non-existent song returns 404."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/songs/{fake_id}/stream", headers=auth_headers
        )

        assert response.status_code == 404
