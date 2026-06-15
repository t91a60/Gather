import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, content: str, author_id: uuid.UUID, post_id: uuid.UUID) -> Comment:
        comment = Comment(content=content, author_id=author_id, post_id=post_id)
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        return await self.session.get(Comment, comment_id)

    async def get_by_post(self, post_id: uuid.UUID) -> list[Comment]:
        result = await self.session.execute(
            select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_post(self, post_id: uuid.UUID) -> Post | None:
        return await self.session.get(Post, post_id)

    async def get_author(self, author_id: uuid.UUID) -> User | None:
        return await self.session.get(User, author_id)

    async def delete(self, comment: Comment) -> None:
        await self.session.delete(comment)
        await self.session.commit()
