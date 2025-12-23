from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from src import models, schemas, security
from src.database import get_db

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("", response_model=schemas.CourseResponse, status_code=201)
async def create_course(
    course_data: schemas.CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """강의 생성 (DB 설정 수정 후 최종본)"""
    new_course = models.Course(
        **course_data.model_dump(),
        instructor_id=current_user.id
    )
    
    db.add(new_course)
    await db.commit()
    # expire_on_commit=False 덕분에 여기서 new_course 데이터가 살아있습니다.
    
    # 관계 데이터(강사, 카테고리)를 로딩하기 위해 깔끔하게 재조회
    query = (
        select(models.Course)
        .options(
            selectinload(models.Course.instructor),
            selectinload(models.Course.category)
        )
        .where(models.Course.id == new_course.id)
    )
    
    result = await db.execute(query)
    created_course = result.scalar_one_or_none()
    
    return created_course

@router.get("", response_model=schemas.PageResponse[schemas.CourseResponse])
async def read_courses(
    page: int = 1,
    size: int = 20,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * size
    
    # 쿼리 구성
    query = select(models.Course).options(
        selectinload(models.Course.instructor),
        selectinload(models.Course.category)
    )
    
    if keyword:
        query = query.where(models.Course.title.ilike(f"%{keyword}%"))
    
    # 개수 카운트
    count_query = select(func.count(models.Course.id))
    if keyword:
        count_query = count_query.where(models.Course.title.ilike(f"%{keyword}%"))
    
    count_res = await db.execute(count_query)
    total_elements = count_res.scalar() or 0
    
    # 페이징 조회
    query = query.offset(skip).limit(size)
    result = await db.execute(query)
    courses = result.scalars().all()
    
    return {
        "content": courses,
        "page": page,
        "size": size,
        "total_elements": total_elements,
        "total_pages": (total_elements + size - 1) // size if total_elements > 0 else 0
    }

@router.get("/search/query", response_model=List[schemas.CourseResponse])
async def search_courses_explicit(keyword: str, db: AsyncSession = Depends(get_db)):
    query = select(models.Course).options(
        selectinload(models.Course.instructor),
        selectinload(models.Course.category)
    ).where(models.Course.title.ilike(f"%{keyword}%"))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/filter/recent", response_model=List[schemas.CourseResponse])
async def get_recent_courses(limit: int = 5, db: AsyncSession = Depends(get_db)):
    query = select(models.Course).options(
        selectinload(models.Course.instructor),
        selectinload(models.Course.category)
    ).order_by(models.Course.id.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{course_id}", response_model=schemas.CourseResponse)
async def get_course_detail(course_id: int, db: AsyncSession = Depends(get_db)):
    query = select(models.Course).options(
        selectinload(models.Course.instructor),
        selectinload(models.Course.category)
    ).where(models.Course.id == course_id)
    result = await db.execute(query)
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.put("/{course_id}", response_model=schemas.CourseResponse)
async def update_course(
    course_id: int,
    course_update: schemas.CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = select(models.Course).where(models.Course.id == course_id)
    result = await db.execute(query)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.instructor_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    for key, value in course_update.model_dump(exclude_unset=True).items():
        setattr(course, key, value)
    await db.commit()
    
    # 수정 후 조회도 selectinload 사용
    query = select(models.Course).options(
        selectinload(models.Course.instructor),
        selectinload(models.Course.category)
    ).where(models.Course.id == course_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

@router.delete("/{course_id}", status_code=204)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = select(models.Course).where(models.Course.id == course_id)
    result = await db.execute(query)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.instructor_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db.delete(course)
    await db.commit()
    return None