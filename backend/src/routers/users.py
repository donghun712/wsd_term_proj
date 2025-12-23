from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database import get_db
from src import models, schemas, security

router = APIRouter(prefix="/users", tags=["Users (Management)"])

# --- [공개 API] 인증이 필요 없는 엔드포인트 ---

@router.get("/check-email")
async def check_email_exists(
    email: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    [신규] 이메일 중복 확인
    - 회원가입 전 단계이므로 Header에 Authorization 토큰이 없어도 200을 반환해야 합니다. [cite: 7, 14]
    """
    result = await db.execute(select(models.User).where(models.User.email == email))
    exists = result.scalars().first() is not None
    return {"email": email, "exists": exists}

# --- [보호된 API] 일반 유저 인증 필요 ---

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user

@router.post("/me/password", status_code=200)
async def change_password(
    body: schemas.PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    if not security.verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.hashed_password = security.get_password_hash(body.new_password)
    await db.commit()
    return {"message": "Password updated successfully"}

@router.delete("/me", status_code=204)
async def delete_me(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    await db.delete(current_user)
    await db.commit()
    return

# --- [보호된 API] 관리자(ADMIN) 전용 ---

@router.get("", response_model=List[schemas.UserResponse])
async def read_all_users(
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin)
):
    result = await db.execute(select(models.User))
    return result.scalars().all()

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def read_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin)
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_user_by_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: models.User = Depends(security.get_current_admin)
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return