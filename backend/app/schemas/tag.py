"""Tag schemas for request/response validation."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagBase(BaseModel):
    """Base tag schema with common fields."""

    name: str = Field(max_length=100)
    color: str | None = Field(default=None, max_length=7)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """Validate color is a valid hex color."""
        if v is None:
            return v
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            msg = "Color must be a valid hex color (e.g., #FF5733)"
            raise ValueError(msg)
        return v.upper()


class TagCreate(TagBase):
    """Schema for creating a tag."""

    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag."""

    name: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=7)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """Validate color is a valid hex color."""
        if v is None:
            return v
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            msg = "Color must be a valid hex color (e.g., #FF5733)"
            raise ValueError(msg)
        return v.upper()


class TagResponse(BaseModel):
    """Schema for tag response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: str | None
    created_at: datetime


class TagListResponse(BaseModel):
    """Schema for tag list response."""

    items: list[TagResponse]


class SongTagRequest(BaseModel):
    """Schema for adding a tag to a song."""

    tag_id: UUID


class SongWithTagsResponse(BaseModel):
    """Schema for song response with tags."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    artist: str | None
    album: str | None
    tags: list[TagResponse] = []
