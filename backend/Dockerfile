# backend/Dockerfile

# 1. Python 3.10 Slim version (Lightweight base image)
FROM python:3.10-slim

# 2. Set working directory inside container
WORKDIR /app

# 3. Install system dependencies
# (gcc, pkg-config, libmysqlclient-dev are required for mysqlclient & other C-extensions)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements first (Layer caching optimization)
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
# [중요] 이 명령어가 'serviceAccountKey.json' 파일도 함께 컨테이너의 /app 으로 복사합니다.
COPY . .

# 7. Run the application
# Use 'src.main:app' assuming your main entry point is src/main.py
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]