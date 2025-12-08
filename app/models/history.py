from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from app.core.database import Base

class DiagnosisHistory(Base):
    """
    诊断历史记录的 ORM 模型
    """
    __tablename__ = "diagnosis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    
    # 存储 JSON 格式的诊断结果
    possible_causes = Column(JSON, nullable=False)
    risk_level = Column(String, nullable=False)
    advice = Column(String, nullable=False)
    
    # --- 新增：存储完整的对话历史 ---
    dialogue_history = Column(JSON, nullable=False, default=[]) 

    created_at = Column(DateTime, server_default=func.now())