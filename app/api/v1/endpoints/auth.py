from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.core.database import get_db_session
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.crud.user_crud import get_user_by_email, create_user
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    # 1. 检查邮箱是否已存在
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="该邮箱已被注册"
        )
    
    # 2. 创建新用户
    new_user = await create_user(db, user_in)
    return new_user

@router.post("/login", response_model=Token)
async def login(
    # 使用 OAuth2 标准表单 (username, password)
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    # 1. 验证用户
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. 生成 Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, # 将用户ID放入 Token
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}