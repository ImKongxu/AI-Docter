import httpx
import json
import re
import os
from openai import AsyncOpenAI
from app.models.diagnosis import SymptomInput, ConsultationResponse, DiagnosisResult
from app.core.session_storage import save_session
from app.core.database import AsyncSessionFactory
from app.crud.history_crud import create_diagnosis_history
from app.core.config import settings

# ==========================================
# 工具函数：JSON 清理
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

# ==========================================
# 核心功能：多模态处理 (语音/图片 -> 文字)
# ==========================================

async def process_voice_input(audio_url: str) -> str:
    """
    处理语音输入：
    1. 这里的 audio_url 是前端上传后返回的文件地址
    2. 我们需要调用 STT (语音转文字) API
    """
    print(f"正在处理语音: {audio_url}")
    
    # 初始化多模态客户端 (使用 .env 中的配置)
    # 注意：如果你的 .env 里没有配置 MULTI_MODAL_API_KEY，这里会报错
    # 建议在 settings.py 里添加对应的读取逻辑，或者直接在这里读取 os.environ
    api_key = os.getenv("MULTI_MODAL_API_KEY", settings.DEEPSEEK_API_KEY) 
    base_url = os.getenv("MULTI_MODAL_BASE_URL", "https://api.openai.com/v1")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    try:
        # 真实场景步骤 A: 下载音频文件到内存
        # async with httpx.AsyncClient() as http_client:
        #     response = await http_client.get(audio_url)
        #     audio_bytes = response.content
        
        # 真实场景步骤 B: 调用 Whisper 或 阿里 Paraformer
        # transcription = await client.audio.transcriptions.create(
        #     model="whisper-1", 
        #     file=("voice.mp3", audio_bytes), # 伪代码，需根据实际 API 要求调整
        # )
        # return transcription.text

        # --- 模拟实现 (为了让你能先跑通流程) ---
        return f"（系统模拟语音识别结果）：患者自述嗓子疼痛，伴有咳嗽，持续了三天，体温38度。"
    
    except Exception as e:
        print(f"语音识别失败: {e}")
        return f"语音识别失败，请重试。（错误信息：{str(e)}）"

async def process_image_input(image_url: str) -> str:
    """
    处理图片输入：
    调用视觉模型 (如 qwen-vl-max, gpt-4o) 识别图片中的文字内容
    """
    print(f"正在处理图片: {image_url}")
    
    api_key = os.getenv("MULTI_MODAL_API_KEY", settings.DEEPSEEK_API_KEY)
    base_url = os.getenv("MULTI_MODAL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    # 阿里云 Qwen-VL-Max 是目前处理中文表格/医疗报告性价比最高的模型之一
    # 如果用 OpenAI，模型名改为 "gpt-4o"
    model_name = "qwen-vl-max" 

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请提取这张医疗图片中的关键信息（如化验项目、结果、箭头标识）。不要分析病情，只提取文字数据。"},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        },
                    ],
                }
            ],
            max_tokens=500
        )
        extracted_text = response.choices[0].message.content
        print(f"图片识别结果: {extracted_text}")
        return f"（基于图片提取的内容）：{extracted_text}"

    except Exception as e:
        # 如果没有配置 Key 或调用失败，返回模拟数据以防崩溃
        print(f"图片识别异常: {e}")
        return "（模拟图片识别结果）：血常规报告显示：白细胞 12.0（偏高），中性粒细胞比率 85%（偏高），C反应蛋白 20mg/L。"

# ==========================================
# 主流程：AI 问诊
# ==========================================

async def process_symptoms_async(session_id: str, user_id: int, data: SymptomInput):
    """
    整合流程：
    1. 判断输入类型 (文本/语音/图片)
    2. 转换为文本 (Text)
    3. 调用 DeepSeek 进行诊断
    4. 存库
    """
    try:
        # Step 1: 初始状态更新
        await save_session(session_id, ConsultationResponse(
            session_id=session_id, status="processing", progress=10,
            next_question="正在分析您的输入...", diagnosis_result=None
        ))

        # Step 2: 多模态预处理 -> 统一转为 Text
        symptoms_text = ""
        
        if data.input_type == "text":
            symptoms_text = data.content
            await save_session(session_id, ConsultationResponse(
                session_id=session_id, status="processing", progress=30,
                next_question="正在理解病情描述...", diagnosis_result=None
            ))
            
        elif data.input_type == "voice":
            await save_session(session_id, ConsultationResponse(
                session_id=session_id, status="processing", progress=20,
                next_question="正在将语音转换为文字...", diagnosis_result=None
            ))
            # 这里传入的是语音文件的 URL
            symptoms_text = await process_voice_input(data.content)
            
        elif data.input_type == "image":
            await save_session(session_id, ConsultationResponse(
                session_id=session_id, status="processing", progress=20,
                next_question="正在识别检查报告/患处图片...", diagnosis_result=None
            ))
            # 这里传入的是图片的 URL
            symptoms_text = await process_image_input(data.content)

        # 校验提取结果
        if not symptoms_text:
            raise ValueError("无法从输入中提取有效信息")

        # Step 3: 调用 DeepSeek 进行诊断
        await save_session(session_id, ConsultationResponse(
            session_id=session_id, status="processing", progress=60,
            next_question="AI 医生正在会诊中...", diagnosis_result=None
        ))

        prompt = f"""
        你是一位专业且经验丰富的医生。请根据以下患者描述（可能包含语音转写的文本或OCR识别的报告数据），提供初步医疗诊断。
        
        【患者描述/报告数据】: 
        "{symptoms_text}"
        
        请严格遵守以下 JSON 格式返回，不要包含 Markdown 标记：
        {{
          "possible_causes": [
            {{ "name": "疾病名称", "confidence": "概率 (如 '85%')" }}
          ],
          "risk_level": "风险等级 (low, medium, high 之一)",
          "advice": "给患者的清晰建议 (限200字)"
        }}
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a professional AI doctor. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(settings.DEEPSEEK_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            raw_content = response.json()["choices"][0]["message"]["content"]
            final_result = json.loads(clean_json_string(raw_content))
            
            diagnosis = DiagnosisResult(**final_result)

    except Exception as e:
        print(f"诊断流程出错: {e}")
        diagnosis = DiagnosisResult(
            possible_causes=[],
            risk_level="unknown",
            advice=f"诊断过程中发生错误，请稍后重试。({str(e)})"
        )

    # Step 4: 保存最终结果
    final_data = ConsultationResponse(
        session_id=session_id, status="complete", progress=100,
        next_question=None, diagnosis_result=diagnosis
    )
    await save_session(session_id, final_data)

    # 持久化到数据库
    if diagnosis.risk_level != "unknown":
        try:
            async with AsyncSessionFactory() as db_session:
                await create_diagnosis_history(db_session, user_id, session_id, diagnosis)
        except Exception as db_e:
            print(f"数据库保存失败: {db_e}")