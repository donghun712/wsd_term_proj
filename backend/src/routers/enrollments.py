from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src import models, schemas, security
from src.database import get_db

router = APIRouter(tags=["Enrollments"])


@router.post(
    "/courses/{course_id}/enroll",
    status_code=201,
    response_model=schemas.EnrollmentResponse,
)
async def enroll_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    # 1) 강의 존재 확인
    course = (await db.execute(
        select(models.Course).where(models.Course.id == course_id)
    )).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2) 중복 수강 확인
    existing = (await db.execute(
        select(models.Enrollment).where(
            models.Enrollment.user_id == current_user.id,
            models.Enrollment.course_id == course_id
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Already enrolled")

    # 3) 생성
    new_enrollment = models.Enrollment(
        user_id=current_user.id,
        course_id=course_id,
        status="ACTIVE",
    )
    db.add(new_enrollment)
    await db.commit()
    await db.refresh(new_enrollment)  # enrolled_at 채우기

    # ✅ 핵심: ORM 객체를 그대로 반환하지 말고 dict로 반환 (관계(course) lazy-load 방지)
    return {
        "id": new_enrollment.id,
        "user_id": new_enrollment.user_id,
        "course_id": new_enrollment.course_id,
        "status": new_enrollment.status,
        "enrolled_at": new_enrollment.enrolled_at,
        "course": None,  # EnrollmentResponse에 course가 Optional이라 문제 없음
    }



# 2. 내 수강 목록 조회 (GET)
# 프론트엔드 편의를 위해 CourseResponse 리스트 반환 유지
@router.get("/enrollments/me", response_model=List[schemas.CourseResponse])
async def get_my_enrollments(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    query = (
        select(models.Enrollment)
        .options(
            selectinload(models.Enrollment.course).selectinload(models.Course.instructor),
            selectinload(models.Enrollment.course).selectinload(models.Course.category),
        )
        .where(models.Enrollment.user_id == current_user.id)
    )

    enrollments = (await db.execute(query)).scalars().all()
    return [e.course for e in enrollments if e.course is not None]


# 3. 수강 취소 (DELETE)
@router.delete("/enrollments/{course_id}", status_code=204)
async def cancel_enrollment(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    enrollment = (await db.execute(
        select(models.Enrollment).where(
            models.Enrollment.user_id == current_user.id,
            models.Enrollment.course_id == course_id,
        )
    )).scalar_one_or_none()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    await db.delete(enrollment)
    await db.commit()
    return None
