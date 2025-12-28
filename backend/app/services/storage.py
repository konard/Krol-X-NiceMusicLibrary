"""File storage service for managing audio files and cover art."""

import os
import uuid
from pathlib import Path
from typing import IO

import aiofiles  # type: ignore[import-untyped]
import aiofiles.os  # type: ignore[import-untyped]

from app.core.config import settings

# Supported audio formats and their MIME types
SUPPORTED_AUDIO_FORMATS = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/flac": "flac",
    "audio/x-flac": "flac",
    "audio/ogg": "ogg",
    "audio/vorbis": "ogg",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/aac": "m4a",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
}

# Extension to format mapping
EXTENSION_TO_FORMAT = {
    ".mp3": "mp3",
    ".flac": "flac",
    ".ogg": "ogg",
    ".wav": "wav",
    ".m4a": "m4a",
    ".aac": "m4a",
}

# MIME types for streaming
FORMAT_MIME_TYPES = {
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
}


class StorageError(Exception):
    """Base exception for storage errors."""


class UnsupportedFormatError(StorageError):
    """Raised when file format is not supported."""


class FileNotFoundError(StorageError):
    """Raised when file is not found."""


class FileTooLargeError(StorageError):
    """Raised when file exceeds size limit."""


class StorageService:
    """Service for managing file storage."""

    def __init__(self, upload_dir: str | None = None) -> None:
        """Initialize storage service.

        Args:
            upload_dir: Base directory for uploads. Defaults to settings.UPLOAD_DIR.
        """
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.songs_dir = self.upload_dir / "songs"
        self.covers_dir = self.upload_dir / "covers"
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    async def ensure_directories(self) -> None:
        """Ensure upload directories exist."""
        await aiofiles.os.makedirs(self.songs_dir, exist_ok=True)
        await aiofiles.os.makedirs(self.covers_dir, exist_ok=True)

    def get_format_from_content_type(self, content_type: str | None) -> str | None:
        """Get file format from content type.

        Args:
            content_type: MIME content type.

        Returns:
            File format extension or None if not supported.
        """
        if not content_type:
            return None
        return SUPPORTED_AUDIO_FORMATS.get(content_type.lower())

    def get_format_from_filename(self, filename: str) -> str | None:
        """Get file format from filename extension.

        Args:
            filename: Original filename.

        Returns:
            File format extension or None if not supported.
        """
        ext = Path(filename).suffix.lower()
        return EXTENSION_TO_FORMAT.get(ext)

    def get_mime_type(self, file_format: str) -> str:
        """Get MIME type for file format.

        Args:
            file_format: Audio file format.

        Returns:
            MIME type string.
        """
        return FORMAT_MIME_TYPES.get(file_format, "application/octet-stream")

    async def save_audio_file(
        self,
        file: IO[bytes],
        owner_id: uuid.UUID,
        filename: str,
        content_type: str | None = None,
    ) -> tuple[str, str, int]:
        """Save an audio file.

        Args:
            file: File-like object to save.
            owner_id: UUID of the file owner.
            filename: Original filename.
            content_type: MIME content type.

        Returns:
            Tuple of (file_path, file_format, file_size).

        Raises:
            UnsupportedFormatError: If file format is not supported.
            FileTooLargeError: If file exceeds size limit.
        """
        await self.ensure_directories()

        # Determine file format
        file_format = self.get_format_from_content_type(
            content_type
        ) or self.get_format_from_filename(filename)

        if not file_format:
            raise UnsupportedFormatError(
                "Unsupported audio format. Supported formats: mp3, flac, ogg, wav, m4a"
            )

        # Generate unique filename
        unique_id = uuid.uuid4()
        safe_filename = f"{owner_id}/{unique_id}.{file_format}"
        file_path = self.songs_dir / safe_filename

        # Ensure owner directory exists
        await aiofiles.os.makedirs(file_path.parent, exist_ok=True)

        # Read and save file
        content = file.read()
        file_size = len(content)

        if file_size > self.max_size_bytes:
            raise FileTooLargeError(
                f"File size {file_size} bytes exceeds limit of "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB"
            )

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return str(file_path), file_format, file_size

    async def save_cover_art(
        self,
        data: bytes,
        owner_id: uuid.UUID,
        image_format: str = "jpg",
    ) -> str:
        """Save cover art image.

        Args:
            data: Image data bytes.
            owner_id: UUID of the owner.
            image_format: Image format (jpg, png).

        Returns:
            Path to saved cover art.
        """
        await self.ensure_directories()

        unique_id = uuid.uuid4()
        safe_filename = f"{owner_id}/{unique_id}.{image_format}"
        file_path = self.covers_dir / safe_filename

        # Ensure owner directory exists
        await aiofiles.os.makedirs(file_path.parent, exist_ok=True)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)

        return str(file_path)

    async def delete_file(self, file_path: str) -> None:
        """Delete a file.

        Args:
            file_path: Path to file to delete.
        """
        try:
            path = Path(file_path)
            if await aiofiles.os.path.exists(path):
                await aiofiles.os.remove(path)
        except OSError:
            pass  # Ignore errors during deletion

    async def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes.

        Args:
            file_path: Path to file.

        Returns:
            File size in bytes.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        path = Path(file_path)
        if not await aiofiles.os.path.exists(path):
            raise FileNotFoundError(f"File not found: {file_path}")
        stat = await aiofiles.os.stat(path)
        return int(stat.st_size)

    async def read_file_range(
        self,
        file_path: str,
        start: int,
        end: int | None = None,
    ) -> bytes:
        """Read a range of bytes from a file.

        Args:
            file_path: Path to file.
            start: Start byte position.
            end: End byte position (exclusive). If None, read to end.

        Returns:
            File content bytes.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        path = Path(file_path)
        if not await aiofiles.os.path.exists(path):
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(path, "rb") as f:
            await f.seek(start)
            if end is None:
                return bytes(await f.read())
            return bytes(await f.read(end - start))

    async def read_file(self, file_path: str) -> bytes:
        """Read entire file content.

        Args:
            file_path: Path to file.

        Returns:
            File content bytes.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        path = Path(file_path)
        if not await aiofiles.os.path.exists(path):
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(path, "rb") as f:
            return bytes(await f.read())

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists (sync version for convenience).

        Args:
            file_path: Path to file.

        Returns:
            True if file exists.
        """
        return os.path.exists(file_path)
