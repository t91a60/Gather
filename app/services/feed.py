import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.post import PostRepository
from app.repositories.follow import FollowRepository
from app.services.post import PostService
from app.schemas.post import PostResponse


class FeedService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.post_repo = PostRepository(session)
        self.follow_repo = FollowRepository(session)
        self.post_service = PostService(session)

    async def get_feed(self, user_id: uuid.UUID, page: int = 1, page_size: int = 20) -> tuple[list[PostResponse], int]:
        following_ids = await self.follow_repo.get_following_ids(user_id)
        posts, total = await self.post_repo.get_feed(following_ids, page=page, page_size=page_size)
        result = [await self.post_service._build_post_response(p) for p in posts]
        return result, total
