from pydantic import BaseModel, ConfigDict
from datetime import datetime

class DiagnosisHistoryBase(BaseModel):
    """基础的历史记录模型"""
    user_id: int
    session_id: str
    possible_causes: list[dict]
    risk_level: str
    advice: str
    created_at: datetime

class DiagnosisHistoryResponse(DiagnosisHistoryBase):
    """用于 API 响应的模型"""
    id: int
    
    # Pydantic v2 写法, orm_mode=True 的替代品
    # 允许模型从 ORM 对象 (如 SQLAlchemy 模型) 中读取数据
    model_config = ConfigDict(from_attributes=True)
