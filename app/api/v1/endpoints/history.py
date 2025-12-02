from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db_session
from app.crud.history_crud import get_history_by_user
from app.schemas.history import DiagnosisHistoryResponse

router = APIRouter()

@router.get("/history/{user_id}", response_model=List[DiagnosisHistoryResponse])
async def read_user_history(
    user_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    根据用户ID获取其完整的诊断历史记录列表。
    """
    history_records = await get_history_by_user(db=db, user_id=user_id)
    return history_records
