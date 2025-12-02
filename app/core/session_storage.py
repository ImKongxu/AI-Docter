from app.models.diagnosis import ConsultationResponse
# 导入内存字典，用于存储会话状态
from app.core.session import session_store
import json

# 由于切换到内存字典，这个常量不再需要但保留在这里
# SESSION_EXPIRATION_SECONDS = 60 * 60 * 24 

async def save_session(session_id: str, data: ConsultationResponse):
    """
    将问诊会话数据存入内存字典 (替代 Redis)。
    """
    # 直接存储 Pydantic 对象
    session_store[session_id] = data

async def load_session(session_id: str) -> ConsultationResponse | None:
    """
    从内存字典读取会话数据。
    """
    # 从字典中获取数据
    return session_store.get(session_id)

async def session_exists(session_id: str) -> bool:
    """
    检查会话是否存在于内存字典中。
    """
    return session_id in session_store