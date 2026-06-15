import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.comment import CommentResponse
from app.schemas.user import UserBrief


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    event_id: uuid.UUID | None = None


class PostUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = Field(None, min_length=1, max_length=10000)


class PostResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    author: UserBrief
    event_id: uuid.UUID | None
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostDetailResponse(PostResponse):
    comments: list[CommentResponse] = []
