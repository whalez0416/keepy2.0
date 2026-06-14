# 작업 이어가기 (Resume) — Keepy

> 다음 세션에서 이 파일을 먼저 읽으면 현재 상태와 다음 할 일을 파악할 수 있습니다.
> 마지막 작업 기준일: 2026-06-14

## ✅ 2026-06-14에 한 것: AI 스팸 헌터 실게시판 테스트 + 버그수정 완료

실제 병원 게시판(`https://minhospital.co.kr/index.php/board/list/counsel/101`, 킴스큐류 CMS)으로 테스트하며 `app/services/ai_spam_classifier.py` 다음을 고침:

1. **글 추출 0개 문제** → `td.noticetitle a` 셀렉터 추가 + 이름 셀렉터 다 실패 시 href 패턴 폴백(`_extract_posts_by_href`, `POST_HREF_PATTERNS`: /board/view/·passwordform·wr_id= 등) 추가. 이제 비밀글(javascript:passwordform)도 제목은 수집.
2. **글 중복 수집**(게시판이 목록 2번 렌더) → (제목,href) 기준 중복 제거 추가.
3. **본문 추출이 사이트 메뉴를 긁어옴** → 본문 셀렉터에 `.contents`, `.re_contents`(킴스큐류) 추가. 공개글은 본문 정상 추출, 비밀글은 본문 없음(정상).
4. **정상 글을 스팸 오판(false positive)** ("검강검진 에약변경"=오타 정상글 등) → 프롬프트를 보수적으로 재작성(기본=정상, 명백한 상업/불법 광고만 스팸; 오타·짧은제목·반말 문의는 정상).
5. **진짜 스팸을 놓치는 버그** → 원인: `confidence` 의미 미정의로 GPT가 값을 뒤집어 답함(is_spam=true인데 confidence=0.0 → 필터 통과). 프롬프트에 confidence 정의(스팸일 확률, is_spam과 같은 방향) 명시 + 모순 예시 수정 + 코드에 is_spam 불리언 신뢰 보정 로직 추가.

검증결과: 실게시판=스팸0(정상, 광고없음). 합성 광고글(대출/비아그라/카지노)=스팸0.95 정확탐지, 정상문의=정상. 2회 연속 일관.

테스트 도구: `scripts/test_spam_scan.py "<게시판URL>"` — 서버/DB 없이 본문추출+GPT판별 결과를 바로 출력.
환경: playwright chromium은 `NODE_TLS_REJECT_UNAUTHORIZED=0 python -m playwright install chromium`으로 설치함(이 PC TLS 가로채기 때문).

### 다음에 할 일 (AI 스팸 관련)
- 다른 CMS의 병원 게시판 1~2개로 더 테스트(셀렉터/본문 셀렉터 커버리지 확인). 그누보드/워드프레스 계열은 이미 셀렉터 있음.
- (선택) 스팸 탐지 시 이메일 알림 실제 발송 경로 점검.

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
