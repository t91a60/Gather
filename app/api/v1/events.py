from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.event import EventCreate, EventUpdate, EventResponse, EventDetailResponse
from app.services.event import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    body: EventCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = EventService(session)
    return await service.create(
        title=body.title,
        description=body.description or "",
        date=body.date,
        location=body.location,
        organizer=current_user,
    )


@router.get("", response_model=dict)
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = EventService(session)
    events, total = await service.get_all(page=page, page_size=page_size)
    return {
        "items": events,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": -(-total // page_size) if total > 0 else 0,
    }


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(event_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    service = EventService(session)
    return await service.get_by_id(event_id)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: uuid.UUID,
    body: EventUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = EventService(session)
    return await service.update(
        event_id,
        current_user,
        title=body.title,
        description=body.description,
        date=body.date,
        location=body.location,
    )


@router.delete("/{event_id}", response_model=MessageResponse)
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = EventService(session)
    return await service.delete(event_id, current_user)


@router.post("/{event_id}/join", response_model=MessageResponse)
async def join_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = EventService(session)
    return await service.join(event_id, current_user)


@router.delete("/{event_id}/leave", response_model=MessageResponse)
async def leave_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = EventService(session)
    return await service.leave(event_id, current_user)
