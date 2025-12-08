from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any

class DiagnosisHistoryBase(BaseModel):
    """基础的历史记录模型"""
    user_id: int
    session_id: str
    possible_causes: list[dict]
    risk_level: str
    advice: str
    # --- 新增 ---
    dialogue_history: List[Dict[str, Any]] = [] 
    created_at: datetime

class DiagnosisHistoryResponse(DiagnosisHistoryBase):
    """用于 API 响应的模型"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)