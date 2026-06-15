from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.auth import TokenResponse, RefreshRequest
from app.schemas.user import UserCreate, UserLogin
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserCreate, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    return await service.register(
        username=body.username,
        email=body.email,
        password=body.password,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    return await service.login(email=body.email, password=body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    return await service.refresh(refresh_token=body.refresh_token)
