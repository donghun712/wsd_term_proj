from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from src import models, schemas, security
from src.database import get_db

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])

@router.get("", response_model=schemas.SystemStats)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """전체 시스템 통계 (관리자 전용)"""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    users_count = (await db.execute(select(func.count(models.User.id)))).scalar()
    courses_count = (await db.execute(select(func.count(models.Course.id)))).scalar()
    reviews_count = (await db.execute(select(func.count(models.Review.id)))).scalar()
    enroll_count = (await db.execute(select(func.count(models.Enrollment.id)))).scalar()
    
    return {
        "total_users": users_count or 0,
        "total_courses": courses_count or 0,
        "total_reviews": reviews_count or 0,
        "total_enrollments": enroll_count or 0
    }

# --- [추가 엔드포인트] 일별 통계 ---
@router.get("/daily")
async def get_daily_stats_mock(
    current_user: models.User = Depends(security.get_current_user)
):
    """[추가] 일별 방문자 및 가입자 통계 (Mock Data)"""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "2023-12-20": {"visits": 120, "signups": 5},
        "2023-12-21": {"visits": 145, "signups": 8},
        "2023-12-22": {"visits": 200, "signups": 15},
        "today": {"visits": 50, "signups": 2}
    }