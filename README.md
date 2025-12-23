# 🎓 Online Learning Management System (LMS) API

FastAPI, MySQL, Redis, Docker를 기반으로 구축된 온라인 강의 플랫폼 백엔드 API입니다.
사용자 관리, 강의(Course) 및 커리큘럼(Lecture) 관리, 수강 신청, 리뷰, 통계 기능을 제공하며,
Google Firebase 소셜 로그인과 JWT 기반 인증 시스템을 갖추고 있습니다.

## 🛠 기술 스택 (Tech Stack)

* **Framework:** FastAPI (Python 3.10)
* **Database:** MySQL 8.0 (Async SQLAlchemy + Alembic)
* **Cache & Rate Limit:** Redis
* **Authentication:** JWT (Access Token) + Firebase Auth (Google Login)
* **Container:** Docker, Docker Compose
* **Testing:** Pytest (AsyncIO)

---

## 🚀 실행 방법 (Installation & Running)

이 프로젝트는 Docker Compose를 통해 한 번의 명령어로 실행할 수 있습니다.

### 1. 환경 변수 설정
`.env.example` 파일을 복사하여 `.env` 파일을 생성합니다. (Google Login을 사용하려면 `backend/` 폴더에 `serviceAccountKey.json`이 필요합니다.)

### 2. 서버 실행
프로젝트 루트 경로에서 아래 명령어를 입력합니다.

```bash
docker compose up -d --build