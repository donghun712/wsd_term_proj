from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src import models, schemas, security
from src.database import get_db

router = APIRouter(tags=["Reviews"])


# ✅ 1) 수강평 작성 (POST) - 테스트가 기대하는 경로
@router.post(
    "/courses/{course_id}/reviews",
    status_code=201,
    response_model=schemas.ReviewResponse,
)
async def create_review(
    course_id: int,
    review_create: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    # 강의 존재 확인
    course = (await db.execute(select(models.Course).where(models.Course.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # (권장) 수강한 사람만 리뷰 작성 가능
    enrolled = (await db.execute(
        select(models.Enrollment).where(
            models.Enrollment.user_id == current_user.id,
            models.Enrollment.course_id == course_id,
            models.Enrollment.status == "ACTIVE",
        )
    )).scalar_one_or_none()
    if not enrolled:
        raise HTTPException(status_code=403, detail="Enroll required to review")

    review = models.Review(
        user_id=current_user.id,
        course_id=course_id,
        rating=review_create.rating,
        comment=review_create.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    # 응답에 user 포함이 필요하면(ReviewResponse가 user 포함하는 경우) selectinload로 재조회
    result = await db.execute(
        select(models.Review)
        .options(selectinload(models.Review.user))
        .where(models.Review.id == review.id)
    )
    return result.scalar_one()


# ✅ 2) 강의별 수강평 조회 (GET) - 설계 문서/프론트용
@router.get(
    "/courses/{course_id}/reviews",
    response_model=List[schemas.ReviewResponse],
)
async def get_course_reviews(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    # 강의 존재 확인(없으면 404)
    course = (await db.execute(select(models.Course).where(models.Course.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    rows = (await db.execute(
        select(models.Review)
        .options(selectinload(models.Review.user))
        .where(models.Review.course_id == course_id)
        .order_by(models.Review.created_at.desc())
    )).scalars().all()
    return rows


# 3) 수강평 수정 (PUT) - 기존 경로 유지
@router.put("/reviews/{review_id}", response_model=schemas.ReviewResponse)
async def update_review(
    review_id: int,
    review_update: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    review = (await db.execute(select(models.Review).where(models.Review.id == review_id))).scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this review")

    review.rating = review_update.rating
    review.comment = review_update.comment
    await db.commit()

    result = await db.execute(
        select(models.Review)
        .options(selectinload(models.Review.user))
        .where(models.Review.id == review_id)
    )
    return result.scalar_one()


# 4) 수강평 삭제 (DELETE) - 기존 경로 유지
@router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    review = (await db.execute(select(models.Review).where(models.Review.id == review_id))).scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")

    await db.delete(review)
    await db.commit()
    return None
