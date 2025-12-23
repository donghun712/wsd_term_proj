from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from src import models, security
from src.database import get_db

# 관리자만 접근 가능하도록 설정
router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin)
):
    """[관리자 전용] 전체 시스템 통계 조회"""
    # 1. 총 유저 수
    user_count = await db.execute(select(func.count(models.User.id)))
    # 2. 총 강의 수
    course_count = await db.execute(select(func.count(models.Course.id)))
    # 3. 총 리뷰 수
    review_count = await db.execute(select(func.count(models.Review.id)))
    
    return {
        "total_users": user_count.scalar() or 0,
        "total_courses": course_count.scalar() or 0,
        "total_reviews": review_count.scalar() or 0
    }