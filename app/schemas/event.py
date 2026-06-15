import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    date: datetime
    location: str = Field(..., min_length=1, max_length=300)


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    date: datetime | None = None
    location: str | None = Field(None, min_length=1, max_length=300)


class EventParticipantResponse(BaseModel):
    user_id: uuid.UUID
    joined_at: datetime

    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    date: datetime
    location: str
    organizer_id: uuid.UUID
    participant_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventDetailResponse(EventResponse):
    participants: list[EventParticipantResponse] = []
