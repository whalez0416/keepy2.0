# ---- Stage 1: React 프론트엔드 빌드 ----
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python 백엔드 (+ 프론트 정적 서빙) ----
FROM python:3.9-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# 파이썬 환경 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저(Chromium) 및 OS 의존 라이브러리 설치
# 이게 없으면 홈페이지/폼/비주얼/스팸 점검이 런타임에 모두 실패함.
RUN playwright install --with-deps chromium

# 애플리케이션 소스 복사
COPY . .

# 1단계에서 빌드한 프론트엔드 결과물 복사 → FastAPI가 / 에서 서빙
COPY --from=frontend-build /frontend/dist ./frontend/dist

# 포트 개방
EXPOSE 8000

# Gunicorn으로 FastAPI 실행 (Uvicorn Worker).
# 스케줄러는 앱 내부 락으로 워커 1개에서만 동작하므로 워커 수를 늘려도 중복 실행되지 않음.
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
