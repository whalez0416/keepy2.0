# ---- Stage 1: React 프론트엔드 빌드 ----
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python 백엔드 (+ 프론트 정적 서빙) ----
# 3.11 사용: 로컬 검증 환경과 일치 + Pillow 12 등 최신 의존성이 Python 3.10+를 요구함.
FROM python:3.11-slim

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
# 워커 1개로 고정한다. 이유:
#  1) Playwright(Chromium)는 점검 시 150~250MB를 쓰는데, 워커별 동시성 제한
#     (browser_pool 세마포어)이 프로세스마다 따로라 워커 2개면 크롬 2개가 동시에
#     떠 512MB(starter)를 초과 → 컨테이너 OOM-kill 위험이 가장 컸다.
#  2) 빈 DB 첫 부팅 시 두 워커가 동시에 create_all 하다 한 워커가 충돌하던 경쟁도 사라진다.
# 단일 워커로도 비동기(uvicorn) 처리라 소수 고객 트래픽에는 충분하다.
CMD ["gunicorn", "app.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
