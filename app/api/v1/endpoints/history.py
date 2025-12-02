from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
# 导入依赖和用户模型
from app.api.deps import get_current_user 
from app.models.user import User

from app.core.database import get_db_session
from app.crud.history_crud import get_history_by_user
from app.schemas.history import DiagnosisHistoryResponse

router = APIRouter()

# 路由改为 /history/me 或 /history，并移除 user_id 参数
@router.get("/history", response_model=List[DiagnosisHistoryResponse])
async def read_user_history(
    # 注入当前用户对象
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取当前登录用户的完整诊断历史记录列表。
    """
    # 使用当前用户的 ID 查询历史记录
    history_records = await get_history_by_user(db=db, user_id=current_user.id)
    return history_records