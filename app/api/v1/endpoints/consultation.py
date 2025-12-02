from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from app.models.diagnosis import SymptomInput, ConsultationResponse, DiagnosisResult
from app.services.ai_service import process_symptoms_async
from app.core.session_storage import load_session, save_session, session_exists
from app.api.deps import get_current_user
from app.models.user import User
import uuid

router = APIRouter()

@router.post("/consultation/submit_symptom", response_model=ConsultationResponse)
async def submit_symptom(
    symptom_data: SymptomInput,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    提交症状描述。如果是首次提交，创建新会话；如果是回复追问，延续旧会话。
    """
    session_id = symptom_data.session_id
    
    # 1. 检查是“新问诊”还是“回复追问”
    if session_id and await session_exists(session_id):
        # --- 老会话：读取现有数据 ---
        current_session = await load_session(session_id)
        # 更新状态为处理中，准备让 AI 思考
        current_session.status = "processing"
        current_session.next_question = None 
    else:
        # --- 新会话：初始化 ---
        session_id = str(uuid.uuid4())
        current_session = ConsultationResponse(
            session_id=session_id,
            status="processing",
            progress=0,
            next_question="正在分析您的病情...",
            history=[] # 初始化空历史
        )
    
    # 2. 保存当前状态（防止异步任务未启动前前端查询报错）
    await save_session(session_id, current_session)
    
    # 3. 启动异步 AI 处理任务
    # 注意：这里我们传入 session_id，service 层会自动读取并追加历史
    background_tasks.add_task(
        process_symptoms_async, 
        session_id, 
        current_user.id, 
        symptom_data
    )
    
    return current_session

@router.get("/consultation/{session_id}/status", response_model=ConsultationResponse)
async def get_consultation_status(session_id: str):
    session_data = await load_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session_data

@router.get("/consultation/{session_id}/result", response_model=DiagnosisResult)
async def get_diagnosis_result(session_id: str):
    session_data = await load_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    if session_data.status != "complete":
        raise HTTPException(status_code=425, detail="诊断仍在进行中")
        
    if not session_data.diagnosis_result:
        raise HTTPException(status_code=500, detail="数据丢失")

    return session_data.diagnosis_result