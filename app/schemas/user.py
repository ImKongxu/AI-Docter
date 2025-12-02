from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- Token 相关 ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

# --- 用户基础模型 (用于数据传输和验证) ---
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")

class UserCreate(UserBase):
    """用于 /register 接口的输入模型"""
    password: str = Field(min_length=8, max_length=20)
    email: EmailStr # 注册时邮箱必填

class UserLogin(BaseModel):
    """用于 /login 接口的输入模型 (FastAPI OAuth2PasswordRequestForm 会自动解析)"""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """用于 API 响应的用户信息模型"""
    id: int # 对应数据库的 ID
    is_active: bool = True
    
    class Config:
        from_attributes = True