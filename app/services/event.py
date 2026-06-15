import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.event import EventRepository
from app.schemas.event import EventResponse, EventDetailResponse, EventParticipantResponse
from app.redis_client import cache_get, cache_set, cache_delete_pattern


class EventService:
    def __init__(self, session: AsyncSession):
        self.repo = EventRepository(session)

    async def create(
        self, title: str, description: str, date: datetime, location: str, organizer: User
    ) -> EventResponse:
        if date <= datetime.now(date.tzinfo):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event date must be in the future")
        event = await self.repo.create(
            title=title,
            description=description,
            date=date,
            location=location,
            organizer_id=organizer.id,
        )
        await cache_delete_pattern("events:list:*")
        result = EventResponse.model_validate(event)
        result.participant_count = 0
        return result

    async def get_all(self, page: int = 1, page_size: int = 20) -> tuple[list[EventResponse], int]:
        cache_key = f"events:list:{page}:{page_size}"
        cached = await cache_get(cache_key)
        if cached:
            events_data = cached["items"]
            total = cached["total"]
            events = [EventResponse(**e) for e in events_data]
            return events, total

        events, total = await self.repo.get_all(page=page, page_size=page_size)
        result = []
        for e in events:
            er = EventResponse.model_validate(e)
            er.participant_count = await self.repo.count_participants(e.id)
            result.append(er)

        await cache_set(cache_key, {"items": [r.model_dump(mode="json") for r in result], "total": total}, ttl=300)
        return result, total

    async def get_by_id(self, event_id: uuid.UUID) -> EventDetailResponse:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        participants = await self.repo.get_participants(event_id)
        participant_count = await self.repo.count_participants(event_id)
        base = EventResponse.model_validate(event)
        result = EventDetailResponse(
            **base.model_dump(exclude={"participant_count"}),
            participant_count=participant_count,
            participants=[EventParticipantResponse.model_validate(p) for p in participants],
        )
        return result

    async def update(self, event_id: uuid.UUID, user: User, **kwargs) -> EventResponse:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        if event.organizer_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only the organizer can update this event"
            )

        if kwargs.get("date") and kwargs["date"] <= datetime.now(kwargs["date"].tzinfo):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event date must be in the future")

        updated = await self.repo.update(event, **kwargs)
        await cache_delete_pattern("events:list:*")
        result = EventResponse.model_validate(updated)
        result.participant_count = await self.repo.count_participants(updated.id)
        return result

    async def delete(self, event_id: uuid.UUID, user: User) -> dict:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        if event.organizer_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only the organizer can delete this event"
            )
        await self.repo.delete(event)
        await cache_delete_pattern("events:list:*")
        return {"message": "Event deleted"}

    async def join(self, event_id: uuid.UUID, user: User) -> dict:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        if event.organizer_id == user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are the organizer of this event")
        existing = await self.repo.get_participant(event_id, user.id)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already joined this event")
        await self.repo.add_participant(event_id, user.id)
        await cache_delete_pattern("events:list:*")
        return {"message": "Joined event successfully"}

    async def leave(self, event_id: uuid.UUID, user: User) -> dict:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        existing = await self.repo.get_participant(event_id, user.id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not a participant of this event")
        await self.repo.remove_participant(event_id, user.id)
        await cache_delete_pattern("events:list:*")
        return {"message": "Left event successfully"}
