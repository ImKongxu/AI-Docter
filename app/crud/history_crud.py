from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.history import DiagnosisHistory
from app.models.diagnosis import DiagnosisResult
from typing import List, Dict, Any

async def create_diagnosis_history(
    db: AsyncSession, 
    user_id: int, 
    session_id: str, 
    result: DiagnosisResult,
    history: List[Dict[str, Any]] # --- 新增参数 ---
) -> DiagnosisHistory:
    """
    创建一个新的诊断历史记录并存入数据库。
    """
    db_history = DiagnosisHistory(
        user_id=user_id,
        session_id=session_id,
        possible_causes=result.model_dump()["possible_causes"],
        risk_level=result.risk_level,
        advice=result.advice,
        dialogue_history=history # --- 保存历史 ---
    )
    db.add(db_history)
    await db.commit()
    await db.refresh(db_history)
    return db_history

async def get_history_by_user(db: AsyncSession, user_id: int) -> List[DiagnosisHistory]:
    """
    根据用户ID查询其所有诊断历史记录。
    """
    query = select(DiagnosisHistory).where(DiagnosisHistory.user_id == user_id).order_by(DiagnosisHistory.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()