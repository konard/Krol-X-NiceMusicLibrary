"""Tests for mood chains service and endpoints."""

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.listening_history import ListeningHistory
from app.models.mood_chain import MoodChain, TransitionStyle
from app.models.song import Song
from app.models.user import User
from app.schemas.mood_chain import (
    MoodChainCreate,
    MoodChainFromHistoryRequest,
    MoodChainTransitionBase,
    MoodChainUpdate,
)
from app.services.mood_chain import (
    MoodChainNotFoundError,
    MoodChainService,
    SongAlreadyInMoodChainError,
    SongNotFoundError,
    SongNotInMoodChainError,
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
        energy=0.7,
        valence=0.6,
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
        energy=0.5,
        valence=0.4,
    )
    db_session.add(song)
    await db_session.flush()
    return song


@pytest.fixture
async def test_song3(db_session: AsyncSession, test_user: User) -> Song:
    """Create a third test song."""
    song = Song(
        owner_id=test_user.id,
        title="Third Song",
        artist="Third Artist",
        album="Third Album",
        genre="Rock",
        year=2024,
        duration_seconds=220,
        file_path="/tmp/test_song3.mp3",
        file_size_bytes=7000000,
        file_format="mp3",
        bitrate=320,
        sample_rate=44100,
        energy=0.8,
        valence=0.7,
    )
    db_session.add(song)
    await db_session.flush()
    return song


@pytest.fixture
async def test_mood_chain(db_session: AsyncSession, test_user: User) -> MoodChain:
    """Create a test mood chain."""
    mood_chain = MoodChain(
        owner_id=test_user.id,
        name="Test Mood Chain",
        description="A test mood chain",
        transition_style=TransitionStyle.SMOOTH,
    )
    db_session.add(mood_chain)
    await db_session.flush()
    return mood_chain


class TestMoodChainService:
    """Tests for MoodChainService."""

    async def test_create_mood_chain(self, db_session: AsyncSession, test_user: User):
        """Test creating a mood chain."""
        service = MoodChainService(db_session)
        data = MoodChainCreate(name="New Chain", description="My chain")
        mood_chain = await service.create_mood_chain(test_user.id, data)

        assert mood_chain.name == "New Chain"
        assert mood_chain.description == "My chain"
        assert mood_chain.owner_id == test_user.id
        assert mood_chain.song_count == 0
        assert mood_chain.transition_style == TransitionStyle.SMOOTH
        assert mood_chain.auto_advance is True
        assert mood_chain.auto_advance_delay_seconds == 10

    async def test_create_mood_chain_with_songs(
        self, db_session: AsyncSession, test_user: User, test_song: Song
    ):
        """Test creating a mood chain with initial songs."""
        service = MoodChainService(db_session)
        data = MoodChainCreate(name="With Songs", song_ids=[test_song.id])
        mood_chain = await service.create_mood_chain(test_user.id, data)

        assert mood_chain.song_count == 1

    async def test_get_mood_chain_by_id(
        self, db_session: AsyncSession, test_mood_chain: MoodChain, test_user: User
    ):
        """Test getting mood chain by ID."""
        service = MoodChainService(db_session)
        mood_chain = await service.get_mood_chain_by_id(
            test_mood_chain.id, test_user.id
        )

        assert mood_chain is not None
        assert mood_chain.id == test_mood_chain.id

    async def test_get_mood_chain_by_id_wrong_owner(
        self, db_session: AsyncSession, test_mood_chain: MoodChain
    ):
        """Test getting mood chain with wrong owner."""
        service = MoodChainService(db_session)
        mood_chain = await service.get_mood_chain_by_id(test_mood_chain.id, uuid4())

        assert mood_chain is None

    async def test_get_mood_chains(
        self, db_session: AsyncSession, test_mood_chain: MoodChain, test_user: User
    ):
        """Test getting mood chains."""
        service = MoodChainService(db_session)
        mood_chains, total = await service.get_mood_chains(test_user.id)

        assert len(mood_chains) == 1
        assert total == 1
        assert mood_chains[0].id == test_mood_chain.id

    async def test_update_mood_chain(
        self, db_session: AsyncSession, test_mood_chain: MoodChain, test_user: User
    ):
        """Test updating mood chain."""
        service = MoodChainService(db_session)
        data = MoodChainUpdate(
            name="Updated Name", transition_style=TransitionStyle.RANDOM
        )
        mood_chain = await service.update_mood_chain(
            test_mood_chain.id, test_user.id, data
        )

        assert mood_chain.name == "Updated Name"
        assert mood_chain.transition_style == TransitionStyle.RANDOM

    async def test_update_mood_chain_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating non-existent mood chain."""
        service = MoodChainService(db_session)
        data = MoodChainUpdate(name="Updated Name")

        with pytest.raises(MoodChainNotFoundError):
            await service.update_mood_chain(uuid4(), test_user.id, data)

    async def test_delete_mood_chain(
        self, db_session: AsyncSession, test_mood_chain: MoodChain, test_user: User
    ):
        """Test deleting mood chain."""
        service = MoodChainService(db_session)
        await service.delete_mood_chain(test_mood_chain.id, test_user.id)

        mood_chain = await service.get_mood_chain_by_id(
            test_mood_chain.id, test_user.id
        )
        assert mood_chain is None

    async def test_delete_mood_chain_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test deleting non-existent mood chain."""
        service = MoodChainService(db_session)

        with pytest.raises(MoodChainNotFoundError):
            await service.delete_mood_chain(uuid4(), test_user.id)

    async def test_add_song_to_mood_chain(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_user: User,
    ):
        """Test adding song to mood chain."""
        service = MoodChainService(db_session)
        mood_chain = await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )

        assert mood_chain.song_count == 1
        assert len(mood_chain.mood_chain_songs) == 1
        assert mood_chain.mood_chain_songs[0].song_id == test_song.id
        assert mood_chain.mood_chain_songs[0].position == 0

    async def test_add_song_to_mood_chain_with_position(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
        test_user: User,
    ):
        """Test adding song at specific position."""
        service = MoodChainService(db_session)

        # Add first song
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )

        # Add second song at position 0
        mood_chain = await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song2.id, test_user.id, position=0
        )

        assert mood_chain.song_count == 2
        songs = sorted(mood_chain.mood_chain_songs, key=lambda x: x.position)
        assert songs[0].song_id == test_song2.id
        assert songs[0].position == 0
        assert songs[1].song_id == test_song.id
        assert songs[1].position == 1

    async def test_add_song_to_mood_chain_already_exists(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_user: User,
    ):
        """Test adding duplicate song to mood chain."""
        service = MoodChainService(db_session)
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )

        with pytest.raises(SongAlreadyInMoodChainError):
            await service.add_song_to_mood_chain(
                test_mood_chain.id, test_song.id, test_user.id
            )

    async def test_add_song_to_mood_chain_song_not_found(
        self, db_session: AsyncSession, test_mood_chain: MoodChain, test_user: User
    ):
        """Test adding non-existent song to mood chain."""
        service = MoodChainService(db_session)

        with pytest.raises(SongNotFoundError):
            await service.add_song_to_mood_chain(
                test_mood_chain.id, uuid4(), test_user.id
            )

    async def test_remove_song_from_mood_chain(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_user: User,
    ):
        """Test removing song from mood chain."""
        service = MoodChainService(db_session)
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )

        mood_chain = await service.remove_song_from_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )

        assert mood_chain.song_count == 0

    async def test_remove_song_from_mood_chain_not_in_chain(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_user: User,
    ):
        """Test removing song not in mood chain."""
        service = MoodChainService(db_session)

        with pytest.raises(SongNotInMoodChainError):
            await service.remove_song_from_mood_chain(
                test_mood_chain.id, test_song.id, test_user.id
            )

    async def test_reorder_mood_chain_songs(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
        test_user: User,
    ):
        """Test reordering songs in mood chain."""
        service = MoodChainService(db_session)

        # Add songs
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song2.id, test_user.id
        )

        # Reorder
        mood_chain = await service.reorder_mood_chain_songs(
            test_mood_chain.id,
            [test_song2.id, test_song.id],
            test_user.id,
        )

        songs = sorted(mood_chain.mood_chain_songs, key=lambda x: x.position)
        assert songs[0].song_id == test_song2.id
        assert songs[1].song_id == test_song.id

    async def test_reorder_mood_chain_songs_invalid_ids(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_user: User,
    ):
        """Test reordering with invalid song IDs."""
        service = MoodChainService(db_session)
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )

        with pytest.raises(ValueError):
            await service.reorder_mood_chain_songs(
                test_mood_chain.id,
                [uuid4()],
                test_user.id,
            )

    async def test_update_transitions(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
        test_user: User,
    ):
        """Test updating transitions."""
        service = MoodChainService(db_session)

        # Add songs
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song2.id, test_user.id
        )

        # Update transitions
        transitions = [
            MoodChainTransitionBase(
                from_song_id=test_song.id, to_song_id=test_song2.id, weight=0.9
            )
        ]
        mood_chain = await service.update_transitions(
            test_mood_chain.id, transitions, test_user.id
        )

        assert len(mood_chain.mood_chain_transitions) == 1
        assert mood_chain.mood_chain_transitions[0].weight == 0.9

    async def test_get_next_song_suggestions(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
        test_user: User,
    ):
        """Test getting next song suggestions."""
        service = MoodChainService(db_session)

        # Add songs
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song.id, test_user.id
        )
        await service.add_song_to_mood_chain(
            test_mood_chain.id, test_song2.id, test_user.id
        )

        suggestions = await service.get_next_song_suggestions(
            test_mood_chain.id, test_song.id, test_user.id
        )

        assert len(suggestions) == 1
        assert suggestions[0]["song_id"] == test_song2.id

    async def test_record_transition_played(
        self,
        db_session: AsyncSession,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
        test_user: User,
    ):
        """Test recording transition played."""
        service = MoodChainService(db_session)

        success = await service.record_transition_played(
            test_mood_chain.id, test_song.id, test_song2.id, test_user.id
        )

        assert success is True

        # Verify mood chain was updated
        mood_chain = await service.get_mood_chain_by_id(
            test_mood_chain.id, test_user.id
        )
        assert mood_chain.play_count == 1

    async def test_create_from_history(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_song: Song,
        test_song2: Song,
    ):
        """Test creating mood chain from listening history."""
        service = MoodChainService(db_session)

        # Create listening history
        for _ in range(3):
            history = ListeningHistory(
                user_id=test_user.id,
                song_id=test_song.id,
                played_duration_seconds=180,
            )
            db_session.add(history)
            history = ListeningHistory(
                user_id=test_user.id,
                song_id=test_song2.id,
                played_duration_seconds=200,
            )
            db_session.add(history)
        await db_session.flush()

        data = MoodChainFromHistoryRequest(name="From History", min_plays=2)
        mood_chain = await service.create_from_history(test_user.id, data)

        assert mood_chain.name == "From History"
        assert mood_chain.is_auto_generated is True
        assert mood_chain.song_count >= 1


class TestMoodChainsEndpoints:
    """Tests for mood chains API endpoints."""

    async def test_list_mood_chains_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test listing mood chains when none exist."""
        response = await client.get("/api/v1/mood-chains", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_mood_chains_with_chain(
        self, client: AsyncClient, auth_headers: dict, test_mood_chain: MoodChain
    ):
        """Test listing mood chains when one exists."""
        response = await client.get("/api/v1/mood-chains", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Mood Chain"

    async def test_list_mood_chains_unauthorized(self, client: AsyncClient):
        """Test listing mood chains without auth fails."""
        response = await client.get("/api/v1/mood-chains")

        assert response.status_code in (401, 403)

    async def test_create_mood_chain(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test creating a mood chain."""
        response = await client.post(
            "/api/v1/mood-chains",
            headers=auth_headers,
            json={"name": "New Chain", "description": "My new chain"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Chain"
        assert data["description"] == "My new chain"
        assert data["song_count"] == 0

    async def test_get_mood_chain(
        self, client: AsyncClient, auth_headers: dict, test_mood_chain: MoodChain
    ):
        """Test getting mood chain details."""
        response = await client.get(
            f"/api/v1/mood-chains/{test_mood_chain.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Mood Chain"
        assert data["songs"] == []
        assert data["transitions"] == []

    async def test_get_mood_chain_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent mood chain returns 404."""
        response = await client.get(
            f"/api/v1/mood-chains/{uuid4()}", headers=auth_headers
        )

        assert response.status_code == 404

    async def test_update_mood_chain(
        self, client: AsyncClient, auth_headers: dict, test_mood_chain: MoodChain
    ):
        """Test updating mood chain."""
        response = await client.patch(
            f"/api/v1/mood-chains/{test_mood_chain.id}",
            headers=auth_headers,
            json={"name": "Updated Chain", "transition_style": "random"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Chain"
        assert data["transition_style"] == "random"

    async def test_delete_mood_chain(
        self, client: AsyncClient, auth_headers: dict, test_mood_chain: MoodChain
    ):
        """Test deleting mood chain."""
        response = await client.delete(
            f"/api/v1/mood-chains/{test_mood_chain.id}", headers=auth_headers
        )

        assert response.status_code == 204

    async def test_add_song_to_mood_chain(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_mood_chain: MoodChain,
        test_song: Song,
    ):
        """Test adding song to mood chain."""
        response = await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["song_count"] == 1
        assert len(data["songs"]) == 1
        assert data["songs"][0]["song_id"] == str(test_song.id)

    async def test_add_song_to_mood_chain_conflict(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_mood_chain: MoodChain,
        test_song: Song,
    ):
        """Test adding duplicate song returns 409."""
        await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )

        response = await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )

        assert response.status_code == 409

    async def test_remove_song_from_mood_chain(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_mood_chain: MoodChain,
        test_song: Song,
    ):
        """Test removing song from mood chain."""
        await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )

        response = await client.delete(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs/{test_song.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["song_count"] == 0

    async def test_reorder_mood_chain_songs(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
    ):
        """Test reordering songs in mood chain."""
        # Add songs
        await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )
        await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song2.id)},
        )

        # Reorder
        response = await client.put(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs/order",
            headers=auth_headers,
            json={"song_ids": [str(test_song2.id), str(test_song.id)]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["songs"][0]["song_id"] == str(test_song2.id)
        assert data["songs"][1]["song_id"] == str(test_song.id)

    async def test_update_transitions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
    ):
        """Test updating transitions."""
        # Add songs
        await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )
        await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song2.id)},
        )

        # Update transitions
        response = await client.put(
            f"/api/v1/mood-chains/{test_mood_chain.id}/transitions",
            headers=auth_headers,
            json={
                "transitions": [
                    {
                        "from_song_id": str(test_song.id),
                        "to_song_id": str(test_song2.id),
                        "weight": 0.9,
                    }
                ]
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["transitions"]) == 1
        assert data["transitions"][0]["weight"] == 0.9

    async def test_create_from_history(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
        test_song: Song,
        test_song2: Song,
    ):
        """Test creating mood chain from history."""
        # Create listening history
        for _ in range(3):
            history = ListeningHistory(
                user_id=test_user.id,
                song_id=test_song.id,
                played_duration_seconds=180,
            )
            db_session.add(history)
            history = ListeningHistory(
                user_id=test_user.id,
                song_id=test_song2.id,
                played_duration_seconds=200,
            )
            db_session.add(history)
        await db_session.flush()

        response = await client.post(
            "/api/v1/mood-chains/from-history",
            headers=auth_headers,
            json={"name": "From History", "min_plays": 2},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "From History"
        assert data["is_auto_generated"] is True

    async def test_get_next_song(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
    ):
        """Test getting next song suggestions."""
        # Add songs
        await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song.id)},
        )
        await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/songs",
            headers=auth_headers,
            json={"song_id": str(test_song2.id)},
        )

        response = await client.get(
            f"/api/v1/mood-chains/{test_mood_chain.id}/next"
            f"?current_song_id={test_song.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 1

    async def test_record_transition_played(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_mood_chain: MoodChain,
        test_song: Song,
        test_song2: Song,
    ):
        """Test recording transition played."""
        response = await client.post(
            f"/api/v1/mood-chains/{test_mood_chain.id}/transition-played",
            headers=auth_headers,
            json={
                "from_song_id": str(test_song.id),
                "to_song_id": str(test_song2.id),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_list_mood_chains_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test mood chains pagination."""
        # Create multiple mood chains
        for i in range(15):
            chain = MoodChain(
                owner_id=test_user.id,
                name=f"Chain {i}",
            )
            db_session.add(chain)
        await db_session.flush()

        # Get first page
        response = await client.get(
            "/api/v1/mood-chains?page=1&limit=10", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15
        assert data["pages"] == 2

        # Get second page
        response = await client.get(
            "/api/v1/mood-chains?page=2&limit=10", headers=auth_headers
        )
        data = response.json()
        assert len(data["items"]) == 5
