# 작업 이어가기 (Resume) — Keepy

> 다음 세션에서 이 파일을 먼저 읽으면 현재 상태와 다음 할 일을 파악할 수 있습니다.
> 마지막 작업 기준일: 2026-06-13

## ⏭️ 내일 바로 할 일 (2026-06-13에 하다 만 것)

- **AI 스팸 헌터가 이제 본문까지 읽도록 개선함** (`app/services/ai_spam_classifier.py`).
  - 변경: 게시판 목록에서 제목+링크 수집 → 각 글 상세페이지 방문해 본문 미리보기(500자) 추출 → 제목+본문(300자)을 GPT에 전달. 한 번에 최대 25개 글 처리(`MAX_POSTS`). `javascript:` 링크 스킵.
  - 상태: **코드 작성+문법검증(py_compile) 통과까지만 함. 실제 게시판으로 테스트 안 함.**
  - **내일 할 일: 진짜 병원 게시판 URL로 `/spam/scan` 돌려서 (1) 본문이 제대로 추출되는지, (2) 스팸 판별이 맞는지 확인.** (실제 스팸 글 있는 게시판이면 베스트)
  - 로컬 실행: `uvicorn app.main:app --reload` 후 `/app`에서 스팸 관리 화면, 또는 API `POST /api/spam/scan`.

---


## 현재 상태 한눈에

- **배포 구조 결정**: A안 = **단일 Docker 컨테이너**. FastAPI가 랜딩(`/`)+React앱(`/app`)+API(`/api`)를 전부 서빙. (Vercel 분리 구조는 폐기 예정)
- **GitHub**: `whalez0416/keepy2.0`
  - `main` (`99e863e`) = 옛 코드 (라이브에 떠있을 수 있음, 보안취약 버전)
  - **`production-refactor` (`294d8ae`) = 이번 대규모 리팩터링 전부** ← 아직 main에 머지/배포 안 됨
- **로컬 `.env`**: 실제 OPENAI_API_KEY, SECRET_KEY, MASTER_EMAIL/PASSWORD 채워져 있음 (git 제외됨)

## 완료된 작업 (production-refactor 브랜치)

1. **보안**: 무인증 레거시 UI(app/ui/views.py) 제거, `/api/test/trigger` 삭제, SECRET_KEY·마스터계정 env화(운영에서 SECRET_KEY 없으면 부팅 실패), 고객 비밀번호 Fernet 암호화(`app/utils/crypto.py`), discovery 인증 추가, CORS/DEBUG 로깅 정리
2. **AI 스팸**: Gemini→OpenAI(GPT, gpt-4o-mini) 교체. 스케줄러 연결 + 탐지 시 이메일 알림 (탐지+알림만, 자동삭제 X). 라이브 테스트로 정상 판별 확인됨.
3. **결제/요금제 제거**: billing.py·BillingView·PricingView·PaymentSuccessView 삭제, 메뉴/라우트 정리 (B2B 수동 발급 모델)
4. **SSL**: 거짓 자동갱신(time.sleep 후 "성공") 제거 → 만료 임박 감지+알림으로 정직화
5. **배포 가능화**: Dockerfile 멀티스테이지(Node 빌드→Python), `playwright install`, Postgres 드라이버(psycopg2)·email-validator 추가, DB는 DATABASE_URL로 SQLite/Postgres 양립, 스케줄러 단일 프로세스 락
6. **계정 흐름**: 비밀번호 변경 기능 실연동(`POST /api/auth/change-password` + SettingsView)
7. **영업 랜딩**(app/static/keepy_landing.html): 문의폼을 실제 `/api/leads`에 연결, 과장/불일치 문구 수정(Gemini→GPT, SSL, 스팸), 테스트 배너 스크립트 제거, 헤더에 로그인 링크
8. **라우팅**: `/`=랜딩, `/app`=React(basename=/app), 401시 /app/login
9. **문서**: `DEPLOY.md`(무료→유료 배포 가이드) 추가

## 다음에 할 일 (우선순위)

1. **(배포 시작)** `DEPLOY.md` 따라: GitHub 연결됨 → Supabase Postgres 생성 → Render Docker 웹서비스 → 환경변수 세팅
   - ⚠️ Render 환경변수(SECRET_KEY, MASTER_*, OPENAI_API_KEY, DATABASE_URL, SMTP_*)를 **먼저 세팅한 뒤** `production-refactor`를 `main`에 머지해야 라이브가 안 깨짐
2. 기존 Vercel/Render 정리 (단일 컨테이너로 일원화)
3. (실고객 받으면) Render 무료→Starter($7) 전환 (무료는 잠들어서 감시 멈춤)
4. (선택) 기존 테스트 DB/계정 초기화, 카카오 알림톡, 실시간 차트

## 남아있는 알려진 한계 (이번 범위 밖)

- RBAC(viewer/editor 역할)는 정의만 있고 강제 안 됨 — B2B 1계정/고객 모델이라 당장 영향 적음
- 설정화면의 SMTP/카카오 등은 제거됨(가짜였음). SMTP는 env로 관리.
- SSL "실제" 자동갱신은 미구현(고객 서버 ACME 권한 필요). 현재는 만료 알림까지.

## 개발/테스트 메모

- 파이썬: `C:\python\keepy new\.venv` (이 폴더 기준 `python`이 이 venv를 가리킴)
- 로컬 실행: `uvicorn app.main:app --reload` → 랜딩 `:8000/`, 앱 `:8000/app`
- 프론트 개발: `cd frontend && npm run dev` → `:5173/app`
- 마스터 로그인(로컬): master@keepy.com / (로컬 .env의 MASTER_PASSWORD)
- git push 시: 이 PC는 TLS 가로채기로 인해 `git -c http.sslVerify=false push ...` 필요 (자격증명은 캐시됨)
