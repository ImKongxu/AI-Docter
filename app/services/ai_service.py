import httpx
import json
import re
import os
from openai import AsyncOpenAI
from app.models.diagnosis import SymptomInput, ConsultationResponse, DiagnosisResult
from app.core.session_storage import save_session, load_session
from app.core.database import AsyncSessionFactory
from app.crud.history_crud import create_diagnosis_history
from app.core.config import settings

# --- 工具函数 ---
def clean_json_string(json_str: str) -> str:
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_str, re.DOTALL)
    if match: return match.group(1)
    start = json_str.find('{')
    end = json_str.rfind('}')
    if start != -1 and end != -1: return json_str[start:end+1]
    return json_str

async def download_file(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content

# --- 多模态处理 ---
async def process_voice_input(audio_url: str) -> str:
    """真实语音识别逻辑"""
    print(f"处理语音: {audio_url}")
    api_key = os.getenv("MULTI_MODAL_API_KEY", settings.DEEPSEEK_API_KEY)
    base_url = os.getenv("MULTI_MODAL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        audio_bytes = await download_file(audio_url)
        transcription = await client.audio.transcriptions.create(
            model="whisper-1", 
            file=("audio.mp3", audio_bytes, "audio/mpeg"),
        )
        return f"（患者语音自述）：{transcription.text}"
    except Exception as e:
        print(f"语音失败: {e}")
        return f"[语音识别失败: {str(e)}]"

async def process_image_input(image_url: str) -> str:
    """真实图片识别逻辑"""
    print(f"处理图片: {image_url}")
    api_key = os.getenv("MULTI_MODAL_API_KEY", settings.DEEPSEEK_API_KEY)
    base_url = os.getenv("MULTI_MODAL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        response = await client.chat.completions.create(
            model="qwen-vl-max",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": "请提取图中的医疗关键信息（症状、指标等），不要分析，只提取事实。"},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]}
            ],
            max_tokens=1000
        )
        return f"（图片提取信息）：{response.choices[0].message.content}"
    except Exception as e:
        print(f"图片失败: {e}")
        return f"[图片识别失败: {str(e)}]"

# --- 核心主流程 (支持多轮对话) ---

async def process_symptoms_async(session_id: str, user_id: int, data: SymptomInput):
    try:
        # 1. 加载当前会话
        session = await load_session(session_id)
        if not session: return

        # 2. 解析本次输入
        current_text = ""
        if data.input_type == "text":
            current_text = data.content
        elif data.input_type == "voice":
            current_text = await process_voice_input(data.content)
        elif data.input_type == "image":
            current_text = await process_image_input(data.content)

        # 3. 将新输入追加到历史记录 (User Role)
        session.history.append({"role": "user", "content": current_text})
        
        # 4. 构造 AI 提示词 (Prompt)
        # 关键：要求 AI 判断是追问 (question) 还是诊断 (diagnosis)
        system_prompt = """
        你是一位专业、耐心、负责的三甲医院全科医生。
        
        【任务目标】
        通过与患者的多轮对话，收集足够的信息，给出初步诊断建议。
        
        【决策逻辑】
        分析对话历史，判断信息是否充足（如：发病时间、诱因、伴随症状、疼痛程度等）。
        1. [需要追问]：如果信息模糊或缺失，请提出**一个**最关键的追问问题。语气要亲切。
        2. [给出诊断]：如果信息已基本充足，或已经追问了超过 3 轮，请给出详细的诊断结果。
        
        【输出格式】
        必须严格输出为以下 JSON 格式（不要包含 markdown 标记）：
        
        情况 A（需要追问）：
        {
            "type": "question",
            "content": "这里写你要追问患者的具体问题"
        }
        
        情况 B（诊断报告）：
        {
            "type": "diagnosis",
            "result": {
                "possible_causes": [{"name": "疾病A", "confidence": "80%"}, {"name": "疾病B", "confidence": "20%"}],
                "risk_level": "low" 或 "medium" 或 "high" 或 "urgent",
                "advice": "给患者的详细建议（包含就医指导、生活建议）"
            }
        }
        """

        # 构造发给 DeepSeek 的完整消息链
        messages = [{"role": "system", "content": system_prompt}]
        # 追加所有历史对话
        for msg in session.history:
            # 过滤掉 DeepSeek 不认识的字段，只留 role 和 content
            messages.append({"role": msg["role"], "content": msg["content"]})

        # 5. 调用 DeepSeek API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.5, # 适度灵活，方便自然追问
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(settings.DEEPSEEK_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            ai_raw = resp.json()["choices"][0]["message"]["content"]
            
            # 清理并解析 JSON
            parsed_res = json.loads(clean_json_string(ai_raw))

        # 6. 根据 AI 决策更新状态
        if parsed_res.get("type") == "question":
            # --- 分支 A：AI 决定追问 ---
            question_text = parsed_res["content"]
            
            session.status = "awaiting_input" # 状态变为等待用户输入
            session.next_question = question_text
            session.progress = min(session.progress + 15, 90) # 进度条增加
            
            # 将 AI 的问题加入历史
            session.history.append({"role": "assistant", "content": question_text})
            
        elif parsed_res.get("type") == "diagnosis":
            # --- 分支 B：AI 决定出结果 ---
            diag_data = parsed_res["result"]
            final_diagnosis = DiagnosisResult(**diag_data)
            
            session.status = "complete" # 状态变为完成
            session.progress = 100
            session.diagnosis_result = final_diagnosis
            session.next_question = None
            
            # 将诊断摘要加入历史
            session.history.append({"role": "assistant", "content": f"诊断完成。主要判断为：{final_diagnosis.possible_causes[0]['name']}。建议：{final_diagnosis.advice}"})
            
            # 存入数据库
            if final_diagnosis.risk_level != "unknown":
                async with AsyncSessionFactory() as db_session:
                    await create_diagnosis_history(db_session, user_id, session_id, final_diagnosis)

    except Exception as e:
        print(f"AI Process Error: {e}")
        session.status = "awaiting_input"
        # 遇到错误时，让用户重试，而不是卡死
        err_msg = "抱歉，刚才连接不稳定，请您重新描述一下症状。"
        session.next_question = err_msg
        session.history.append({"role": "assistant", "content": err_msg})

    # 7. 保存更新后的会话数据到 Redis/内存
    await save_session(session_id, session)