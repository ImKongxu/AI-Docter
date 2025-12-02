import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

# 假设 Redis 在本地默认端口上运行
REDIS_URL = "redis://localhost:6379/0"

# 创建一个可复用的异步连接池
# decode_responses=True 会将从 Redis 获取的二进制数据自动解码为 UTF-8 字符串
pool = ConnectionPool.from_url(REDIS_URL, decode_responses=True, max_connections=10)

def get_redis_client() -> redis.Redis:
    """
    获取一个 Redis 异步客户端实例。
    """
    return redis.Redis(connection_pool=pool)
