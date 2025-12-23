# backend/tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool # [중요] SQLite 메모리용 풀

from src.database import Base, get_db
from src import models
from src.main import app

# 테스트용 인메모리 DB (SQLite)
# connect_args={"check_same_thread": False} 는 SQLite 필수 옵션
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool, # 연결 유지 (데이터 증발 방지)
    echo=False
)

TestingSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    """비동기 이벤트 루프 생성"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    """테스트용 DB 세션 생성 및 초기화"""
    # 1. 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. 세션 제공
    async with TestingSessionLocal() as session:
        yield session
        # (옵션) 테스트 후 롤백은 자동 처리됨
        
    # 3. 테이블 삭제 (청소)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session):
    """FastAPI 앱의 DB 의존성을 가짜 DB 세션으로 교체"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    # Transport 설정으로 httpx 최신 버전 대응
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    
    app.dependency_overrides.clear()