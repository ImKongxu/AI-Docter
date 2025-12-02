from app.models.diagnosis import ConsultationResponse
from app.core.redis_client import get_redis_client
import json

# 设置会话的过期时间为 24 小时
SESSION_EXPIRATION_SECONDS = 60 * 60 * 24 

async def save_session(session_id: str, data: ConsultationResponse):
    """
    将问诊会话数据序列化为 JSON 并存入 Redis。
    """
    redis = get_redis_client()
    # Pydantic v2 使用 model_dump_json
    json_data = data.model_dump_json()
    await redis.set(session_id, json_data, ex=SESSION_EXPIRATION_SECONDS)

async def load_session(session_id: str) -> ConsultationResponse | None:
    """
    从 Redis 读取会话数据并反序列化为 Pydantic 模型。
    """
    redis = get_redis_client()
    json_data = await redis.get(session_id)
    
    if not json_data:
        return None
    
    # Pydantic v2 使用 model_validate_json
    return ConsultationResponse.model_validate_json(json_data)

async def session_exists(session_id: str) -> bool:
    """
    检查会话是否存在于 Redis 中。
    """
    redis = get_redis_client()
    return await redis.exists(session_id) > 0