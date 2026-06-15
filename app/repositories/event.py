import uuid
from datetime import datetime

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventParticipant


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, title: str, description: str, date: datetime, location: str, organizer_id: uuid.UUID
    ) -> Event:
        event = Event(
            title=title,
            description=description,
            date=date,
            location=location,
            organizer_id=organizer_id,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> Event | None:
        return await self.session.get(Event, event_id)

    async def get_all(self, page: int = 1, page_size: int = 20) -> tuple[list[Event], int]:
        total_q = select(func.count(Event.id))
        total_result = await self.session.execute(total_q)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        q = select(Event).order_by(Event.date.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(q)
        events = list(result.scalars().all())
        return events, total

    async def update(self, event: Event, **kwargs) -> Event:
        for key, value in kwargs.items():
            if value is not None:
                setattr(event, key, value)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def delete(self, event: Event) -> None:
        await self.session.delete(event)
        await self.session.commit()

    async def get_participant(self, event_id: uuid.UUID, user_id: uuid.UUID) -> EventParticipant | None:
        result = await self.session.execute(
            select(EventParticipant).where(
                EventParticipant.event_id == event_id,
                EventParticipant.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_participant(self, event_id: uuid.UUID, user_id: uuid.UUID) -> EventParticipant:
        participant = EventParticipant(event_id=event_id, user_id=user_id)
        self.session.add(participant)
        await self.session.commit()
        return participant

    async def remove_participant(self, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(EventParticipant).where(
                EventParticipant.event_id == event_id,
                EventParticipant.user_id == user_id,
            )
        )
        await self.session.commit()

    async def get_participants(self, event_id: uuid.UUID) -> list[EventParticipant]:
        result = await self.session.execute(select(EventParticipant).where(EventParticipant.event_id == event_id))
        return list(result.scalars().all())

    async def count_participants(self, event_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count(EventParticipant.user_id)).where(EventParticipant.event_id == event_id)
        )
        return result.scalar()
