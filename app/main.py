from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.models.history import DiagnosisHistory # 确保模型被加载

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时执行
    async with engine.begin() as conn:
        # 这将根据加载的所有模型创建表 (这里是 DiagnosisHistory)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 应用关闭时执行 (如果需要)
    # await engine.dispose()

app = FastAPI(
    title="AI 问诊小程序后端",
    description="支持多模态输入和智能诊断的辅助健康系统。",
    lifespan=lifespan
)

# 配置 CORS 允许跨域访问（如果需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境应严格限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "AI Diagnosis Backend Running"}