from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db_session
from app.models.user import UserCreate, UserLogin, UserResponse
from app.core.security import hash_password, verify_password
# 这里的 User 需要你在 models/user.py 里定义好 SQLAlchemy 模型，
# 但你的 models/user.py 目前是 Pydantic 模型。
# 为了快速跑通，我们这里用简单的逻辑演示，你需要确保数据库里有 User 表
# 建议：在 app/models/user.py 里补充 SQLAlchemy 定义 (见下文)

router = APIRouter()

# 这是一个模拟的内存数据库，为了不让你改动太大 models/crud
# 生产环境请务必替换为真实 DB 操作
fake_users_db = {} 

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate):
    if user_in.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = hash_password(user_in.password)
    user_id = len(fake_users_db) + 1
    
    user_data = {
        "user_id": user_id,
        "email": user_in.email,
        "phone_number": user_in.phone_number,
        "hashed_password": hashed_pw,
        "is_active": True
    }
    fake_users_db[user_in.email] = user_data
    return user_data

@router.post("/login")
async def login(user_in: UserLogin):
    user = fake_users_db.get(user_in.email)
    if not user or not verify_password(user_in.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    return {"message": "Login successful", "user_id": user["user_id"]}