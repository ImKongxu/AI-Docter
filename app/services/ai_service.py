import httpx
import json
import re
from app.models.diagnosis import SymptomInput, ConsultationResponse, DiagnosisResult
from app.core.session_storage import save_session
from app.core.database import AsyncSessionFactory
from app.crud.history_crud import create_diagnosis_history
from app.core.config import settings

def clean_json_string(json_str: str) -> str:
    """
    清理从 AI 获取的 JSON 字符串。
    DeepSeek 等模型经常会返回 markdown 格式，例如:
    ```json
    { ... }
    ```
    我们需要去除 markdown 标记以进行解析。
    """
    # 移除 ```json 和 ``` 标记
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_str, re.DOTALL)
    if match:
        return match.group(1)
    
    # 如果没有 markdown 标记，尝试直接查找第一个 { 和最后一个 }
    # 这可以处理开头或结尾有额外杂文本的情况
    start = json_str.find('{')
    end = json_str.rfind('}')
    if start != -1 and end != -1:
        return json_str[start:end+1]
    
    return json_str

async def process_symptoms_async(session_id: str, user_id: int, data: SymptomInput):
    """
    调用 DeepSeek API 获取真实诊断结果。
    """
    try:
        # 1. 更新状态为 "processing"
        in_progress_data = ConsultationResponse(
            session_id=session_id, status="processing", progress=50,
            next_question=None, diagnosis_result=None
        )
        await save_session(session_id, in_progress_data)

        # 2. 检查输入类型 (暂时仅支持文本)
        if data.input_type != "text":
            # 如果是语音或图片，目前逻辑无法处理，直接返回提示
            diagnosis = DiagnosisResult(
                possible_causes=[],
                risk_level="unknown",
                advice=f"当前后端仅支持文本问诊。您上传了 {data.input_type} 类型的数据，请提供文字描述。"
            )
        else:
            # 3. 构造 DeepSeek API 请求
            # 修正：使用 data.content 而不是 data.symptoms
            symptoms_text = data.content 
            
            prompt = f"""
            你是一位专业且经验丰富的医生。请根据以下患者描述的症状，提供初步的医疗诊断建议。
            
            患者描述: "{symptoms_text}"
            
            你的回答必须严格遵守以下 JSON 格式，不要包含任何额外的解释或Markdown标记：
            {{
              "possible_causes": [
                {{
                  "name": "疾病名称",
                  "confidence": "概率 (例如 '85%')"
                }}
              ],
              "risk_level": "风险等级 (low, medium, high 之一)",
              "advice": "给患者的清晰、可执行的建议 (200字以内)"
            }}
            """

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
            }

            payload = {
                "model": "deepseek-chat", # 确保模型名称正确，DeepSeek V3 通常使用 deepseek-chat
                "messages": [
                    {"role": "system", "content": "You are a helpful AI medical assistant. You output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3, # 降低温度以提高格式输出的稳定性
                "stream": False
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(settings.DEEPSEEK_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                
                api_response = response.json()
                raw_content = api_response["choices"][0]["message"]["content"]
                
                # 4. 清理并解析 JSON
                cleaned_json = clean_json_string(raw_content)
                final_result = json.loads(cleaned_json)

                diagnosis = DiagnosisResult(**final_result)

    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        error_message = f"API 调用失败: {str(e)}"
        print(error_message)
        diagnosis = DiagnosisResult(
            possible_causes=[],
            risk_level="unknown",
            advice="无法连接到 AI 医生，请稍后再试。"
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        error_message = f"解析响应失败: {str(e)}\n原始内容: {locals().get('raw_content', 'N/A')}"
        print(error_message)
        diagnosis = DiagnosisResult(
            possible_causes=[],
            risk_level="unknown",
            advice="AI 医生的回复格式有误，请重试。"
        )
    except Exception as e:
        error_message = f"未预期的错误: {str(e)}"
        print(error_message)
        diagnosis = DiagnosisResult(
            possible_causes=[],
            risk_level="unknown",
            advice="系统发生内部错误，请联系管理员。"
        )

    # 5. 保存最终结果到 Redis
    final_data = ConsultationResponse(
        session_id=session_id, status="complete", progress=100,
        next_question=None, diagnosis_result=diagnosis
    )
    await save_session(session_id, final_data)

    # 6. 异步持久化到 SQLite 数据库
    if diagnosis.risk_level != "unknown": # 仅保存有效诊断
        try:
            async with AsyncSessionFactory() as db_session:
                await create_diagnosis_history(
                    db=db_session,
                    user_id=user_id,
                    session_id=session_id,
                    result=diagnosis
                )
        except Exception as e:
            print(f"Error saving history to DB: {e}")