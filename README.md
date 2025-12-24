# 🎓 WSD Term Project – Online Course Platform Backend

본 프로젝트는 **FastAPI 기반 온라인 강의 플랫폼 백엔드 시스템**으로,  
사용자 인증, 강의/카테고리 관리, 수강 신청, 리뷰, 파일 업로드, 관리자 통계 기능을 포함합니다.  
Docker & Docker Compose 기반 컨테이너 환경에서 배포되었습니다.

---

## 📌 주요 기능 요약

- JWT 기반 사용자 인증 (일반 / 관리자)
- Google Firebase OAuth 로그인
- 강의(Course), 강의차시(Lecture), 카테고리(Category) CRUD
- 수강 신청 및 취소 (Enrollment)
- 강의 리뷰 작성 / 수정 / 삭제
- 파일 업로드 및 다운로드
- 관리자 전용 통계 API
- Redis 캐시, MySQL DB 연동
- Swagger 기반 API 문서 자동 생성

---

## 🧱 기술 스택

| 구분 | 기술 |
|---|---|
| Backend | FastAPI (Python 3.10) |
| Frontend | Streamlit |
| Database | MySQL 8.0 |
| Cache | Redis |
| Auth | JWT, Firebase OAuth |
| ORM | SQLAlchemy |
| Infra | Docker, Docker Compose |
| Docs | Swagger (OpenAPI) |
| Test | Pytest |
| API Test | Postman |

---

## 🚀 배포 및 서버 정보 (Deployment Info)

이 프로젝트는 **Docker & Docker Compose**를 사용하여  
프론트엔드, 백엔드, DB, 캐시 서버를 각각 독립 컨테이너로 구성했습니다.

### 🛠 시스템 아키텍처 및 포트 구성

| 서비스 | 스택 | 내부 포트 | 외부 포트 | 설명 |
|---|---|---|---|---|
| Frontend | Streamlit | 8501 | **13027** | 사용자 웹 UI |
| Backend | FastAPI | 8000 | **17027** | REST API |

---

## 🌐 서비스 접속 주소

- **Frontend**  
  👉 http://113.198.66.68:13027/

- **Backend API (Swagger)**  
  👉 http://113.198.66.68:17027/docs

---

## 📦 설치 및 실행 방법

### 1️⃣ 필수 조건
- Docker
- Docker Compose

### 2️⃣ 환경 변수 및 보안 파일
- `.env` 파일 (저장소에 포함되지 않음)
- Firebase 인증 키 파일:
serviceAccountKey.json

shell
코드 복사

> ⚠️ 보안상 `.env` 및 Firebase 키는 GitHub에 커밋되지 않습니다.

### 3️⃣ 컨테이너 빌드 및 실행

```bash
docker-compose up -d --build
```

---

## 🔐 인증 방식
JWT Access / Refresh Token

Authorization Header 사용

css
코드 복사
Authorization: Bearer {access_token}
Firebase OAuth 로그인 지원

---

## 📚 API 엔드포인트 개요 (30+)
🔑 Auth
POST /auth/signup

POST /auth/login

POST /auth/google

POST /auth/refresh

POST /auth/logout

👤 Users
GET /users/me

PUT /users/me/password

DELETE /users/me

GET /admin/users

GET /admin/users/{id}

DELETE /admin/users/{id}

🗂 Categories
POST /categories (ADMIN)

GET /categories

PUT /categories/{id}

DELETE /categories/{id}

🎓 Courses
POST /courses

GET /courses

GET /courses/{id}

PUT /courses/{id}

DELETE /courses/{id}

GET /courses/search

GET /courses/recent

📖 Lectures
POST /courses/{id}/lectures

GET /courses/{id}/lectures

PUT /lectures/{id}

DELETE /lectures/{id}

📝 Reviews
POST /courses/{id}/reviews

GET /courses/{id}/reviews

PUT /reviews/{id}

DELETE /reviews/{id}

🎟 Enrollments
POST /enrollments

GET /enrollments/me

DELETE /enrollments/{id}

📁 Files
POST /files/upload

GET /files/{filename}

📊 Admin Stats
GET /admin/stats

GET /admin/stats/daily

---

## 🧪 테스트
Pytest 기반 테스트 코드 포함

주요 인증/엔드포인트 테스트 완료

bash
코드 복사
pytest
📮 Postman
Postman Collection 포함

pgsql
코드 복사
wsd_tp.postman_collection.json
Swagger와 함께 API 테스트 가능

---

## 🌱 Seed 데이터
seed_data.py 제공

대량 데이터 삽입용 스크립트 포함

강의/유저/카테고리 데이터 생성

---

## ⚠️ 보안 유의 사항
.env, Firebase Key 파일은 GitHub에 포함되지 않음

JWT Secret은 환경 변수로 관리

관리자 API는 ADMIN 권한만 접근 가능

---