# backend/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# [안전] 이제 .dockerignore 덕분에 키 파일은 복사되지 않습니다.
COPY . .

# [변경] 포트 8080으로 통일, --reload 제거 (실서버용)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]