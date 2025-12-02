import os
from dotenv import load_dotenv

# Load environment variables from .env file
# The path is relative to the project root where the app is started.
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/chat/completions"

settings = Settings()
