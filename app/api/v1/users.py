import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    return await service.update_profile(
        user=current_user,
        username=body.username,
        bio=body.bio,
        avatar_url=body.avatar_url,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    service = UserService(session)
    return await service.get_profile(user_id)


@router.post("/{user_id}/follow", response_model=MessageResponse)
async def follow_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    return await service.follow_user(current_user, user_id)


@router.delete("/{user_id}/follow", response_model=MessageResponse)
async def unfollow_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    return await service.unfollow_user(current_user, user_id)


@router.get("/{user_id}/following", response_model=list[UserResponse])
async def get_following(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    service = UserService(session)
    return await service.get_following(user_id)


@router.get("/{user_id}/followers", response_model=list[UserResponse])
async def get_followers(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    service = UserService(session)
    return await service.get_followers(user_id)
