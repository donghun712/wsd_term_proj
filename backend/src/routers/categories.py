# backend/src/routers/categories.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src import models, schemas, security
from src.database import get_db

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("", response_model=schemas.CategoryResponse, status_code=201)
async def create_category(
    category_data: schemas.CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """카테고리 생성 (관리자 전용)"""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # 중복 체크
    result = await db.execute(select(models.Category).where(models.Category.name == category_data.name))
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Category already exists")
    
    new_category = models.Category(name=category_data.name)
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category

@router.get("", response_model=List[schemas.CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """카테고리 목록 조회 (전체 공개)"""
    result = await db.execute(select(models.Category))
    return result.scalars().all()