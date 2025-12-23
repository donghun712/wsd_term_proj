# backend/src/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LMS API"
    API_V1_STR: str = "/api/v1"
    
    # 보안 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "TEST_SECRET_KEY_1234")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+aiomysql://user:password@localhost:3306/lms_db")
    
    # Redis 설정
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # [수정됨] 에러 원인이었던 관리자 계정 정보 추가
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "password123")

    class Config:
        env_file = ".env"
        case_sensitive = True
        # [중요] 정의되지 않은 환경변수가 있어도 에러 내지 말고 무시해라 (서버 죽음 방지)
        extra = "ignore" 

settings = Settings()