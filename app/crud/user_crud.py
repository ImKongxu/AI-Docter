from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password

async def get_user_by_email(db: AsyncSession, email: str):
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: int):
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hash_password(user.password),
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user