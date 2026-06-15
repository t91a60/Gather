import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.comment import CommentRepository
from app.schemas.comment import CommentResponse
from app.schemas.user import UserBrief


class CommentService:
    def __init__(self, session: AsyncSession):
        self.repo = CommentRepository(session)

    async def _build_response(self, comment) -> CommentResponse:
        author = await self.repo.get_author(comment.author_id)
        result = CommentResponse.model_validate(comment)
        result.author = UserBrief.model_validate(author)
        return result

    async def create(self, content: str, author: User, post_id: uuid.UUID) -> CommentResponse:
        post = await self.repo.get_post(post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        comment = await self.repo.create(content=content, author_id=author.id, post_id=post_id)
        return await self._build_response(comment)

    async def get_by_post(self, post_id: uuid.UUID) -> list[CommentResponse]:
        post = await self.repo.get_post(post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        comments = await self.repo.get_by_post(post_id)
        result = []
        for c in comments:
            result.append(await self._build_response(c))
        return result

    async def delete(self, comment_id: uuid.UUID, user: User) -> dict:
        comment = await self.repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if comment.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can delete this comment")
        await self.repo.delete(comment)
        return {"message": "Comment deleted"}
