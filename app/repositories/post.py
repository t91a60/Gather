import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.comment import Comment
from app.models.user import User


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, title: str, content: str, author_id: uuid.UUID, event_id: uuid.UUID | None = None) -> Post:
        post = Post(title=title, content=content, author_id=author_id, event_id=event_id)
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_by_id(self, post_id: uuid.UUID) -> Post | None:
        return await self.session.get(Post, post_id)

    async def get_all(
        self, event_id: uuid.UUID | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[Post], int]:
        conditions = []
        if event_id:
            conditions.append(Post.event_id == event_id)

        total_q = select(func.count(Post.id))
        total_q = total_q.where(*conditions) if conditions else total_q
        total_result = await self.session.execute(total_q)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        q = select(Post).where(*conditions).order_by(Post.created_at.desc()).offset(offset).limit(page_size)
        result = await self.session.execute(q)
        posts = list(result.scalars().all())
        return posts, total

    async def get_feed(self, user_ids: list[uuid.UUID], page: int = 1, page_size: int = 20) -> tuple[list[Post], int]:
        if not user_ids:
            return [], 0

        total_q = select(func.count(Post.id)).where(Post.author_id.in_(user_ids))
        total_result = await self.session.execute(total_q)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        q = (
            select(Post)
            .where(Post.author_id.in_(user_ids))
            .order_by(Post.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(q)
        posts = list(result.scalars().all())
        return posts, total

    async def update(self, post: Post, **kwargs) -> Post:
        for key, value in kwargs.items():
            if value is not None:
                setattr(post, key, value)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
        await self.session.commit()

    async def count_comments(self, post_id: uuid.UUID) -> int:
        result = await self.session.execute(select(func.count(Comment.id)).where(Comment.post_id == post_id))
        return result.scalar()

    async def get_author(self, author_id: uuid.UUID) -> User | None:
        return await self.session.get(User, author_id)
