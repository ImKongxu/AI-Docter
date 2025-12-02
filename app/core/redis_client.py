# 这是一个存根文件，用于在不启动 Redis 服务时避免程序崩溃。
# 会话存储逻辑已迁移到 app/core/session_storage.py 使用内存字典。

class RedisClientStub:
    """模拟 Redis 客户端，确保程序启动不报错"""
    def __init__(self):
        pass
        
    def ping(self):
        return True # 模拟连接成功
        
    async def get_connection(self):
        # 避免连接尝试
        pass
        
    # 其他方法如果被调用会直接失败，但核心的 session_storage 已经不使用它了。
    
def get_redis_client():
    """返回一个 Redis 客户端存根实例"""
    return RedisClientStub()