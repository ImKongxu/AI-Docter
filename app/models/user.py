from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$") # 手机号格式校验

class UserCreate(UserBase):
    """用户注册输入模型"""
    password: str = Field(min_length=8, max_length=20) # 密码长度校验

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str

class UserResponse(UserBase):
    """用户响应模型"""
    user_id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True