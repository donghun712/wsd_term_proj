# backend/src/routers/lectures.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from src import models, schemas, security
from src.database import get_db

router = APIRouter(tags=["Lectures"])

# 강의 하위 리소스로 생성
@router.post("/courses/{course_id}/lectures", response_model=schemas.LectureResponse, status_code=201)
async def create_lecture(
    course_id: int,
    lecture_data: schemas.LectureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # 강의 존재 확인
    result = await db.execute(select(models.Course).where(models.Course.id == course_id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    new_lecture = models.Lecture(
        **lecture_data.model_dump(),
        course_id=course_id
    )
    db.add(new_lecture)
    await db.commit()
    await db.refresh(new_lecture)
    return new_lecture

# 강의 하위 리소스로 목록 조회
@router.get("/courses/{course_id}/lectures", response_model=List[schemas.LectureResponse])
async def list_course_lectures(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Lecture).where(models.Lecture.course_id == course_id)
    result = await db.execute(query)
    return result.scalars().all()