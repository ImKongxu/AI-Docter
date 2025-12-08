这是一个为您定制的、功能完整的 README.md 文件。它涵盖了项目介绍、技术栈、安装配置、以及前后端的使用说明。您可以直接将以下内容保存为项目根目录下的 README.md 文件。

AI 智能医疗助手 (AI Doctor Assistant)
这是一个基于 FastAPI 和 Vue.js 构建的全栈智能问诊系统。它集成了 DeepSeek 大模型 的推理能力，能够模拟专业医生进行多轮问诊，支持文本、语音、图片等多模态输入，并提供完整的用户认证与历史记录管理功能。

✨ 核心特性
🤖 智能多轮问诊：不同于传统的单轮问答，本系统支持连续对话。AI 会根据患者描述判断信息是否充足，自动进行追问，直到收集到足够信息才给出诊断建议。

🎙️ 多模态支持：

文本：自然语言描述症状。

语音：支持语音文件 URL 识别（自动转文字）。

图片：支持检查报告或患处照片 URL 识别（自动提取关键信息）。

🔐 完整的用户系统：包含用户注册、登录、密码加密存储及 JWT (JSON Web Token) 安全认证。

💾 历史记录回溯：系统会将每一次问诊的完整对话过程（不仅是结果）持久化存储。用户随时可以查看过往的诊断详情。

💻 现代化前端：基于 Vue 3 + Tailwind CSS 构建的单页应用 (SPA)，界面美观，响应式适配移动端与 PC 端，支持 Markdown 渲染。

🛠️ 技术栈
后端 (Backend)
框架: FastAPI (高性能 Python Web 框架)

数据库: SQLite (配合 SQLAlchemy + aiosqlite 异步驱动)

AI 服务:

DeepSeek API (核心医学推理)

OpenAI 兼容接口 (用于 STT 语音转文字和 Vision 图片识别，如阿里云 DashScope)

安全: python-jose (JWT 令牌), passlib (BCrypt 密码哈希)

工具: Pydantic (数据验证), httpx (异步 HTTP 请求)

前端 (Frontend)
核心: Vue.js 3 (Composition API)

样式: Tailwind CSS (Utility-first CSS 框架)

网络: Axios

渲染: Marked.js (Markdown 解析)

图标: FontAwesome

🚀 快速开始
1. 后端部署
环境要求
Python 3.8 或更高版本

安装步骤
安装依赖

Bash

pip install -r requirements.txt
配置环境变量 在项目根目录下创建一个 .env 文件，填入您的 API Key（参考下方示例）：

Ini, TOML

# --- 核心问诊服务 (DeepSeek) ---
DEEPSEEK_API_KEY="sk-你的DeepSeek密钥"
DEEPSEEK_API_URL="https://api.deepseek.com/chat/completions"

# --- 多模态服务 (语音/图片识别) ---
# 这里以兼容 OpenAI 格式的服务商（如阿里云 DashScope）为例
MULTI_MODAL_API_KEY="sk-你的多模态服务密钥"
MULTI_MODAL_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# --- 安全配置 ---
SECRET_KEY="请修改为一个复杂的随机字符串"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
初始化数据库

如果是首次运行，无需操作，系统启动时会自动生成 diagnosis_history.db。

注意：如果之前运行过旧版本代码，请务必先删除旧的 .db 文件，以便系统重建包含新字段的表结构。

启动服务

Bash

uvicorn app.main:app --reload
启动成功后，后端 API 地址默认为：http://127.0.0.1:8000

2. 前端运行
本项目的为了极简体验，前端采用了 无构建 (No-Build) 模式，不需要安装 Node.js 或 npm。

找到项目根目录下的 index.html 文件。

直接双击，使用浏览器（推荐 Chrome, Edge, Safari）打开即可。

前端会自动连接本地运行的后端 API。

📖 使用指南
注册与登录：

首次打开页面，点击“注册”标签，输入邮箱和密码完成注册。

注册成功后，切换到“登录”标签登录系统。

进行问诊：

在底部输入框描述您的症状（例如：“我最近两天头痛，还伴有低烧”）。

点击发送。AI 可能会追问您具体的细节（如体温多少、是否有其他症状）。

持续回复 AI 的问题，直到 AI 收集到足够信息，生成包含病因分析、风险等级和建议的诊断卡片。

多模态功能：

点击输入框上方的“图片链接”或“语音链接”单选框。

输入可公开访问的 URL（http/https 开头），发送给 AI 进行分析。

查看历史：

点击界面左侧（移动端为左上角菜单）的历史记录列表。

点击任意一条记录，即可完整还原当时的对话情景。

📂 项目结构
Plaintext

AIdoctor/
├── app/
│   ├── api/
│   │   ├── endpoints/     # 具体的 API 接口 (Auth, Consultation, History)
│   │   ├── deps.py        # 依赖注入 (如获取当前用户)
│   │   └── api.py         # 路由汇总
│   ├── core/              # 核心配置 (Database, Security, Session)
│   ├── crud/              # 数据库增删改查操作
│   ├── models/            # SQLAlchemy 数据库模型
│   ├── schemas/           # Pydantic 数据交互模型
│   ├── services/          # 业务逻辑层 (DeepSeek 调用, 多模态处理)
│   └── main.py            # 程序入口
├── index.html             # Vue 前端入口文件
├── requirements.txt       # Python 依赖列表
├── .env                   # 环境变量配置 (需自行创建)
└── diagnosis_history.db   # SQLite 数据库文件 (自动生成)
⚠️ 注意事项
API Key：请确保 .env 文件中的 Key 有效且有余额。

多模态输入：目前的实现是通过后端下载 URL 内容。因此，输入的图片/语音 URL 必须是后端服务器能够访问到的公网地址。

数据安全：生产环境部署时，请务必修改 SECRET_KEY 并将 allow_origins 限制为特定的前端域名。