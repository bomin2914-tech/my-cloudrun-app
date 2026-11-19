# ==============================================================================
# Google Cloud Run 배포용 Dockerfile (BFS & DFS 백엔드)
# Base Image: Python 3.11 Slim
# ==============================================================================
FROM python:3.11-slim

# 표준 출력/에러 버퍼링 방지 및 포트 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# 의존성 복사 및 설치 (캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY . .

EXPOSE 8080

# Cloud Run 권장 실행 명령어 (PID 1 신호 전파 최적화)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
