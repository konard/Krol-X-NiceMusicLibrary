"""Tests for authentication service and endpoints."""

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.auth import (
    AuthService,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
)


def get_test_database_url() -> str:
    """Get database URL for testing.

    Uses PostgreSQL if environment variables are set (CI), otherwise raises error.
    """
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_user = os.getenv("POSTGRES_USER", "test")
    pg_password = os.getenv("POSTGRES_PASSWORD", "test")
    pg_db = os.getenv("POSTGRES_DB", "test")
    return f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"


# Create test database URL
TEST_DATABASE_URL = get_test_database_url()


@pytest.fixture
async def db_session():
    """Create a test database session.

    Creates the engine inside the fixture to avoid event loop issues with asyncpg.
    """
    # Create engine inside fixture to use the correct event loop
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    # Create session factory
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create and yield session
    async with session_factory() as session:
        yield session

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine
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
def user_data() -> UserCreate:
    """Create test user data."""
    return UserCreate(
        email="test@example.com",
        username="testuser",
        password="SecurePass123",
    )


@pytest.fixture
async def auth_service(db_session: AsyncSession) -> AuthService:
    """Create auth service with test session."""
    return AuthService(db_session)


@pytest.fixture
async def existing_user(db_session: AsyncSession, user_data: UserCreate) -> User:
    """Create an existing user in the database."""
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
    )
    db_session.add(user)
    await db_session.flush()
    return user


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_password_hash_is_different_from_password(self):
        """Test that hashed password is different from original."""
        password = "SecurePass123"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_verify_password_correct(self):
        """Test that correct password verifies successfully."""
        password = "SecurePass123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that incorrect password fails verification."""
        password = "SecurePass123"
        hashed = get_password_hash(password)
        assert verify_password("WrongPassword123", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (bcrypt salt)."""
        password = "SecurePass123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests for JWT token utilities."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "test-user-id"
        token = create_access_token(user_id)
        assert token is not None
        assert isinstance(token, str)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "test-user-id"
        token = create_refresh_token(user_id)
        assert token is not None
        assert isinstance(token, str)

    def test_decode_access_token(self):
        """Test access token decoding."""
        user_id = "test-user-id"
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_refresh_token(self):
        """Test refresh token decoding."""
        user_id = "test-user-id"
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None."""
        payload = decode_token("invalid-token")
        assert payload is None

    def test_access_and_refresh_tokens_are_different(self):
        """Test that access and refresh tokens are different."""
        user_id = "test-user-id"
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        assert access_token != refresh_token


class TestAuthService:
    """Tests for AuthService class."""

    async def test_register_success(
        self,
        auth_service: AuthService,
        user_data: UserCreate,
    ):
        """Test successful user registration."""
        user, tokens = await auth_service.register(user_data)

        assert user.email == user_data.email
        assert user.username == user_data.username
        assert user.password_hash != user_data.password
        assert verify_password(user_data.password, user.password_hash)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None

    async def test_register_duplicate_email(
        self,
        auth_service: AuthService,
        user_data: UserCreate,
        existing_user: User,
    ):
        """Test registration fails with duplicate email."""
        with pytest.raises(UserAlreadyExistsError):
            await auth_service.register(user_data)

    async def test_register_duplicate_username(
        self,
        auth_service: AuthService,
        user_data: UserCreate,
        existing_user: User,
    ):
        """Test registration fails with duplicate username."""
        new_user_data = UserCreate(
            email="different@example.com",
            username=user_data.username,
            password="SecurePass123",
        )
        with pytest.raises(UserAlreadyExistsError):
            await auth_service.register(new_user_data)

    async def test_login_success(
        self,
        auth_service: AuthService,
        user_data: UserCreate,
        existing_user: User,
    ):
        """Test successful login."""
        user, tokens = await auth_service.login(user_data.email, user_data.password)

        assert user.email == user_data.email
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None

    async def test_login_invalid_email(
        self,
        auth_service: AuthService,
        existing_user: User,
    ):
        """Test login fails with invalid email."""
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("wrong@example.com", "SecurePass123")

    async def test_login_invalid_password(
        self,
        auth_service: AuthService,
        user_data: UserCreate,
        existing_user: User,
    ):
        """Test login fails with invalid password."""
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(user_data.email, "WrongPassword123")

    async def test_refresh_tokens_success(
        self,
        auth_service: AuthService,
        existing_user: User,
    ):
        """Test successful token refresh."""
        refresh_token = create_refresh_token(str(existing_user.id))
        new_tokens = await auth_service.refresh_tokens(refresh_token)

        assert new_tokens.access_token is not None
        assert new_tokens.refresh_token is not None

    async def test_refresh_tokens_invalid_token(
        self,
        auth_service: AuthService,
    ):
        """Test token refresh fails with invalid token."""
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_tokens("invalid-token")

    async def test_refresh_tokens_with_access_token(
        self,
        auth_service: AuthService,
        existing_user: User,
    ):
        """Test token refresh fails when using access token instead of refresh."""
        access_token = create_access_token(str(existing_user.id))
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_tokens(access_token)

    async def test_get_current_user_success(
        self,
        auth_service: AuthService,
        existing_user: User,
    ):
        """Test getting current user from access token."""
        access_token = create_access_token(str(existing_user.id))
        user = await auth_service.get_current_user(access_token)

        assert user.id == existing_user.id
        assert user.email == existing_user.email

    async def test_get_current_user_invalid_token(
        self,
        auth_service: AuthService,
    ):
        """Test getting current user fails with invalid token."""
        with pytest.raises(InvalidTokenError):
            await auth_service.get_current_user("invalid-token")


class TestAuthEndpoints:
    """Tests for authentication API endpoints."""

    async def test_register_endpoint(self, client: AsyncClient):
        """Test POST /api/v1/auth/register endpoint."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "username": "newuser",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["username"] == "newuser"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    async def test_register_endpoint_invalid_password(self, client: AsyncClient):
        """Test registration fails with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "weak",
            },
        )

        assert response.status_code == 422

    async def test_register_endpoint_duplicate_email(self, client: AsyncClient):
        """Test registration fails with duplicate email."""
        # Register first user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123",
            },
        )

        # Try to register with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "different",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 400

    async def test_login_endpoint(self, client: AsyncClient):
        """Test POST /api/v1/auth/login endpoint."""
        # Register user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123",
            },
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "tokens" in data

    async def test_login_endpoint_invalid_credentials(self, client: AsyncClient):
        """Test login fails with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 401

    async def test_refresh_endpoint(self, client: AsyncClient):
        """Test POST /api/v1/auth/refresh endpoint."""
        # Register user first
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123",
            },
        )
        refresh_token = register_response.json()["tokens"]["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data

    async def test_refresh_endpoint_invalid_token(self, client: AsyncClient):
        """Test refresh fails with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401

    async def test_me_endpoint(self, client: AsyncClient):
        """Test GET /api/v1/auth/me endpoint."""
        # Register user first
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123",
            },
        )
        access_token = register_response.json()["tokens"]["access_token"]

        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    async def test_me_endpoint_no_auth(self, client: AsyncClient):
        """Test /me fails without authentication."""
        response = await client.get("/api/v1/auth/me")

        # HTTPBearer returns 403 when no credentials provided
        # Accept both 401 and 403 as both are valid for "not authenticated"
        assert response.status_code in (401, 403)

    async def test_me_endpoint_invalid_token(self, client: AsyncClient):
        """Test /me fails with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
