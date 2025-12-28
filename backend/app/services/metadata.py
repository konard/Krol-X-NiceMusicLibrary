"""Metadata extraction service using mutagen."""

from dataclasses import dataclass
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis


@dataclass
class AudioMetadata:
    """Extracted audio metadata."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    genre: str | None = None
    year: int | None = None
    track_number: int | None = None
    disc_number: int | None = None
    duration_seconds: int = 0
    bitrate: int | None = None
    sample_rate: int | None = None
    cover_art: bytes | None = None
    cover_art_mime: str | None = None
    lyrics: str | None = None
    bpm: int | None = None


class MetadataExtractorError(Exception):
    """Base exception for metadata extraction errors."""


class MetadataExtractor:
    """Service for extracting metadata from audio files."""

    def extract(self, file_path: str) -> AudioMetadata:
        """Extract metadata from an audio file.

        Args:
            file_path: Path to audio file.

        Returns:
            Extracted metadata.

        Raises:
            MetadataExtractorError: If extraction fails.
        """
        try:
            audio = MutagenFile(file_path, easy=False)
            if audio is None:
                raise MetadataExtractorError(f"Cannot read audio file: {file_path}")

            # Determine file type and extract accordingly
            path = Path(file_path)
            ext = path.suffix.lower()

            if ext == ".mp3":
                return self._extract_mp3(file_path)
            elif ext == ".flac":
                return self._extract_flac(file_path)
            elif ext == ".ogg":
                return self._extract_ogg(file_path)
            elif ext in (".m4a", ".aac", ".mp4"):
                return self._extract_m4a(file_path)
            elif ext == ".wav":
                return self._extract_wav(file_path)
            else:
                # Generic extraction for unknown formats
                return self._extract_generic(audio)

        except Exception as e:
            if isinstance(e, MetadataExtractorError):
                raise
            raise MetadataExtractorError(f"Failed to extract metadata: {e}") from e

    def _extract_mp3(self, file_path: str) -> AudioMetadata:
        """Extract metadata from MP3 file."""
        audio = MP3(file_path)
        metadata = AudioMetadata()

        # Get audio properties
        if audio.info:
            metadata.duration_seconds = int(audio.info.length)
            metadata.bitrate = (
                audio.info.bitrate // 1000 if audio.info.bitrate else None
            )
            metadata.sample_rate = audio.info.sample_rate

        # Get ID3 tags
        if audio.tags:
            tags = audio.tags

            # Title
            if "TIT2" in tags:
                metadata.title = str(tags["TIT2"])

            # Artist
            if "TPE1" in tags:
                metadata.artist = str(tags["TPE1"])

            # Album
            if "TALB" in tags:
                metadata.album = str(tags["TALB"])

            # Album artist
            if "TPE2" in tags:
                metadata.album_artist = str(tags["TPE2"])

            # Genre
            if "TCON" in tags:
                metadata.genre = str(tags["TCON"])

            # Year
            if "TDRC" in tags:
                try:
                    metadata.year = int(str(tags["TDRC"])[:4])
                except (ValueError, TypeError):
                    pass
            elif "TYER" in tags:
                try:
                    metadata.year = int(str(tags["TYER"]))
                except (ValueError, TypeError):
                    pass

            # Track number
            if "TRCK" in tags:
                try:
                    track_str = str(tags["TRCK"]).split("/")[0]
                    metadata.track_number = int(track_str)
                except (ValueError, TypeError):
                    pass

            # Disc number
            if "TPOS" in tags:
                try:
                    disc_str = str(tags["TPOS"]).split("/")[0]
                    metadata.disc_number = int(disc_str)
                except (ValueError, TypeError):
                    pass

            # Lyrics
            for key in tags:
                if key.startswith("USLT"):
                    metadata.lyrics = str(tags[key])
                    break

            # BPM
            if "TBPM" in tags:
                try:
                    metadata.bpm = int(float(str(tags["TBPM"])))
                except (ValueError, TypeError):
                    pass

            # Cover art (APIC frame)
            for key in tags:
                if key.startswith("APIC"):
                    apic = tags[key]
                    metadata.cover_art = apic.data
                    metadata.cover_art_mime = apic.mime
                    break

        return metadata

    def _extract_flac(self, file_path: str) -> AudioMetadata:
        """Extract metadata from FLAC file."""
        audio = FLAC(file_path)
        metadata = AudioMetadata()

        # Get audio properties
        if audio.info:
            metadata.duration_seconds = int(audio.info.length)
            metadata.bitrate = (
                audio.info.bitrate // 1000
                if hasattr(audio.info, "bitrate") and audio.info.bitrate
                else None
            )
            metadata.sample_rate = audio.info.sample_rate

        # Get Vorbis comments
        if audio.tags:
            metadata.title = self._get_first(audio.tags, "title")
            metadata.artist = self._get_first(audio.tags, "artist")
            metadata.album = self._get_first(audio.tags, "album")
            metadata.album_artist = self._get_first(audio.tags, "albumartist")
            metadata.genre = self._get_first(audio.tags, "genre")
            metadata.lyrics = self._get_first(audio.tags, "lyrics")

            # Year
            date_str = self._get_first(audio.tags, "date")
            if date_str:
                try:
                    metadata.year = int(date_str[:4])
                except (ValueError, TypeError):
                    pass

            # Track number
            track_str = self._get_first(audio.tags, "tracknumber")
            if track_str:
                try:
                    metadata.track_number = int(track_str.split("/")[0])
                except (ValueError, TypeError):
                    pass

            # Disc number
            disc_str = self._get_first(audio.tags, "discnumber")
            if disc_str:
                try:
                    metadata.disc_number = int(disc_str.split("/")[0])
                except (ValueError, TypeError):
                    pass

            # BPM
            bpm_str = self._get_first(audio.tags, "bpm")
            if bpm_str:
                try:
                    metadata.bpm = int(float(bpm_str))
                except (ValueError, TypeError):
                    pass

        # Cover art
        if audio.pictures:
            for picture in audio.pictures:
                metadata.cover_art = picture.data
                metadata.cover_art_mime = picture.mime
                break

        return metadata

    def _extract_ogg(self, file_path: str) -> AudioMetadata:
        """Extract metadata from OGG Vorbis file."""
        audio = OggVorbis(file_path)
        metadata = AudioMetadata()

        # Get audio properties
        if audio.info:
            metadata.duration_seconds = int(audio.info.length)
            metadata.bitrate = (
                audio.info.bitrate // 1000 if audio.info.bitrate else None
            )
            metadata.sample_rate = audio.info.sample_rate

        # Get Vorbis comments (same as FLAC)
        if audio.tags:
            metadata.title = self._get_first(audio.tags, "title")
            metadata.artist = self._get_first(audio.tags, "artist")
            metadata.album = self._get_first(audio.tags, "album")
            metadata.album_artist = self._get_first(audio.tags, "albumartist")
            metadata.genre = self._get_first(audio.tags, "genre")
            metadata.lyrics = self._get_first(audio.tags, "lyrics")

            # Year
            date_str = self._get_first(audio.tags, "date")
            if date_str:
                try:
                    metadata.year = int(date_str[:4])
                except (ValueError, TypeError):
                    pass

            # Track number
            track_str = self._get_first(audio.tags, "tracknumber")
            if track_str:
                try:
                    metadata.track_number = int(track_str.split("/")[0])
                except (ValueError, TypeError):
                    pass

            # Disc number
            disc_str = self._get_first(audio.tags, "discnumber")
            if disc_str:
                try:
                    metadata.disc_number = int(disc_str.split("/")[0])
                except (ValueError, TypeError):
                    pass

            # BPM
            bpm_str = self._get_first(audio.tags, "bpm")
            if bpm_str:
                try:
                    metadata.bpm = int(float(bpm_str))
                except (ValueError, TypeError):
                    pass

        return metadata

    def _extract_m4a(self, file_path: str) -> AudioMetadata:
        """Extract metadata from M4A/AAC file."""
        audio = MP4(file_path)
        metadata = AudioMetadata()

        # Get audio properties
        if audio.info:
            metadata.duration_seconds = int(audio.info.length)
            metadata.bitrate = (
                audio.info.bitrate // 1000 if audio.info.bitrate else None
            )
            metadata.sample_rate = audio.info.sample_rate

        # Get MP4 tags
        if audio.tags:
            tags = audio.tags

            # Title
            if "\xa9nam" in tags:
                metadata.title = tags["\xa9nam"][0]

            # Artist
            if "\xa9ART" in tags:
                metadata.artist = tags["\xa9ART"][0]

            # Album
            if "\xa9alb" in tags:
                metadata.album = tags["\xa9alb"][0]

            # Album artist
            if "aART" in tags:
                metadata.album_artist = tags["aART"][0]

            # Genre
            if "\xa9gen" in tags:
                metadata.genre = tags["\xa9gen"][0]

            # Year
            if "\xa9day" in tags:
                try:
                    metadata.year = int(str(tags["\xa9day"][0])[:4])
                except (ValueError, TypeError):
                    pass

            # Track number
            if "trkn" in tags and tags["trkn"]:
                try:
                    metadata.track_number = tags["trkn"][0][0]
                except (IndexError, TypeError):
                    pass

            # Disc number
            if "disk" in tags and tags["disk"]:
                try:
                    metadata.disc_number = tags["disk"][0][0]
                except (IndexError, TypeError):
                    pass

            # Lyrics
            if "\xa9lyr" in tags:
                metadata.lyrics = tags["\xa9lyr"][0]

            # BPM
            if "tmpo" in tags and tags["tmpo"]:
                try:
                    metadata.bpm = tags["tmpo"][0]
                except (IndexError, TypeError):
                    pass

            # Cover art
            if "covr" in tags and tags["covr"]:
                cover = tags["covr"][0]
                metadata.cover_art = bytes(cover)
                # MP4 cover format
                if hasattr(cover, "imageformat"):
                    if cover.imageformat == 13:  # JPEG
                        metadata.cover_art_mime = "image/jpeg"
                    elif cover.imageformat == 14:  # PNG
                        metadata.cover_art_mime = "image/png"
                else:
                    metadata.cover_art_mime = "image/jpeg"

        return metadata

    def _extract_wav(self, file_path: str) -> AudioMetadata:
        """Extract metadata from WAV file."""
        audio = MutagenFile(file_path)
        metadata = AudioMetadata()

        # WAV files usually don't have tags, but we can get audio info
        if audio and audio.info:
            metadata.duration_seconds = int(audio.info.length)
            metadata.sample_rate = (
                audio.info.sample_rate if hasattr(audio.info, "sample_rate") else None
            )
            # Calculate bitrate for WAV (typically uncompressed)
            if hasattr(audio.info, "bits_per_sample") and hasattr(
                audio.info, "channels"
            ):
                bps = (
                    audio.info.bits_per_sample
                    * audio.info.sample_rate
                    * audio.info.channels
                )
                metadata.bitrate = bps // 1000

        # Try to get any available tags
        if audio and audio.tags:
            for key in audio.tags:
                key_lower = key.lower()
                if "title" in key_lower and not metadata.title:
                    metadata.title = str(audio.tags[key])
                elif "artist" in key_lower and not metadata.artist:
                    metadata.artist = str(audio.tags[key])
                elif "album" in key_lower and not metadata.album:
                    metadata.album = str(audio.tags[key])

        return metadata

    def _extract_generic(self, audio: MutagenFile) -> AudioMetadata:
        """Generic metadata extraction for unknown formats."""
        metadata = AudioMetadata()

        if audio.info:
            metadata.duration_seconds = int(audio.info.length)
            if hasattr(audio.info, "bitrate") and audio.info.bitrate:
                metadata.bitrate = audio.info.bitrate // 1000
            if hasattr(audio.info, "sample_rate"):
                metadata.sample_rate = audio.info.sample_rate

        return metadata

    def _get_first(self, tags: dict, key: str) -> str | None:
        """Get first value from a tag list.

        Args:
            tags: Tag dictionary.
            key: Tag key.

        Returns:
            First value or None.
        """
        values = tags.get(key)
        if values and isinstance(values, list):
            return str(values[0])
        return None
