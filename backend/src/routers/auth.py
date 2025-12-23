from datetime import timedelta
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from src import models, schemas, security, config
from src.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = config.settings

# --- Firebase 초기화 ---
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("/app/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin Initialized!")
except Exception as e:
    print(f"⚠️ Firebase Init Failed: {e}")

@router.post("/signup", response_model=schemas.UserResponse, status_code=201)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        email=user.email,
        hashed_password=security.get_password_hash(user.password),
        role=user.role,
        provider="LOCAL",
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalars().first()

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Access & Refresh 토큰 생성
    access_token = security.create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.post("/google", response_model=schemas.Token)
async def google_login(req: schemas.GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded_token = firebase_auth.verify_id_token(req.token)
        email = decoded_token.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid Google Token (No Email)")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google Auth Failed: {str(e)}")

    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalars().first()

    if not user:
        random_password = secrets.token_urlsafe(16)
        user = models.User(
            email=email,
            hashed_password=security.get_password_hash(random_password),
            role=models.UserRole.USER,
            provider="GOOGLE", 
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = security.create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(req: schemas.TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """[수정] 리프레시 토큰을 검증하여 새로운 액세스 토큰 발급"""
    try:
        payload = jwt.decode(req.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        # 리프레시 토큰 전용 타입인지 확인
        if email is None or payload.get("type") != "refresh":
            raise JWTError
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = security.create_access_token(data={"sub": user.email, "role": user.role.value})
    
    return {
        "access_token": new_access_token, 
        "refresh_token": req.refresh_token, 
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout():
    """로그아웃 (클라이언트 측에서 토큰 폐기 유도)"""
    return {"message": "Successfully logged out"}