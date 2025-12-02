import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/chat/completions"
    
    # JWT 配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret") # 生产环境请在.env中设置
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # Token 有效期 1 天

settings = Settings()