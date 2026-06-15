import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.follow import FollowRepository
from app.schemas.user import UserResponse


class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)
        self.follow_repo = FollowRepository(session)

    async def get_profile(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)

    async def update_profile(
        self, user: User, username: str | None, bio: str | None, avatar_url: str | None
    ) -> UserResponse:
        if username and username != user.username:
            existing = await self.repo.get_by_username(username)
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
        updated = await self.repo.update(user, username=username, bio=bio, avatar_url=avatar_url)
        return UserResponse.model_validate(updated)

    async def follow_user(self, follower: User, followed_id: uuid.UUID) -> dict:
        if follower.id == followed_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")
        target = await self.repo.get_by_id(followed_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if await self.follow_repo.is_following(follower.id, followed_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already following this user")
        await self.follow_repo.follow(follower.id, followed_id)
        return {"message": f"Now following {target.username}"}

    async def unfollow_user(self, follower: User, followed_id: uuid.UUID) -> dict:
        if follower.id == followed_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot unfollow yourself")
        target = await self.repo.get_by_id(followed_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not await self.follow_repo.is_following(follower.id, followed_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not following this user")
        await self.follow_repo.unfollow(follower.id, followed_id)
        return {"message": f"Unfollowed {target.username}"}

    async def get_following(self, user_id: uuid.UUID) -> list[UserResponse]:
        follows = await self.follow_repo.get_following(user_id)
        users = []
        for f in follows:
            u = await self.repo.get_by_id(f.followed_id)
            if u:
                users.append(UserResponse.model_validate(u))
        return users

    async def get_followers(self, user_id: uuid.UUID) -> list[UserResponse]:
        follows = await self.follow_repo.get_followers(user_id)
        users = []
        for f in follows:
            u = await self.repo.get_by_id(f.follower_id)
            if u:
                users.append(UserResponse.model_validate(u))
        return users
