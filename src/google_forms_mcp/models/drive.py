"""Data models for Google Drive entities."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ShareRole(str, Enum):
    """Permission roles for shared files."""

    READER = "reader"
    COMMENTER = "commenter"
    WRITER = "writer"
    ORGANIZER = "organizer"
    OWNER = "owner"


class ShareType(str, Enum):
    """Permission types for shared files."""

    USER = "user"
    GROUP = "group"
    DOMAIN = "domain"
    ANYONE = "anyone"


class DriveFile(BaseModel):
    """Representation of a Google Drive file."""

    file_id: str = ""
    name: str = ""
    mime_type: str = ""
    created_time: datetime | None = None
    modified_time: datetime | None = None
    size: int | None = None
    parents: list[str] = Field(default_factory=list)
    web_view_link: str = ""
    trashed: bool = False
    owners: list[str] = Field(default_factory=list)


class DrivePermission(BaseModel):
    """A sharing permission on a Drive file."""

    permission_id: str = ""
    role: ShareRole = ShareRole.READER
    type: ShareType = ShareType.USER
    email_address: str = ""
    display_name: str = ""
    domain: str = ""


class DriveFolder(BaseModel):
    """Representation of a Google Drive folder."""

    folder_id: str = ""
    name: str = ""
    parent_id: str = ""
    web_view_link: str = ""
