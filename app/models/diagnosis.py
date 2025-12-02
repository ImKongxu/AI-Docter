from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SymptomInput(BaseModel):
    """问诊输入模型"""
    session_id: Optional[str] = None # 首次提交为空，后续追问时携带
    input_type: str = Field(pattern="^(text|voice|image)$") 
    content: str 

class DiagnosisResult(BaseModel):
    """诊断结果模型"""
    possible_causes: list[dict]
    risk_level: str 
    advice: str

class ConsultationResponse(BaseModel):
    """问诊响应模型"""
    session_id: str
    status: str # processing / awaiting_input / complete
    next_question: Optional[str] = None # 系统追问的内容
    progress: int = 0 
    diagnosis_result: Optional[DiagnosisResult] = None 
    # 新增：聊天历史，用于记录上下文 [{"role": "user", "content": "..."}, ...]
    history: List[Dict[str, str]] = []