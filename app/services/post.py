import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.post import PostRepository
from app.repositories.event import EventRepository
from app.schemas.post import PostResponse, PostDetailResponse
from app.schemas.comment import CommentResponse
from app.schemas.user import UserBrief


class PostService:
    def __init__(self, session: AsyncSession):
        self.repo = PostRepository(session)
        self.event_repo = EventRepository(session)

    async def _build_post_response(self, post) -> PostResponse:
        author = await self.repo.get_author(post.author_id)
        comment_count = await self.repo.count_comments(post.id)
        result = PostResponse.model_validate(post)
        result.author = UserBrief.model_validate(author)
        result.comment_count = comment_count
        return result

    async def create(self, title: str, content: str, author: User, event_id: uuid.UUID | None = None) -> PostResponse:
        if event_id:
            event = await self.event_repo.get_by_id(event_id)
            if not event:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        post = await self.repo.create(title=title, content=content, author_id=author.id, event_id=event_id)
        return await self._build_post_response(post)

    async def get_all(
        self, event_id: uuid.UUID | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[PostResponse], int]:
        posts, total = await self.repo.get_all(event_id=event_id, page=page, page_size=page_size)
        result = [await self._build_post_response(p) for p in posts]
        return result, total

    async def get_by_id(self, post_id: uuid.UUID) -> PostDetailResponse:
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        author = await self.repo.get_author(post.author_id)
        comment_count = await self.repo.count_comments(post.id)
        result = PostDetailResponse.model_validate(post)
        result.author = UserBrief.model_validate(author)
        result.comment_count = comment_count
        result.comments = []
        return result

    async def update(self, post_id: uuid.UUID, user: User, **kwargs) -> PostResponse:
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can update this post")
        updated = await self.repo.update(post, **kwargs)
        return await self._build_post_response(updated)

    async def delete(self, post_id: uuid.UUID, user: User) -> dict:
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can delete this post")
        await self.repo.delete(post)
        return {"message": "Post deleted"}
