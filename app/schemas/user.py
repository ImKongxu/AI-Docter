from pydantic import BaseModel, EmailStr, Field
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- Token 相关 ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

