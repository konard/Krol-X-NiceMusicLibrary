"""Database seed data for development and testing."""

import uuid
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ListeningHistory,
    MoodChain,
    MoodChainSong,
    Playlist,
    PlaylistSong,
    Song,
    Tag,
    SongTag,
    User,
)
from app.models.listening_history import ContextType
from app.models.mood_chain import TransitionStyle
from app.models.user import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


async def seed_database(db: AsyncSession) -> None:
    """Seed the database with test data."""
    # Create test users
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        username="admin",
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
        preferences={"theme": "dark", "language": "ru"},
    )

    test_user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        username="testuser",
        password_hash=hash_password("user123"),
        role=UserRole.USER,
        is_active=True,
        preferences={"theme": "auto", "language": "en"},
    )

    db.add(admin_user)
    db.add(test_user)

    # Create test songs for admin user
    songs = []
    for i in range(1, 11):
        song = Song(
            id=uuid.uuid4(),
            owner_id=admin_user.id,
            title=f"Test Song {i}",
            artist=f"Artist {(i - 1) % 3 + 1}",
            album=f"Album {(i - 1) // 3 + 1}",
            genre=["Rock", "Pop", "Electronic"][i % 3],
            year=2020 + (i % 5),
            track_number=i,
            duration_seconds=180 + i * 10,
            file_path=f"/uploads/songs/test_song_{i}.mp3",
            file_size_bytes=5000000 + i * 100000,
            file_format="mp3",
            bitrate=320,
            sample_rate=44100,
            bpm=120 + i * 5,
            energy=0.5 + (i % 5) * 0.1,
            valence=0.4 + (i % 5) * 0.1,
            play_count=i * 10,
            is_favorite=i % 2 == 0,
        )
        songs.append(song)
        db.add(song)

    # Create test playlist
    playlist = Playlist(
        id=uuid.uuid4(),
        owner_id=admin_user.id,
        name="My Favorites",
        description="A collection of my favorite songs",
        is_public=False,
        song_count=5,
        total_duration_seconds=sum(s.duration_seconds for s in songs[:5]),
    )
    db.add(playlist)

    # Add songs to playlist
    for i, song in enumerate(songs[:5]):
        playlist_song = PlaylistSong(
            id=uuid.uuid4(),
            playlist_id=playlist.id,
            song_id=song.id,
            position=i + 1,
        )
        db.add(playlist_song)

    # Create test mood chain
    mood_chain = MoodChain(
        id=uuid.uuid4(),
        owner_id=admin_user.id,
        name="Evening Chill",
        description="Relaxing music for the evening",
        mood_tags=["chill", "relaxing", "evening"],
        is_auto_generated=False,
        transition_style=TransitionStyle.SMOOTH,
        song_count=3,
        play_count=5,
    )
    db.add(mood_chain)

    # Add songs to mood chain
    for i, song in enumerate(songs[5:8]):
        chain_song = MoodChainSong(
            id=uuid.uuid4(),
            mood_chain_id=mood_chain.id,
            song_id=song.id,
            position=i + 1,
            transition_weight=1.0 - i * 0.1,
        )
        db.add(chain_song)

    # Create test tags
    tags = []
    tag_names = ["workout", "study", "party", "relax"]
    tag_colors = ["#FF5733", "#33FF57", "#3357FF", "#F033FF"]
    for name, color in zip(tag_names, tag_colors):
        tag = Tag(
            id=uuid.uuid4(),
            owner_id=admin_user.id,
            name=name,
            color=color,
        )
        tags.append(tag)
        db.add(tag)

    # Add tags to songs
    for i, song in enumerate(songs[:4]):
        song_tag = SongTag(
            id=uuid.uuid4(),
            song_id=song.id,
            tag_id=tags[i].id,
        )
        db.add(song_tag)

    # Create listening history
    now = datetime.now(timezone.utc)
    for i, song in enumerate(songs[:5]):
        history = ListeningHistory(
            id=uuid.uuid4(),
            user_id=admin_user.id,
            song_id=song.id,
            played_at=now - timedelta(hours=i),
            played_duration_seconds=song.duration_seconds - 10,
            completed=True,
            skipped=False,
            context_type=ContextType.LIBRARY,
            device_type="web",
        )
        db.add(history)

    await db.commit()
    print("Database seeded successfully!")


async def clear_database(db: AsyncSession) -> None:
    """Clear all data from the database."""
    # Delete in reverse order of dependencies
    await db.execute("TRUNCATE song_tags CASCADE")
    await db.execute("TRUNCATE tags CASCADE")
    await db.execute("TRUNCATE listening_history CASCADE")
    await db.execute("TRUNCATE mood_chain_songs CASCADE")
    await db.execute("TRUNCATE mood_chains CASCADE")
    await db.execute("TRUNCATE playlist_songs CASCADE")
    await db.execute("TRUNCATE playlists CASCADE")
    await db.execute("TRUNCATE songs CASCADE")
    await db.execute("TRUNCATE users CASCADE")
    await db.commit()
    print("Database cleared successfully!")
