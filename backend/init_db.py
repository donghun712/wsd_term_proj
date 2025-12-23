import asyncio
from src.database import engine, Base
from src.models import * # 모든 모델 불러오기 (User, Course 등)

async def create_tables():
    print("⏳ 테이블 생성 시작...")
    async with engine.begin() as conn:
        # 기존 테이블이 있다면 삭제하고 새로 생성 (초기화)
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())