# System Architecture

## 1. Tech Stack
- **Backend Framework**: FastAPI (Python 3.10)
- **Database**: MySQL 8.0 (Async SQLAlchemy ORM)
- **Cache & Rate Limiting**: Redis (Global IP Rate Limit Middleware)
- **Authentication**: JWT + Social Login (Google / Firebase)
- **Migration**: Alembic (alembic upgrade head)
- **Seed Data**: Async seed script (`/seed/seed_data.py`) generating 200+ rows
- **Containerization**: Docker & Docker Compose

## 2. System Flow
1. Client Request → FastAPI
2. Global Middleware
   - Rate Limit (Redis)
   - Logging (method/path/status/latency)
   - CORS (production에서는 허용 Origin 제한 권장)
3. Auth
   - Local login: email/password → JWT 발급
   - Social login: Google/Firebase token 검증 → 서비스 JWT 발급
4. Business Logic → Router/Service
5. DB Interaction → Async SQLAlchemy → MySQL
6. Standardized JSON Response (success / error)

## 3. Deployment (Docker Compose)
- Backend: `:8000`
- MySQL: `:3307` (host) → `3306` (container)
- Redis: `:6380` (host) → `6379` (container)

## 4. Directory Structure
- `src/routers`: API endpoints
- `src/models.py`: SQLAlchemy models
- `src/schemas.py`: Pydantic validation schemas
- `src/security.py`: JWT + password hashing
- `migrations/`: Alembic revisions
- `seed/`: Seed scripts (200+ rows)
- `tests/`: pytest tests
