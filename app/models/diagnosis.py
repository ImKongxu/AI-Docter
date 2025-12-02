from pydantic import BaseModel, Field
from typing import Optional

class SymptomInput(BaseModel):
    """问诊输入模型"""
    session_id: Optional[str] = None # 首次提交为空，后续追问时携带
    input_type: str = Field(pattern="^(text|voice|image)$") # 输入类型
    content: str # 文本描述、语音文件/图片 URL

class DiagnosisResult(BaseModel):
    """诊断结果模型 (仅在 status: complete 时返回)"""
    possible_causes: list[dict]
    risk_level: str # low / medium / high / urgent
    advice: str

class ConsultationResponse(BaseModel):
    """问诊响应模型"""
    session_id: str
    status: str # processing / awaiting_input / complete
    next_question: Optional[str] = None # 系统追问
    progress: int = 0 # 进度条
    diagnosis_result: Optional[DiagnosisResult] = None # 最终诊断结果