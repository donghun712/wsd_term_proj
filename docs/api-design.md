# REST API Design Specification

## 1. General Conventions
- **Base URL**: `/api/v1`
- **Protocol**: HTTP/1.1 (HTTPS Recommended)
- **Content-Type**: `application/json; charset=utf-8`
- **Date Format**: ISO 8601 (e.g., `2023-12-23T12:00:00Z`)

## 2. Authentication & Authorization
본 프로젝트는 **JWT (JSON Web Token)** 기반의 Statless 인증을 사용합니다.

- **Header**: `Authorization: Bearer <Access Token>`
- **Roles**:
  - `USER`: 일반 사용자 (수강신청, 리뷰 작성, 본인 정보 관리)
  - `ADMIN`: 관리자 (카테고리 관리, 전체 통계 조회, 강의 강제 삭제)
- **Flow**:
  1. `POST /auth/login` 또는 `/auth/google` 로 인증
  2. 서버에서 Access Token (유효기간 30분) 발급
  3. API 요청 시 헤더에 토큰 포함

## 3. Standard Response Formats

### 3.1. Success Response (Single Resource)
```json
{
  "id": 1,
  "title": "FastAPI Master Class",
  "price": 50000,
  "created_at": "2023-12-23T10:00:00Z"
}
```

### 3.2. Success Response (Pagination)

목록 조회 시 페이지네이션 메타데이터를 포함합니다.
{
  "content": [
    { "id": 1, "name": "Python" },
    { "id": 2, "name": "Java" }
  ],
  "page": 1,
  "size": 20,
  "total_elements": 55,
  "total_pages": 3
}

### 3.3. Error Response (Standardized)

모든 에러 상황에서 일관된 포맷을 유지합니다.
{
  "timestamp": "2023-12-23T12:00:00Z",
  "path": "/api/v1/auth/login",
  "status": 401,
  "code": "UNAUTHORIZED",
  "message": "Incorrect email or password",
  "details": null
}

## 4. Status & Error Codes
본 프로젝트는 상황에 따라 12종 이상의 HTTP Status Code를 구분하여 사용합니다.

| Status Code | Error Code | Description |
| :--- | :--- | :--- |
| **200** | - | 요청 성공 (OK) |
| **201** | - | 리소스 생성 성공 (Created) |
| **204** | - | 내용 없는 성공 (No Content) - 삭제 등 |
| **400** | `BAD_REQUEST` | 잘못된 요청 문법 |
| **400** | `VALIDATION_FAILED` | 입력값 유효성 검사 실패 |
| **401** | `UNAUTHORIZED` | 인증 실패 (토큰 없음/만료) |
| **401** | `TOKEN_EXPIRED` | 토큰 유효기간 만료 |
| **403** | `FORBIDDEN` | 권한 없음 (일반 유저가 관리자 API 접근) |
| **404** | `NOT_FOUND` | 리소스를 찾을 수 없음 |
| **409** | `CONFLICT` | 리소스 충돌 (이메일 중복, 이미 수강신청됨) |
| **422** | `UNPROCESSABLE_ENTITY` | Pydantic 스키마 검증 실패 |
| **429** | `TOO_MANY_REQUESTS` | 요청 횟수 초과 (Rate Limit) |
| **500** | `INTERNAL_SERVER_ERROR` | 서버 내부 로직 오류 |
| **503** | `SERVICE_UNAVAILABLE` | DB 또는 Redis 연결 실패 |


## 5. API Endpoints Overview
Auth (인증)
POST /auth/signup: 회원가입
POST /auth/login: 이메일 로그인
POST /auth/google: 구글 소셜 로그인
POST /auth/refresh: 토큰 갱신
POST /auth/logout: 로그아웃

Users (사용자)
GET /users/me: 내 정보 조회
PATCH /users/me/password: 비밀번호 변경
DELETE /users/me: 회원 탈퇴
GET /users/check-email: 이메일 중복 확인 (신규)

Courses (강의)
GET /courses: 강의 목록 검색 (Paging, Sort, Keyword)
POST /courses: 강의 개설 (Instructor)
GET /courses/{id}: 강의 상세 조회
PUT /courses/{id}: 강의 정보 수정
DELETE /courses/{id}: 강의 삭제
GET /courses/search/query: 강의 명시적 검색 (신규)
GET /courses/filter/recent: 최신 강의 Top 5 (신규)

Lectures (커리큘럼)
GET /courses/{id}/lectures: 강의 커리큘럼 조회
POST /courses/{id}/lectures: 회차 추가

Enrollments (수강신청)
POST /courses/{id}/enroll: 수강신청
GET /enrollments/me: 내 학습 목록 조회

Reviews (수강평)
POST /courses/{id}/reviews: 수강평 작성
GET /courses/{id}/reviews: 강의별 수강평 조회

Files (파일 업로드)
POST /files/upload: 이미지 업로드 (신규)
GET /files/{filename}: 이미지 조회 (신규)

Categories & Admin
GET /categories: 카테고리 목록 조회
POST /categories: 카테고리 추가 (Admin)
GET /users: 전체 회원 조회 (Admin)
GET /users/{id}: 회원 상세 조회 (Admin)
DELETE /users/{id}: 회원 강제 추방 (Admin)
GET /admin/stats: 전체 시스템 통계 (Admin)
GET /admin/stats/daily: 일별 가입/방문 통계 (Admin/신규)

## 6. Cross-Cutting Concerns (공통 처리)

CORS

개발 환경: 모든 Origin 허용
배포 환경: 허용 Origin 제한 가능 (환경변수 기반 설정)

Rate Limiting
Redis 기반 전역 IP Rate Limit 적용
과도한 요청 시 429 TOO_MANY_REQUESTS 반환

Validation
모든 요청 DTO는 Pydantic 스키마로 검증
검증 실패 시 422 UNPROCESSABLE_ENTITY

Health Check
GET /health
DB / Redis 연결 상태 확인 (200 or 503)