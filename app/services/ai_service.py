import httpx
import json
import re
import os
import io
from openai import AsyncOpenAI
from app.models.diagnosis import SymptomInput, ConsultationResponse, DiagnosisResult
from app.core.session_storage import save_session
from app.core.database import AsyncSessionFactory
from app.crud.history_crud import create_diagnosis_history
from app.core.config import settings

# ==========================================
# 工具函数
# ==========================================
def clean_json_string(json_str: str) -> str:
    """清理 AI 返回的 Markdown 格式，提取纯 JSON"""
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_str, re.DOTALL)
    if match:
        return match.group(1)
    start = json_str.find('{')
    end = json_str.rfind('}')
    if start != -1 and end != -1:
        return json_str[start:end+1]
    return json_str

async def download_file(url: str) -> bytes:
    """辅助函数：下载文件并返回二进制数据"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content

# ==========================================
# 核心功能：多模态处理 (真实调用)
# ==========================================

async def process_voice_input(audio_url: str) -> str:
    """处理语音输入：下载音频 -> 调用 STT 接口"""
    print(f"正在处理语音 URL: {audio_url}")
    
    # 获取配置 (优先读取环境变量)
    api_key = os.getenv("MULTI_MODAL_API_KEY", settings.DEEPSEEK_API_KEY) 
    base_url = os.getenv("MULTI_MODAL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    try:
        # 1. 下载音频文件 (必需步骤，API通常无法访问你的私有URL)
        audio_bytes = await download_file(audio_url)
        
        # 2. 调用语音转文字 (以 Whisper/SenseVoice 为例)
        # 注意: 这里的 model 需根据你实际使用的服务商填写 (如 'whisper-1' 或 'paraformer-v1')
        transcription = await client.audio.transcriptions.create(
            model="whisper-1",  # 如果用阿里，可用 'paraformer-realtime-v1' 或兼容模型名
            file=("audio.mp3", audio_bytes, "audio/mpeg"), # 模拟文件名，帮助API识别格式
        )
        
        result_text = transcription.text
        print(f"语音识别结果: {result_text}")
        return f"（患者语音转述）：{result_text}"
    
    except Exception as e:
        print(f"语音识别失败: {e}")
        # 降级处理：依然让流程继续，但不包含语音内容
        return f"[语音识别失败，请让患者尝试文字描述。错误: {str(e)}]"

async def process_image_input(image_url: str) -> str:
    """处理图片输入：调用视觉模型"""
    print(f"正在处理图片 URL: {image_url}")
    
    api_key = os.getenv("MULTI_MODAL_API_KEY", settings.DEEPSEEK_API_KEY)
    base_url = os.getenv("MULTI_MODAL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    # 推荐使用 qwen-vl-max (阿里) 或 gpt-4o
    model_name = "qwen-vl-max" 

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    try:
        # 对于图片，如果 URL 是公网可访问的，直接传 URL 即可
        # 如果 URL 是内网的，你需要先下载并转 base64，这里假设是公网 URL
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请仔细阅读这张医疗图片（检查报告或患处照片），提取所有关键文字信息（如异常指标、诊断意见）。不要进行推断，只提取客观文字。"},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            max_tokens=1000
        )
        extracted_text = response.choices[0].message.content
        print(f"图片识别结果: {extracted_text}")
        return f"（基于图片提取的客观数据）：{extracted_text}"

    except Exception as e:
        print(f"图片识别异常: {e}")
        return f"[图片识别失败。错误: {str(e)}]"

# ==========================================
# 主流程：AI 问诊
# ==========================================

async def process_symptoms_async(session_id: str, user_id: int, data: SymptomInput):
    """DeepSeek 诊断主流程"""
    try:
        # 1. 状态: 分析输入
        await save_session(session_id, ConsultationResponse(
            session_id=session_id, status="processing", progress=10,
            next_question="正在解析您的输入数据...", diagnosis_result=None
        ))

        # 2. 多模态转换
        symptoms_text = ""
        
        if data.input_type == "text":
            symptoms_text = data.content
            await save_session(session_id, ConsultationResponse(
                session_id=session_id, status="processing", progress=20, next_question="正在理解病情..."
            ))
            
        elif data.input_type == "voice":
            await save_session(session_id, ConsultationResponse(
                session_id=session_id, status="processing", progress=20, next_question="正在将语音转换为文字..."
            ))
            symptoms_text = await process_voice_input(data.content)
            
        elif data.input_type == "image":
            await save_session(session_id, ConsultationResponse(
                session_id=session_id, status="processing", progress=20, next_question="正在读取检查报告..."
            ))
            symptoms_text = await process_image_input(data.content)

        # 3. 状态: AI 思考中
        await save_session(session_id, ConsultationResponse(
            session_id=session_id, status="processing", progress=60,
            next_question="AI 专家正在综合分析病情...", diagnosis_result=None
        ))

        # 4. 构造 Prompt
        prompt = f"""
        你是一位经验丰富的三甲医院全科医生。请根据以下信息进行初步诊断。
        
        【患者主诉/检查数据】: 
        {symptoms_text}
        
        请严格按照以下 JSON 格式输出（不要输出 Markdown 代码块）：
        {{
          "possible_causes": [ {{ "name": "疾病名称", "confidence": "概率(如85%)" }} ],
          "risk_level": "low" 或 "medium" 或 "high",
          "advice": "给患者的专业建议，包括需进行的检查或生活指导（200字以内）"
        }}
        """

        # 5. 调用 DeepSeek
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
        }
        
        # 使用 httpx 直接调用 DeepSeek (因为 ai_service 上面用了 OpenAI SDK 可能会有 BaseURL 冲突，这里分开写最稳)
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful medical AI. Return JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(settings.DEEPSEEK_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            api_res = resp.json()
            raw_content = api_res["choices"][0]["message"]["content"]
            
            # 解析结果
            final_result = json.loads(clean_json_string(raw_content))
            diagnosis = DiagnosisResult(**final_result)

    except Exception as e:
        print(f"诊断流程错误: {e}")
        # 发生错误时，保存一个错误的诊断结果，避免前端一直卡在 processing
        diagnosis = DiagnosisResult(
            possible_causes=[], risk_level="unknown", advice=f"服务暂时繁忙，请稍后重试。({str(e)})"
        )

    # 6. 完成并保存
    final_data = ConsultationResponse(
        session_id=session_id, status="complete", progress=100,
        next_question=None, diagnosis_result=diagnosis
    )
    await save_session(session_id, final_data)

    if diagnosis.risk_level != "unknown":
        async with AsyncSessionFactory() as db_session:
            await create_diagnosis_history(db_session, user_id, session_id, diagnosis)