from pydantic import BaseModel, EmailStr, Field
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- Token 相关 ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

# --- 用户相关 ---
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=20)
    email: EmailStr # 注册时邮箱必填

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int # 注意这里对应数据库的 id
    is_active: bool = True
    
    class Config:
        from_attributes = True
