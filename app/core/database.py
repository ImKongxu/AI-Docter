from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 定义 SQLite 数据库文件
DATABASE_URL = "sqlite+aiosqlite:///./diagnosis_history.db"

# 创建异步数据库引擎
# connect_args 用于 aiosqlite，确保多线程访问的安全性
engine = create_async_engine(
    DATABASE_URL, 
    echo=True, # echo=True 会打印执行的 SQL 语句，便于调试
    connect_args={"check_same_thread": False}
)

# 创建一个异步会话工厂
# expire_on_commit=False 意味着在提交后，对象不会失效，仍可访问
AsyncSessionFactory = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 创建一个所有 ORM 模型都要继承的基类
Base = declarative_base()

async def get_db_session() -> AsyncSession:
    """
    FastAPI 依赖注入函数，用于获取数据库会话。
    它确保每个请求都使用独立的会话，并在请求结束后自动关闭。
    """
    async with AsyncSessionFactory() as session:
        yield session
