import time
import logging
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Union

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

import redis.asyncio as redis
from src.config import settings
# [수정] files 추가
from src.routers import auth, users, courses, categories, lectures, enrollments, reviews, stats, files, admin
from fastapi.staticfiles import StaticFiles

# --- 로거 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

redis_client = None

# --- 에러 응답 공통 포맷 ---
def create_error_response(status_code: int, message: str, code: str = None, details: Union[dict, str] = None, path: str = ""):
    if code is None:
        error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_FAILED",
            429: "TOO_MANY_REQUESTS",
            500: "INTERNAL_SERVER_ERROR"
        }
        code = error_codes.get(status_code, "UNKNOWN_ERROR")

    return JSONResponse(
        status_code=status_code,
        content={
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "path": path,
            "status": status_code,
            "code": code,
            "message": message,
            "details": details
        }
    )

# --- 미들웨어 ---
class LoggingAndRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        
        # 1. Rate Limiting
        if redis_client:
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}"
            limit = 60
            expire_time = 60
            
            try:
                async with redis_client.pipeline(transaction=True) as pipe:
                    await pipe.incr(key)
                    await pipe.ttl(key)
                    result = await pipe.execute()
                
                request_count = result[0]
                if result[1] == -1:
                    await redis_client.expire(key, expire_time)
                
                if request_count > limit:
                    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                    return create_error_response(
                        status_code=429, 
                        message="Rate limit exceeded", 
                        code="TOO_MANY_REQUESTS",
                        path=path
                    )
            except Exception as e:
                logger.error(f"Redis Error: {str(e)}")

        # 2. 로깅 및 에러 핸들링
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(f"{request.method} {path} - {response.status_code} - {process_time:.4f}s")
            return response
        except Exception as e:
            logger.error(f"Server Error: {str(e)}")
            logger.error(traceback.format_exc())
            return create_error_response(
                status_code=500, 
                message="Internal Server Error", 
                details=str(e),
                path=path
            )

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL, 
            encoding="utf-8", 
            decode_responses=True,
            socket_connect_timeout=3
        )
        await redis_client.ping()
        logger.info("✅ Redis Connected!")
    except Exception as e:
        logger.warning(f"❌ Redis Connection Failed: {e}")
        
    yield
    
    if redis_client:
        await redis_client.close()
        logger.info("🛑 Redis Closed.")

# --- App Init ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)
app.mount(
    "/static", 
    StaticFiles(directory="static"), 
    name="static"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingAndRateLimitMiddleware)

# --- Exception Handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return create_error_response(
        status_code=exc.status_code,
        message=exc.detail,
        path=request.url.path
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation Failed",
        details=str(exc),
        path=request.url.path
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database Error: {str(exc)}")
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Database Error",
        code="DATABASE_ERROR",
        path=request.url.path
    )

# --- 라우터 등록 ---
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(categories.router, prefix=settings.API_V1_STR)
app.include_router(courses.router, prefix=settings.API_V1_STR)
app.include_router(lectures.router, prefix=settings.API_V1_STR)
app.include_router(enrollments.router, prefix=settings.API_V1_STR)
app.include_router(reviews.router, prefix=settings.API_V1_STR)
app.include_router(stats.router, prefix=settings.API_V1_STR)
app.include_router(files.router, prefix=settings.API_V1_STR) # [추가]
app.include_router(admin.router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "version": "1.0.0", "uptime": datetime.utcnow().isoformat()}

@app.get("/", tags=["System"])
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}