from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.diagnosis import SymptomInput, ConsultationResponse, DiagnosisResult
from app.services.ai_service import process_symptoms_async
from app.core.session_storage import load_session, save_session, session_exists
import uuid

router = APIRouter()

@router.post("/consultation/submit_symptom", response_model=ConsultationResponse)
async def submit_symptom(
    symptom_data: SymptomInput,
    background_tasks: BackgroundTasks,
    current_user: int = 1 # 假设通过依赖注入获取用户ID, 暂时硬编码为 1
):
    """
    提交症状描述，启动或继续问诊会话。
    """
    session_id = symptom_data.session_id
    
    # 首次提交或会话ID无效，生成新的会话ID
    if not session_id or not await session_exists(session_id):
        session_id = str(uuid.uuid4())
        # 初始化会话状态并存入 Redis
        initial_data = ConsultationResponse(
            session_id=session_id,
            status="processing",
            progress=0,
            next_question="已收到您的请求，正在分配AI医生..."
        )
        await save_session(session_id, initial_data)
    
    # 异步处理：避免复杂 AI 逻辑阻塞主线程
    background_tasks.add_task(
        process_symptoms_async, 
        session_id, 
        current_user, 
        symptom_data
    )
    
    # 立即返回当前会话状态
    current_session = await load_session(session_id)
    return current_session

@router.get("/consultation/{session_id}/status", response_model=ConsultationResponse)
async def get_consultation_status(session_id: str):
    """
    前端定期轮询（例如，间隔3秒）以获取最新状态。
    """
    session_data = await load_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return session_data

@router.get("/consultation/{session_id}/result", response_model=DiagnosisResult)
async def get_diagnosis_result(session_id: str):
    """
    获取最终的诊断结果。
    只有在 status 为 'complete' 时才能成功返回。
    """
    session_data = await load_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    if session_data.status != "complete":
        raise HTTPException(status_code=425, detail="诊断仍在进行中，请稍后重试。") # 425 Too Early
        
    if not session_data.diagnosis_result:
        raise HTTPException(status_code=500, detail="诊断已完成但结果数据丢失。")

    return session_data.diagnosis_result