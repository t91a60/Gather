import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserBrief


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: uuid.UUID
    content: str
    author: UserBrief
    post_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
