"""Tests for playlists service and endpoints."""

import os
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
from app.schemas.playlist import PlaylistCreate, PlaylistUpdate
from app.services.playlist import (
    PlaylistNotFoundError,
    PlaylistService,
    SongAlreadyInPlaylistError,
    SongNotFoundError,
    SongNotInPlaylistError,
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
async def test_song2(db_session: AsyncSession, test_user: User) -> Song:
    """Create a second test song."""
    song = Song(
        owner_id=test_user.id,
        title="Another Song",
        artist="Another Artist",
        album="Another Album",
        genre="Pop",
        year=2024,
        duration_seconds=200,
        file_path="/tmp/test_song2.mp3",
        file_size_bytes=6000000,
        file_format="mp3",
        bitrate=320,
        sample_rate=44100,
    )
    db_session.add(song)
    await db_session.flush()
    return song


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


class TestPlaylistService:
    """Tests for PlaylistService."""

    async def test_create_playlist(self, db_session: AsyncSession, test_user: User):
        """Test creating a playlist."""
        service = PlaylistService(db_session)
        data = PlaylistCreate(name="New Playlist", description="My playlist")
        playlist = await service.create_playlist(test_user.id, data)

        assert playlist.name == "New Playlist"
        assert playlist.description == "My playlist"
        assert playlist.owner_id == test_user.id
        assert playlist.song_count == 0
        assert playlist.total_duration_seconds == 0

    async def test_get_playlist_by_id(
        self, db_session: AsyncSession, test_playlist: Playlist, test_user: User
    ):
        """Test getting playlist by ID."""
        service = PlaylistService(db_session)
        playlist = await service.get_playlist_by_id(test_playlist.id, test_user.id)

        assert playlist is not None
        assert playlist.id == test_playlist.id

    async def test_get_playlist_by_id_wrong_owner(
        self, db_session: AsyncSession, test_playlist: Playlist
    ):
        """Test getting playlist with wrong owner."""
        service = PlaylistService(db_session)
        playlist = await service.get_playlist_by_id(test_playlist.id, uuid4())

        assert playlist is None

    async def test_get_playlists(
        self, db_session: AsyncSession, test_playlist: Playlist, test_user: User
    ):
        """Test getting playlists."""
        service = PlaylistService(db_session)
        playlists, total = await service.get_playlists(test_user.id)

        assert len(playlists) == 1
        assert total == 1
        assert playlists[0].id == test_playlist.id

    async def test_update_playlist(
        self, db_session: AsyncSession, test_playlist: Playlist, test_user: User
    ):
        """Test updating playlist."""
        service = PlaylistService(db_session)
        data = PlaylistUpdate(name="Updated Name", is_public=True)
        playlist = await service.update_playlist(test_playlist.id, test_user.id, data)

        assert playlist.name == "Updated Name"
        assert playlist.is_public is True

    async def test_update_playlist_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating non-existent playlist."""
        service = PlaylistService(db_session)
        data = PlaylistUpdate(name="Updated Name")

        with pytest.raises(PlaylistNotFoundError):
            await service.update_playlist(uuid4(), test_user.id, data)

    async def test_delete_playlist(
        self, db_session: AsyncSession, test_playlist: Playlist, test_user: User
    ):
        """Test deleting playlist."""
        service = PlaylistService(db_session)
        await service.delete_playlist(test_playlist.id, test_user.id)

        playlist = await service.get_playlist_by_id(test_playlist.id, test_user.id)
        assert playlist is None

    async def test_delete_playlist_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test deleting non-existent playlist."""
        service = PlaylistService(db_session)

        with pytest.raises(PlaylistNotFoundError):
            await service.delete_playlist(uuid4(), test_user.id)

    async def test_add_song_to_playlist(
        self,
        db_session: AsyncSession,
        test_playlist: Playlist,
        test_song: Song,
        test_user: User,
    ):
        """Test adding song to playlist."""
        service = PlaylistService(db_session)
        playlist = await service.add_song_to_playlist(
            test_playlist.id, test_song.id, test_user.id
        )

        assert playlist.song_count == 1
        assert playlist.total_duration_seconds == test_song.duration_seconds
        assert len(playlist.playlist_songs) == 1
        assert playlist.playlist_songs[0].song_id == test_song.id
        assert playlist.playlist_songs[0].position == 0

    async def test_add_song_to_playlist_with_position(
        self,
        db_session: AsyncSession,
        test_playlist: Playlist,
        test_song: Song,
        test_song2: Song,
        test_user: User,
    ):
        """Test adding song at specific position."""
        service = PlaylistService(db_session)

        # Add first song
        await service.add_song_to_playlist(test_playlist.id, test_song.id, test_user.id)

        # Add second song at position 0
        playlist = await service.add_song_to_playlist(
            test_playlist.id, test_song2.id, test_user.id, position=0
        )

        assert playlist.song_count == 2
        songs = sorted(playlist.playlist_songs, key=lambda x: x.position)
        assert songs[0].song_id == test_song2.id
        assert songs[0].position == 0
        assert songs[1].song_id == test_song.id
        assert songs[1].position == 1

    async def test_add_song_to_playlist_already_exists(
        self,
        db_session: AsyncSession,
        test_playlist: Playlist,
        test_song: Song,
        test_user: User,
    ):
        """Test adding duplicate song to playlist."""
        service = PlaylistService(db_session)
        await service.add_song_to_playlist(test_playlist.id, test_song.id, test_user.id)

        with pytest.raises(SongAlreadyInPlaylistError):
            await service.add_song_to_playlist(
                test_playlist.id, test_song.id, test_user.id
            )

    async def test_add_song_to_playlist_song_not_found(
        self, db_session: AsyncSession, test_playlist: Playlist, test_user: User
    ):
        """Test adding non-existent song to playlist."""
        service = PlaylistService(db_session)

        with pytest.raises(SongNotFoundError):
            await service.add_song_to_playlist(test_playlist.id, uuid4(), test_user.id)

    async def test_remove_song_from_playlist(
        self,
        db_session: AsyncSession,
        test_playlist: Playlist,
        test_song: Song,
        test_user: User,
    ):
        """Test removing song from playlist."""
        service = PlaylistService(db_session)
        await service.add_song_to_playlist(test_playlist.id, test_song.id, test_user.id)

        playlist = await service.remove_song_from_playlist(
            test_playlist.id, test_song.id, test_user.id
        )

        assert playlist.song_count == 0
        assert playlist.total_duration_seconds == 0

    async def test_remove_song_from_playlist_not_in_playlist(
        self,
        db_session: AsyncSession,
        test_playlist: Playlist,
        test_song: Song,
        test_user: User,
    ):
        """Test removing song not in playlist."""
        service = PlaylistService(db_session)

        with pytest.raises(SongNotInPlaylistError):
            await service.remove_song_from_playlist(
                test_playlist.id, test_song.id, test_user.id
            )

    async def test_reorder_playlist_songs(
        self,
        db_session: AsyncSession,
        test_playlist: Playlist,
        test_song: Song,
        test_song2: Song,
        test_user: User,
    ):
        """Test reordering songs in playlist."""
        service = PlaylistService(db_session)

        # Add songs
        await service.add_song_to_playlist(test_playlist.id, test_song.id, test_user.id)
        await service.add_song_to_playlist(
            test_playlist.id, test_song2.id, test_user.id
        )

        # Reorder
        playlist = await service.reorder_playlist_songs(
            test_playlist.id,
            [test_song2.id, test_song.id],
            test_user.id,
        )

        songs = sorted(playlist.playlist_songs, key=lambda x: x.position)
        assert songs[0].song_id == test_song2.id
        assert songs[1].song_id == test_song.id

    async def test_reorder_playlist_songs_invalid_ids(
        self,
        db_session: AsyncSession,
        test_playlist: Playlist,
        test_song: Song,
        test_user: User,
    ):
        """Test reordering with invalid song IDs."""
        service = PlaylistService(db_session)
        await service.add_song_to_playlist(test_playlist.id, test_song.id, test_user.id)

        with pytest.raises(ValueError):
            await service.reorder_playlist_songs(
                test_playlist.id,
                [uuid4()],
                test_user.id,
            )


class TestPlaylistsEndpoints:
    """Tests for playlists API endpoints."""

    async def test_list_playlists_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test listing playlists when none exist."""
        response = await client.get("/api/v1/playlists", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_playlists_with_playlist(
        self, client: AsyncClient, auth_headers: dict, test_playlist: Playlist
    ):
        """Test listing playlists when one exists."""
        response = await client.get("/api/v1/playlists", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Playlist"

    async def test_list_playlists_unauthorized(self, client: AsyncClient):
        """Test listing playlists without auth fails."""
        response = await client.get("/api/v1/playlists")

        assert response.status_code in (401, 403)

    async def test_create_playlist(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test creating a playlist."""
        response = await client.post(
            "/api/v1/playlists",
            headers=auth_headers,
            json={"name": "New Playlist", "description": "My new playlist"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Playlist"
        assert data["description"] == "My new playlist"
        assert data["song_count"] == 0

    async def test_get_playlist(
        self, client: AsyncClient, auth_headers: dict, test_playlist: Playlist
    ):
        """Test getting playlist details."""
        response = await client.get(
            f"/api/v1/playlists/{test_playlist.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Playlist"
        assert data["songs"] == []

    async def test_get_playlist_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent playlist returns 404."""
        response = await client.get(
            f"/api/v1/playlists/{uuid4()}", headers=auth_headers
        )

        assert response.status_code == 404

    async def test_update_playlist(
        self, client: AsyncClient, auth_headers: dict, test_playlist: Playlist
    ):
        """Test updating playlist."""
        response = await client.patch(
            f"/api/v1/playlists/{test_playlist.id}",
            headers=auth_headers,
            json={"name": "Updated Playlist", "is_public": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Playlist"
        assert data["is_public"] is True

    async def test_delete_playlist(
        self, client: AsyncClient, auth_headers: dict, test_playlist: Playlist
    ):
        """Test deleting playlist."""
        response = await client.delete(
            f"/api/v1/playlists/{test_playlist.id}", headers=auth_headers
        )

        assert response.status_code == 204

    async def test_add_song_to_playlist(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_playlist: Playlist,
        test_song: Song,
    ):
        """Test adding song to playlist."""
        response = await client.post(
            f"/api/v1/playlists/{test_playlist.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["song_count"] == 1
        assert len(data["songs"]) == 1
        assert data["songs"][0]["song_id"] == str(test_song.id)

    async def test_add_song_to_playlist_conflict(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_playlist: Playlist,
        test_song: Song,
    ):
        """Test adding duplicate song returns 409."""
        await client.post(
            f"/api/v1/playlists/{test_playlist.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )

        response = await client.post(
            f"/api/v1/playlists/{test_playlist.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )

        assert response.status_code == 409

    async def test_remove_song_from_playlist(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_playlist: Playlist,
        test_song: Song,
    ):
        """Test removing song from playlist."""
        await client.post(
            f"/api/v1/playlists/{test_playlist.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )

        response = await client.delete(
            f"/api/v1/playlists/{test_playlist.id}/songs/{test_song.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["song_count"] == 0

    async def test_reorder_playlist_songs(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_playlist: Playlist,
        test_song: Song,
        test_song2: Song,
    ):
        """Test reordering songs in playlist."""
        # Add songs
        await client.post(
            f"/api/v1/playlists/{test_playlist.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )
        await client.post(
            f"/api/v1/playlists/{test_playlist.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song2.id)},
        )

        # Reorder
        response = await client.put(
            f"/api/v1/playlists/{test_playlist.id}/songs/order",
            headers=auth_headers,
            json={"song_ids": [str(test_song2.id), str(test_song.id)]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["songs"][0]["song_id"] == str(test_song2.id)
        assert data["songs"][1]["song_id"] == str(test_song.id)

    async def test_list_playlists_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test playlists pagination."""
        # Create multiple playlists
        for i in range(15):
            playlist = Playlist(
                owner_id=test_user.id,
                name=f"Playlist {i}",
            )
            db_session.add(playlist)
        await db_session.flush()

        # Get first page
        response = await client.get(
            "/api/v1/playlists?page=1&limit=10", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15
        assert data["pages"] == 2

        # Get second page
        response = await client.get(
            "/api/v1/playlists?page=2&limit=10", headers=auth_headers
        )
        data = response.json()
        assert len(data["items"]) == 5
