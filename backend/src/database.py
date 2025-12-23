from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

# DB URL 설정
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 엔진 생성
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True, # 쿼리 로그 확인용 (운영 시에는 False 권장)
    future=True
)

# [핵심 수정] expire_on_commit=False 설정을 반드시 추가해야 합니다!
# 이 설정이 있어야 commit 후에도 객체 데이터가 메모리에 남아있어 에러가 안 납니다.
async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,  # <--- 이 부분이 누락되어 있었습니다.
    autoflush=False
)

Base = declarative_base()

# 의존성 주입 함수
async def get_db():
    async with async_session_maker() as session:
        yield session