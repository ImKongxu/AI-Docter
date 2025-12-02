import bcrypt
from datetime import datetime, timedelta
from typing import Optional

# ... JWT 相关的导入和配置稍后添加 ...

def hash_password(password: str) -> str:
    """使用 BCrypt 算法加密密码。"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否与哈希密码匹配。"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))