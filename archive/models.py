from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Source(BaseModel):
    platform: str
    id: str
    url: str


class Media(BaseModel):
    type: Literal["image", "video", "gif"]
    url: str
    original_url: str | None = None
    alt: str | None = None


class Post(BaseModel):
    id: str
    published_at: datetime
    updated_at: datetime

    text: str
    html: str

    sources: list[Source]
    media: list[Media] = []
    tags: list[str] = []
