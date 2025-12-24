# frontend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Streamlit 기본 포트 8501 열기
EXPOSE 8501

# 실행 명령어
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]