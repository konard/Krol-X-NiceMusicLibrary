"""Tests for tags service and endpoints."""

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.song import Song
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagUpdate
from app.services.tag import (
    SongNotFoundError,
    TagAlreadyExistsError,
    TagAlreadyOnSongError,
    TagNotFoundError,
    TagNotOnSongError,
    TagService,
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
async def test_tag(db_session: AsyncSession, test_user: User) -> Tag:
    """Create a test tag."""
    tag = Tag(
        owner_id=test_user.id,
        name="Rock",
        color="#FF5733",
    )
    db_session.add(tag)
    await db_session.flush()
    return tag


@pytest.fixture
async def test_tag2(db_session: AsyncSession, test_user: User) -> Tag:
    """Create a second test tag."""
    tag = Tag(
        owner_id=test_user.id,
        name="Favorite",
        color="#00FF00",
    )
    db_session.add(tag)
    await db_session.flush()
    return tag


class TestTagService:
    """Tests for TagService."""

    async def test_create_tag(self, db_session: AsyncSession, test_user: User):
        """Test creating a tag."""
        service = TagService(db_session)
        data = TagCreate(name="New Tag", color="#FF0000")
        tag = await service.create_tag(test_user.id, data)

        assert tag.name == "New Tag"
        assert tag.color == "#FF0000"
        assert tag.owner_id == test_user.id

    async def test_create_tag_without_color(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test creating a tag without color."""
        service = TagService(db_session)
        data = TagCreate(name="No Color Tag")
        tag = await service.create_tag(test_user.id, data)

        assert tag.name == "No Color Tag"
        assert tag.color is None

    async def test_create_tag_duplicate_name(
        self, db_session: AsyncSession, test_tag: Tag, test_user: User
    ):
        """Test creating tag with duplicate name fails."""
        service = TagService(db_session)
        data = TagCreate(name="Rock")

        with pytest.raises(TagAlreadyExistsError):
            await service.create_tag(test_user.id, data)

    async def test_get_tag_by_id(
        self, db_session: AsyncSession, test_tag: Tag, test_user: User
    ):
        """Test getting tag by ID."""
        service = TagService(db_session)
        tag = await service.get_tag_by_id(test_tag.id, test_user.id)

        assert tag is not None
        assert tag.id == test_tag.id

    async def test_get_tag_by_id_wrong_owner(
        self, db_session: AsyncSession, test_tag: Tag
    ):
        """Test getting tag with wrong owner returns None."""
        service = TagService(db_session)
        tag = await service.get_tag_by_id(test_tag.id, uuid4())

        assert tag is None

    async def test_get_tags(
        self, db_session: AsyncSession, test_tag: Tag, test_user: User
    ):
        """Test getting all tags."""
        service = TagService(db_session)
        tags = await service.get_tags(test_user.id)

        assert len(tags) == 1
        assert tags[0].id == test_tag.id

    async def test_get_tags_sorted_by_name(
        self,
        db_session: AsyncSession,
        test_tag: Tag,
        test_tag2: Tag,
        test_user: User,
    ):
        """Test tags are sorted alphabetically."""
        service = TagService(db_session)
        tags = await service.get_tags(test_user.id)

        assert len(tags) == 2
        # "Favorite" comes before "Rock" alphabetically
        assert tags[0].name == "Favorite"
        assert tags[1].name == "Rock"

    async def test_update_tag(
        self, db_session: AsyncSession, test_tag: Tag, test_user: User
    ):
        """Test updating a tag."""
        service = TagService(db_session)
        data = TagUpdate(name="Updated Rock", color="#0000FF")
        tag = await service.update_tag(test_tag.id, test_user.id, data)

        assert tag.name == "Updated Rock"
        assert tag.color == "#0000FF"

    async def test_update_tag_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating non-existent tag."""
        service = TagService(db_session)
        data = TagUpdate(name="Updated")

        with pytest.raises(TagNotFoundError):
            await service.update_tag(uuid4(), test_user.id, data)

    async def test_update_tag_name_conflict(
        self,
        db_session: AsyncSession,
        test_tag: Tag,
        test_tag2: Tag,
        test_user: User,
    ):
        """Test updating tag name to existing name fails."""
        service = TagService(db_session)
        data = TagUpdate(name="Favorite")  # Already exists

        with pytest.raises(TagAlreadyExistsError):
            await service.update_tag(test_tag.id, test_user.id, data)

    async def test_delete_tag(
        self, db_session: AsyncSession, test_tag: Tag, test_user: User
    ):
        """Test deleting a tag."""
        service = TagService(db_session)
        await service.delete_tag(test_tag.id, test_user.id)

        tag = await service.get_tag_by_id(test_tag.id, test_user.id)
        assert tag is None

    async def test_delete_tag_not_found(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test deleting non-existent tag."""
        service = TagService(db_session)

        with pytest.raises(TagNotFoundError):
            await service.delete_tag(uuid4(), test_user.id)

    async def test_add_tag_to_song(
        self,
        db_session: AsyncSession,
        test_song: Song,
        test_tag: Tag,
        test_user: User,
    ):
        """Test adding tag to song."""
        service = TagService(db_session)
        song = await service.add_tag_to_song(test_song.id, test_tag.id, test_user.id)

        assert len(song.song_tags) == 1
        assert song.song_tags[0].tag.id == test_tag.id

    async def test_add_tag_to_song_already_exists(
        self,
        db_session: AsyncSession,
        test_song: Song,
        test_tag: Tag,
        test_user: User,
    ):
        """Test adding duplicate tag to song fails."""
        service = TagService(db_session)
        await service.add_tag_to_song(test_song.id, test_tag.id, test_user.id)

        with pytest.raises(TagAlreadyOnSongError):
            await service.add_tag_to_song(test_song.id, test_tag.id, test_user.id)

    async def test_add_tag_to_song_song_not_found(
        self, db_session: AsyncSession, test_tag: Tag, test_user: User
    ):
        """Test adding tag to non-existent song."""
        service = TagService(db_session)

        with pytest.raises(SongNotFoundError):
            await service.add_tag_to_song(uuid4(), test_tag.id, test_user.id)

    async def test_add_tag_to_song_tag_not_found(
        self, db_session: AsyncSession, test_song: Song, test_user: User
    ):
        """Test adding non-existent tag to song."""
        service = TagService(db_session)

        with pytest.raises(TagNotFoundError):
            await service.add_tag_to_song(test_song.id, uuid4(), test_user.id)

    async def test_remove_tag_from_song(
        self,
        db_session: AsyncSession,
        test_song: Song,
        test_tag: Tag,
        test_user: User,
    ):
        """Test removing tag from song."""
        service = TagService(db_session)
        await service.add_tag_to_song(test_song.id, test_tag.id, test_user.id)

        song = await service.remove_tag_from_song(
            test_song.id, test_tag.id, test_user.id
        )

        assert len(song.song_tags) == 0

    async def test_remove_tag_from_song_not_on_song(
        self,
        db_session: AsyncSession,
        test_song: Song,
        test_tag: Tag,
        test_user: User,
    ):
        """Test removing tag not on song fails."""
        service = TagService(db_session)

        with pytest.raises(TagNotOnSongError):
            await service.remove_tag_from_song(test_song.id, test_tag.id, test_user.id)


class TestTagsEndpoints:
    """Tests for tags API endpoints."""

    async def test_list_tags_empty(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test listing tags when none exist."""
        response = await client.get("/api/v1/tags", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_list_tags_with_tag(
        self, client: AsyncClient, auth_headers: dict, test_tag: Tag
    ):
        """Test listing tags when one exists."""
        response = await client.get("/api/v1/tags", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Rock"

    async def test_list_tags_unauthorized(self, client: AsyncClient):
        """Test listing tags without auth fails."""
        response = await client.get("/api/v1/tags")

        assert response.status_code in (401, 403)

    async def test_create_tag(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test creating a tag."""
        response = await client.post(
            "/api/v1/tags",
            headers=auth_headers,
            json={"name": "New Tag", "color": "#FF0000"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Tag"
        assert data["color"] == "#FF0000"

    async def test_create_tag_invalid_color(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating tag with invalid color fails."""
        response = await client.post(
            "/api/v1/tags",
            headers=auth_headers,
            json={"name": "Invalid", "color": "not-a-color"},
        )

        assert response.status_code == 422

    async def test_create_tag_duplicate(
        self, client: AsyncClient, auth_headers: dict, test_tag: Tag
    ):
        """Test creating duplicate tag fails."""
        response = await client.post(
            "/api/v1/tags",
            headers=auth_headers,
            json={"name": "Rock"},
        )

        assert response.status_code == 409

    async def test_update_tag(
        self, client: AsyncClient, auth_headers: dict, test_tag: Tag
    ):
        """Test updating a tag."""
        response = await client.patch(
            f"/api/v1/tags/{test_tag.id}",
            headers=auth_headers,
            json={"name": "Updated Rock", "color": "#0000FF"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Rock"
        assert data["color"] == "#0000FF"

    async def test_update_tag_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test updating non-existent tag returns 404."""
        response = await client.patch(
            f"/api/v1/tags/{uuid4()}",
            headers=auth_headers,
            json={"name": "Updated"},
        )

        assert response.status_code == 404

    async def test_delete_tag(
        self, client: AsyncClient, auth_headers: dict, test_tag: Tag
    ):
        """Test deleting a tag."""
        response = await client.delete(
            f"/api/v1/tags/{test_tag.id}", headers=auth_headers
        )

        assert response.status_code == 204

    async def test_delete_tag_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent tag returns 404."""
        response = await client.delete(f"/api/v1/tags/{uuid4()}", headers=auth_headers)

        assert response.status_code == 404


class TestSongTagsEndpoints:
    """Tests for song-tag endpoints."""

    async def test_add_tag_to_song(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_song: Song,
        test_tag: Tag,
    ):
        """Test adding tag to song."""
        response = await client.post(
            f"/api/v1/songs/{test_song.id}/tags",
            headers=auth_headers,
            json={"tag_id": str(test_tag.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "Rock"

    async def test_add_tag_to_song_conflict(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_song: Song,
        test_tag: Tag,
    ):
        """Test adding duplicate tag returns 409."""
        await client.post(
            f"/api/v1/songs/{test_song.id}/tags",
            headers=auth_headers,
            json={"tag_id": str(test_tag.id)},
        )

        response = await client.post(
            f"/api/v1/songs/{test_song.id}/tags",
            headers=auth_headers,
            json={"tag_id": str(test_tag.id)},
        )

        assert response.status_code == 409

    async def test_add_tag_to_song_song_not_found(
        self, client: AsyncClient, auth_headers: dict, test_tag: Tag
    ):
        """Test adding tag to non-existent song."""
        response = await client.post(
            f"/api/v1/songs/{uuid4()}/tags",
            headers=auth_headers,
            json={"tag_id": str(test_tag.id)},
        )

        assert response.status_code == 404

    async def test_add_tag_to_song_tag_not_found(
        self, client: AsyncClient, auth_headers: dict, test_song: Song
    ):
        """Test adding non-existent tag to song."""
        response = await client.post(
            f"/api/v1/songs/{test_song.id}/tags",
            headers=auth_headers,
            json={"tag_id": str(uuid4())},
        )

        assert response.status_code == 404

    async def test_remove_tag_from_song(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_song: Song,
        test_tag: Tag,
    ):
        """Test removing tag from song."""
        await client.post(
            f"/api/v1/songs/{test_song.id}/tags",
            headers=auth_headers,
            json={"tag_id": str(test_tag.id)},
        )

        response = await client.delete(
            f"/api/v1/songs/{test_song.id}/tags/{test_tag.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 0

    async def test_remove_tag_from_song_not_on_song(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_song: Song,
        test_tag: Tag,
    ):
        """Test removing tag not on song returns 404."""
        response = await client.delete(
            f"/api/v1/songs/{test_song.id}/tags/{test_tag.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_multiple_tags_on_song(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_song: Song,
        test_tag: Tag,
        test_tag2: Tag,
    ):
        """Test adding multiple tags to song."""
        await client.post(
            f"/api/v1/songs/{test_song.id}/tags",
            headers=auth_headers,
            json={"tag_id": str(test_tag.id)},
        )

        response = await client.post(
            f"/api/v1/songs/{test_song.id}/tags",
            headers=auth_headers,
            json={"tag_id": str(test_tag2.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 2
        tag_names = {t["name"] for t in data["tags"]}
        assert tag_names == {"Rock", "Favorite"}
