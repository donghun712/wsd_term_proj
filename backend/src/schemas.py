from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Generic, TypeVar, Dict, Any
from datetime import datetime
from src.models import UserRole

# --- Generic Type for Pagination ---
T = TypeVar("T")

# --- Common Response ---
class ResponseBase(BaseModel):
    message: str = "Success"

# --- Error Response Schema ---
class ErrorDetail(BaseModel):
    timestamp: datetime
    path: str
    status: int
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

# --- User Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="비밀번호는 8자 이상이어야 합니다.")
    role: UserRole = UserRole.USER

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    role: Optional[UserRole] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    refresh_token: str  # 리프레시 토큰 포함
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str  # 재발급 요청용 스키마

# --- Google Login Schema ---
class GoogleLoginRequest(BaseModel):
    token: str

# --- Category Schemas ---
class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)

class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# --- Course Schemas ---
class CourseCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: Optional[str] = None
    price: int = Field(ge=0, default=0)
    level: str = "BEGINNER"
    category_id: Optional[int] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    level: Optional[str] = None
    is_public: Optional[bool] = None

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: int
    level: str
    thumbnail_url: Optional[str]
    category_id: Optional[int]
    instructor_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    category: Optional[CategoryResponse] = None
    instructor: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# --- Lecture Schemas ---
class LectureCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    video_url: str = Field(pattern=r"^https?://")
    order_index: int = 1

class LectureUpdate(BaseModel):
    title: Optional[str] = None
    video_url: Optional[str] = None
    order_index: Optional[int] = None

class LectureResponse(BaseModel):
    id: int
    title: str
    video_url: str
    order_index: int
    course_id: int

    class Config:
        from_attributes = True

# --- Enrollment Schemas ---
class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    status: str
    enrolled_at: datetime
    
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True

# --- Review Schemas ---
class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=5, max_length=500)

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=5, max_length=500)

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    rating: int
    comment: str
    created_at: datetime
    
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# --- Stats Schemas ---
class SystemStats(BaseModel):
    total_users: int
    total_courses: int
    total_reviews: int
    total_enrollments: int  # enrollments 추가됨

# --- Pagination Schema ---
class PageResponse(BaseModel, Generic[T]):
    content: List[T]
    page: int
    size: int
    total_elements: int
    total_pages: int
    
    class Config:
        from_attributes = True