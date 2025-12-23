# Database Schema

## 1. Users (사용자)
- **id**: PK, Integer, Auto Increment
- **email**: Unique String (Indexed)
- **hashed_password**: String (Bcrypt)
- **role**: Enum ('USER', 'ADMIN')
- **provider**: String(20) NOT NULL (e.g., LOCAL / GOOGLE / FIREBASE)
- **created_at / updated_at**: DateTime (server_default now())

## 2. Categories (카테고리)
- **id**: PK
- **name**: Unique String (Indexed)

## 3. Courses (강의)
- **id**: PK
- **instructor_id**: FK (Users)
- **category_id**: FK (Categories)
- **title**: String (Indexed for search)
- **description**: Text
- **price**: Integer
- **level**: String (BEGINNER / INTERMEDIATE / ADVANCED)
- **thumbnail_url**: String (nullable)
- **is_public**: Boolean (공개 여부)
- **created_at / updated_at**: DateTime (server_default now())

## 4. Lectures (강의 회차/커리큘럼)
- **id**: PK
- **course_id**: FK (Courses)
- **title**: String
- **video_url**: String
- **order_index**: Integer (Sort key)

## 5. Enrollments (수강 신청)
- **id**: PK
- **user_id**: FK (Users, Indexed)
- **course_id**: FK (Courses, Indexed)
- **status**: String ('ACTIVE', 'CANCELED')
- **enrolled_at**: DateTime (server_default now())

## 6. Reviews (수강평)
- **id**: PK
- **user_id**: FK (Users)
- **course_id**: FK (Courses)
- **rating**: Integer (1~5)
- **comment**: Text
- **created_at**: DateTime (server_default now())
