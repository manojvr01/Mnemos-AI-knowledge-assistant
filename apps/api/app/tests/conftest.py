import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.base import Base
from app.db.session import get_db, set_session_maker, async_session_maker
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.factory import set_embedding_provider
from app.rag.llm.mock import MockLLMProvider
from app.rag.llm.factory import set_llm_provider


@pytest.fixture(autouse=True)
def setup_default_test_providers():
    """Ensure test suite runs deterministically with 768-dim mock providers."""
    set_embedding_provider(MockEmbeddingProvider(dimension=768))
    set_llm_provider(MockLLMProvider())
    yield
    set_embedding_provider(None)
    set_llm_provider(None)

# Use in-memory SQLite for high-speed, isolated unit and integration testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database schema for each test."""
    set_session_maker(TestingSessionLocal)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient with the database dependency overridden."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
