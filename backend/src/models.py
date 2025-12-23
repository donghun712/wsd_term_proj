# backend/src/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

# database.py에 있는 Base 사용 (중요)
from src.database import Base


# --- Enums ---
class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


# --- Models ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # DB 스키마 기준: varchar(100) + unique + not null
    # (네 기존은 255였는데, 더 작게 맞춰도 되고 255 유지해도 동작은 함)
    email = Column(String(100), unique=True, index=True, nullable=False)

    hashed_password = Column(String(255), nullable=False)

    # ✅ DB 스키마에 provider NOT NULL 존재 -> 모델에도 반드시 필요
    # varchar(20) NOT NULL DEFAULT 'LOCAL' 로 맞춤
    provider = Column(String(20), nullable=False, server_default="LOCAL")

    # role: enum('USER','ADMIN') NOT NULL
    role = Column(
        Enum(UserRole, native_enum=False, create_constraint=False, length=50),
        nullable=False,
        server_default="USER",
        default=UserRole.USER,
    )

    # DB 스키마: created_at / updated_at 기본 now()
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 관계 설정
    courses = relationship("Course", back_populates="instructor")
    enrollments = relationship("Enrollment", back_populates="user")
    reviews = relationship("Review", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    courses = relationship("Course", back_populates="category")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, default=0)
    level = Column(String(50), default="BEGINNER")
    thumbnail_url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"))
    instructor_id = Column(Integer, ForeignKey("users.id"))

    category = relationship("Category", back_populates="courses")
    instructor = relationship("User", back_populates="courses")
    lectures = relationship("Lecture", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course")
    reviews = relationship("Review", back_populates="course")


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    video_url = Column(String(500), nullable=False)
    order_index = Column(Integer, default=1)

    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="lectures")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), default="ACTIVE")
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

    user = relationship("User", back_populates="reviews")
    course = relationship("Course", back_populates="reviews")
