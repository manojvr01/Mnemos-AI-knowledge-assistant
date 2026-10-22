import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Ensure local runtime storage & database directories exist
os.makedirs("./data", exist_ok=True)
os.makedirs(settings.STORAGE_LOCAL_ROOT, exist_ok=True)

# In test mode or when running SQLite, connect_args can be set appropriately
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

def get_session_maker():
    return async_session_maker

def set_session_maker(custom_maker):
    global async_session_maker
    async_session_maker = custom_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
