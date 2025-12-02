AI Doctor Backend (AI 问诊小程序后端)
这是一个基于 FastAPI 构建的智能问诊系统后端服务。它利用 DeepSeek 大模型 的能力，根据用户描述的症状提供初步的医疗诊断、风险评估及健康建议。

项目采用异步架构设计，结合 Redis 进行会话管理，并使用 SQLite 持久化存储诊断历史，适合作为医疗辅助类小程序或 Web 应用的后端服务。

📚 功能特性
🤖 智能诊断：集成 DeepSeek API，模拟专业医生进行病情分析，返回结构化的诊断报告（可能病因、置信度、风险等级、建议）。

⚡ 异步处理：利用 FastAPI 的 BackgroundTasks 异步处理耗时的 AI 推理任务，保证 API 接口的快速响应。

🔄 状态轮询：提供标准的状态查询机制（Processing -> Complete），适配前端轮询逻辑。

💾 数据持久化：自动将诊断结果保存至 SQLite 数据库，支持按用户查询历史记录。

🚀 高性能：全链路异步 I/O 操作（Async Database, Async Redis, Async HTTP Client）。

🛠️ 技术栈
Web 框架: FastAPI

语言: Python 3.8+

数据库: SQLite (配合 SQLAlchemy + aiosqlite 异步驱动)

缓存/会话: Redis (配合 redis-py 异步客户端)

AI 服务: DeepSeek API (通过 httpx 调用)

数据验证: Pydantic

📂 项目结构
Plaintext

AIdoctor/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── consultation.py  # 问诊相关接口 (提交、状态、结果)
│   │       │   └── history.py       # 历史记录接口
│   │       └── api.py               # 路由汇总
│   ├── core/
│   │   ├── config.py          # 配置加载
│   │   ├── database.py        # 数据库连接与会话
│   │   ├── redis_client.py    # Redis 连接池
│   │   ├── security.py        # 加密与安全工具
│   │   └── session_storage.py # 会话状态管理逻辑
│   ├── crud/
│   │   └── history_crud.py    # 数据库 CRUD 操作
│   ├── models/
│   │   ├── diagnosis.py       # Pydantic 模型 (输入/输出定义)
│   │   ├── history.py         # SQLAlchemy ORM 模型 (数据库表)
│   │   └── user.py            # 用户模型
│   ├── services/
│   │   └── ai_service.py      # AI 核心业务逻辑 (调用 DeepSeek)
│   └── main.py                # 程序入口
├── .env                       # 环境变量 (API Key 等)
├── requirements.txt           # 项目依赖
└── README.md                  # 项目说明
🚀 快速开始
1. 环境准备
确保本地已安装：

Python 3.8 或更高版本

Redis 服务 (默认端口 6379)

2. 安装依赖
Bash

# 创建虚拟环境 (推荐)
python -m venv venv
# Windows 激活
venv\Scripts\activate
# Linux/Mac 激活
source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
3. 配置环境变量
在项目根目录下创建一个 .env 文件，并填入以下内容（参考 .env.example）：

Ini, TOML

# DeepSeek API 配置
DEEPSEEK_API_KEY="sk-你的DeepSeek密钥"

# 数据库配置 (默认使用本地 SQLite)
DATABASE_URL="sqlite+aiosqlite:///./diagnosis_history.db"

# Redis 配置 (视本地情况修改)
REDIS_URL="redis://localhost:6379/0"
4. 运行服务
使用 uvicorn 启动服务：

Bash

uvicorn app.main:app --reload
服务启动后，API 文档将自动生成：

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

🔌 API 接口说明
完整的交互流程如下：

提交症状

POST /api/v1/consultation/submit_symptom

Body: {"input_type": "text", "content": "头痛，伴有轻微发烧，持续两天了"}

Response: 返回 session_id 和初始状态 processing。

轮询状态 (前端每隔几秒调用一次)

GET /api/v1/consultation/{session_id}/status

Response: 返回当前 status (processing/complete) 和 progress (进度条数值)。

获取结果

GET /api/v1/consultation/{session_id}/result

Condition: 仅当状态为 complete 时调用。

Response: 返回详细的诊断 JSON（包含可能病因、建议等）。

查看历史

GET /api/v1/history/{user_id}

⚠️ 注意事项
DeepSeek Key: 请务必在 .env 中配置有效的 API Key，否则 AI 诊断功能无法使用。

Redis 依赖: 服务启动强依赖 Redis，请确保 Redis 服务已开启。

输入类型: 目前仅支持 text 类型的症状描述。虽然模型定义了 voice/image，但尚未实现对应的转写/OCR 处理逻辑。

📝 待办计划 (To-Do)
[ ] 接入 STT (语音转文字) 服务，支持语音输入。

[ ] 接入 OCR 或多模态模型，支持上传检查报告图片。

[ ] 完善用户注册/登录系统 (JWT 鉴权)。

[ ] 增加 Docker 部署支持。