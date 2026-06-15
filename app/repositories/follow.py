import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import Follow


class FollowRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def follow(self, follower_id: uuid.UUID, followed_id: uuid.UUID) -> Follow:
        follow = Follow(follower_id=follower_id, followed_id=followed_id)
        self.session.add(follow)
        await self.session.commit()
        return follow

    async def unfollow(self, follower_id: uuid.UUID, followed_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(Follow).where(
                Follow.follower_id == follower_id,
                Follow.followed_id == followed_id,
            )
        )
        await self.session.commit()

    async def is_following(self, follower_id: uuid.UUID, followed_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Follow).where(
                Follow.follower_id == follower_id,
                Follow.followed_id == followed_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_followers(self, user_id: uuid.UUID) -> list[Follow]:
        result = await self.session.execute(select(Follow).where(Follow.followed_id == user_id))
        return list(result.scalars().all())

    async def get_following(self, user_id: uuid.UUID) -> list[Follow]:
        result = await self.session.execute(select(Follow).where(Follow.follower_id == user_id))
        return list(result.scalars().all())

    async def get_following_ids(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self.session.execute(select(Follow.followed_id).where(Follow.follower_id == user_id))
        return [row[0] for row in result.all()]
