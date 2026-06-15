import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostDetailResponse
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.post import PostService
from app.services.comment import CommentService

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("", response_model=PostResponse, status_code=201)
async def create_post(
    body: PostCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    return await service.create(
        title=body.title,
        content=body.content,
        author=current_user,
        event_id=body.event_id,
    )


@router.get("", response_model=dict)
async def list_posts(
    event_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    posts, total = await service.get_all(event_id=event_id, page=page, page_size=page_size)
    return {
        "items": posts,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": -(-total // page_size) if total > 0 else 0,
    }


@router.get("/feed", response_model=dict)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from app.services.feed import FeedService

    service = FeedService(session)
    posts, total = await service.get_feed(current_user.id, page=page, page_size=page_size)
    return {
        "items": posts,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": -(-total // page_size) if total > 0 else 0,
    }


@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post(post_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    service = PostService(session)
    post = await service.get_by_id(post_id)
    comment_service = CommentService(session)
    post.comments = await comment_service.get_by_post(post_id)
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: uuid.UUID,
    body: PostUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    return await service.update(post_id, current_user, title=body.title, content=body.content)


@router.delete("/{post_id}", response_model=MessageResponse)
async def delete_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PostService(session)
    return await service.delete(post_id, current_user)


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: uuid.UUID,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = CommentService(session)
    return await service.create(content=body.content, author=current_user, post_id=post_id)


@router.get("/{post_id}/comments", response_model=list[CommentResponse])
async def list_comments(post_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    service = CommentService(session)
    return await service.get_by_post(post_id)
