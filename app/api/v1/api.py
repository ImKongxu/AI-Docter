from fastapi import APIRouter
from app.api.v1.endpoints import consultation, history, auth

api_router = APIRouter()

# 核心模块
api_router.include_router(consultation.router, tags=["Consultation"])
api_router.include_router(history.router, tags=["History"])

# 认证模块，带有 /auth 前缀
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])