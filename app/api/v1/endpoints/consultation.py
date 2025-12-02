from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from app.models.diagnosis import SymptomInput, ConsultationResponse, DiagnosisResult
from app.services.ai_service import process_symptoms_async
from app.core.session_storage import load_session, save_session, session_exists
from app.api.deps import get_current_user # 导入依赖
from app.models.user import User
import uuid

router = APIRouter()

@router.post("/consultation/submit_symptom", response_model=ConsultationResponse)
async def submit_symptom(
    symptom_data: SymptomInput,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user) # 关键修改：自动验证 Token 并获取用户对象
):
    """
    提交症状描述，启动或继续问诊会话。
    需要 Header: Authorization: Bearer <your_token>
    """
    session_id = symptom_data.session_id
    
    # ... (原有 session 逻辑不变) ...
    if not session_id or not await session_exists(session_id):
        session_id = str(uuid.uuid4())
        initial_data = ConsultationResponse(
            session_id=session_id,
            status="processing",
            progress=0,
            next_question="已收到您的请求，正在分配AI医生..."
        )
        await save_session(session_id, initial_data)
    
    # 异步任务传入真实的用户 ID
    background_tasks.add_task(
        process_symptoms_async, 
        session_id, 
        current_user.id,  # 使用解析出来的真实 ID
        symptom_data
    )
    
    current_session = await load_session(session_id)
    return current_session

# ... status 和 result 接口保持不变，或者也可以加上 Depends(get_current_user) 进行保护 ...