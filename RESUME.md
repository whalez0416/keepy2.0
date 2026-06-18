# 작업 이어가기 (Resume) — Keepy

> 다음 세션에서 이 파일을 먼저 읽으면 현재 상태와 다음 할 일을 파악할 수 있습니다.
> 마지막 작업 기준일: 2026-06-18

## ⏸️ 퇴근 전 스냅샷 (여기부터 이어서) — 2026-06-18

**지금 상태: 두 갈래가 떠 있음. 코드 작업은 다 끝났고, "내가 직접 해야 하는 외부 작업"만 남음.**

### 갈래 A) Keepy 본제품 — 배포만 남음
- 코드: 판매전 BLOCKER + 배포전 SHOULD-FIX 전부 처리 완료. **GitHub push까지 완료**(production-refactor, 최신 9768328). 로컬=origin 동기화됨.
- **다음 할 일(내가 브라우저로 로그인해야 하는 부분, AI가 대신 못함):**
  1. **Supabase**에서 Postgres 프로젝트 생성(Region: Seoul) → 연결 URL(postgresql://...) 복사
  2. **Render** → New → **Blueprint** → repo `whalez0416/keepy2.0` 연결(render.yaml 자동인식) → 환경변수 값 채우기:
     - `SECRET_KEY` = `OgMiiGtiXWV8eUi3cs0EJpeZnDa4OW6qOknwpgz9RMmIC7y5lkQ0da1mSvK4027b`
     - `DATABASE_URL` = (Supabase URL) / `MASTER_EMAIL`·`MASTER_PASSWORD` / `OPENAI_API_KEY`
     - `SMTP_USER`=chjandhot@gmail.com / `SMTP_PASSWORD`=Gmail앱비번 / `SMTP_FROM_EMAIL`=chjandhot@gmail.com / `DEBUG`=false
  3. 빌드 완료 후 주소 확인 → **production-refactor를 main에 머지**(AI가 git으로 처리 가능)
  - ⚠️ 환경변수 세팅 "먼저", main 머지 "나중"(SECRET_KEY 없으면 부팅 실패)
  - SMTP는 chjandhot@gmail.com로 실발송 검증됨. 앱비번은 .env에 이미 있음(배포엔 별도 입력 필요).

### 갈래 B) 영업용 메일링 도구 — 1차 완성, 로컬 테스트만 남음
- 위치 `C:\python\keepy new\keepy_outreach` (keepy_mvp와 별개 폴더, 아직 git 아님).
- 완성+검증됨(수집/(광고)강제/수신거부/전라우트). 상세는 그 폴더 README.md + 메모 [[keepy-outreach-tool]].
- **다음 할 일:** `cp .env.example .env`로 SMTP·SENDER_* 채우고 `uvicorn app.main:app --reload --port 8001` → http://localhost:8001 에서 ①수집 ②연락처 ③테스트발송 순으로 한번 돌려보기.
- 보완 후보: CSV 일괄 import, 발송 리포트, 본문 템플릿 저장. 실발송 캠페인은 수신거부 링크 동작 위해 외부 배포(PUBLIC_BASE_URL) 필요.

---

## 🟢 2026-06-18 (2차) — 판매가능성 종합 점검 + BLOCKER 정비 완료

서브에이전트 4명 병렬 종합검토(보안/멀티테넌시·체커 견고성·영업문구 정직성·운영안정성)
→ BLOCKER 다수 발견 → 전부 수정 → 재검토로 검증. 모든 변경 커밋됨(origin보다 앞섬, push 안 함).

**고친 것(커밋 c8b8e5e, 0975650, 0ac772d, 4f9b476, 287b708, 931ac03):**
1. 거짓 경보 3대장: 연락처(전화번호 평문 인식+정확/끝8자리 매칭, 시스템오류는 warning), 화면(임계값 90→60), 관리자(로그인폼 있으면 정상). homepage 200 정지/주차페이지 탐지. networkidle 10s 타임아웃(contact/visual/form).
2. 보안: 폼/게시판 비밀번호 API 응답 제외(schemas Field exclude + has_password, **spam.py는 response_model 추가로 별도 차단**). 마스터 계정 부팅 시 비번 덮어쓰기 제거(시드-원스). 공개 회원가입 기본 차단(ALLOW_PUBLIC_REGISTRATION=False).
3. 폼 오염: submit_test 플래그(기본 False=미제출 점검). 설정모달에 성공메시지·제출토글 추가.
4. 영업문구 정직화: 문자/카카오 '출시예정', SLA 99.9% 제거, 5분/자동배너/피해0원 시나리오 톤다운, 더미번호 제거.
5. 배포: Pillow 추가, render.yaml starter+Postgres(sqlite기본 제거), 스팸 브라우저 누수 try/finally+세마포어, 경량 마이그레이션 견고화. 죽은 spam_hunter.py 삭제.

**배포 전 SHOULD-FIX도 처리 완료(커밋 fd6cbb8):**
- RBAC 강제(OWNER/ADMIN/EDITOR=쓰기, VIEWER=읽기) — sites/spam/checks
- SSRF 방어(url_guard, 공인IP만) — discovery/scan
- auto_discovery 브라우저 세마포어+try/finally 누수차단
- 스크린샷 보존정책: 30일(SCREENSHOT_RETENTION_DAYS) 자동삭제 + 로그상세 다운로드(보관) 버튼 + 안내문. 인증 스크린샷 엔드포인트 신규(/api/logs/screenshot/{id}).

**아직 남은 작은 SHOULD-FIX(확장 전):** 화면 baseline 노후화, update_site 비번보존이 폼이름 기준(이름 변경 시 재입력 필요), _consecutive_fails 인메모리.

**→ 다음: GitHub push(이 PC는 `git -c http.sslVerify=false push origin production-refactor` 직접 실행) → Supabase Postgres → Render(starter) Docker + 환경변수(SECRET_KEY/MASTER_*/OPENAI/DATABASE_URL/SMTP_*) → production-refactor를 main에 머지/배포. 상세는 DEPLOY.md.**

## 🟢 2026-06-18 (1차) — 판매 전 알림 결함 정비

영업 시작 전 "정말 팔아도 되는가" 점검 중 **핵심 가치인 알림 전달이 고객에게 안 닿던 구조적 결함**을 발견·수정. **커밋 완료 `7efdfe6`** (origin보다 4커밋 앞섬, 아직 push 안 함).

1. **알림 이메일이 고객이 아니라 운영자에게만 가던 문제 수정** (가장 치명적)
   - `email_service.send_alert_email`: `msg['To']=SMTP_USER` 고정 → `recipients` 목록 파라미터로 변경, 없으면 운영자 폴백.
   - `Organization`에 `notify_emails`·`notify_phones`(쉼표 다수) 컬럼 추가(`models.py`). `db.py`에 Alembic 없는 환경용 경량 컬럼 마이그레이션(`run_light_migrations`) 추가, `main.py` 부팅 시 실행(멱등).
   - `alert_service._recipients_for_site`: 조직 notify_emails → billing_email 순으로 수신처 계산. 휴대폰은 SMS/알림톡 미연동이라 **로그만**(거짓 발송 금지). 
   - API: `PATCH /api/organizations/{id}`(OWNER/ADMIN/superadmin) 추가. 프론트 `SettingsView`에 "알림 수신" 섹션 추가(이메일/휴대폰 입력·저장).

2. **연락처변조·화면변조·SSL 알림이 이메일을 안 보내던 문제 수정 + 알림 일원화**
   - 기존: 이 3개는 체커가 Alert를 **직접** 생성, 이메일은 0. `handle_check_result`엔 분기 자체가 없었음.
   - 변경: 체커들의 직접 Alert 생성 제거(contact/visual/ssl) → 전부 `handle_check_result` 한곳에서 Alert+이메일+쿨다운 처리. `handle_check_result`에 contact_hijack/visual_defacement/ssl 분기 추가.
   - scheduler·checks.py(수동 점검) 양쪽 모두 동일 경로로 라우팅. visual은 **warning(변조 의심)만** 알림(시스템 fail은 오탐 방지 위해 제외).
   - 검증: 격리 임시 DB로 5개 유형 전부 고객 이메일 수신·Alert 1건·쿨다운 중복0 확인.

3. **상담폼 성공 판정 강화** (false negative 차단)
   - 기존 `"제출" in content` 폴백은 제출 버튼 라벨이 늘 있어 **폼이 깨져도 success로 오판**. → 제거.
   - `expected_success_text` 있으면 그것만으로 판정. 없으면: 엄격한 성공문구 OR (제출 후 URL 이동 & 에러문구 없음). JS `alert()` 메시지도 캡처해 판정에 포함(게시판이 '등록되었습니다' alert 후 리다이렉트하는 케이스).

4. **홈페이지 점검 오탐 완화**: `requests.get`에 브라우저 User-Agent/Accept 헤더 + allow_redirects 추가(WAF가 python-requests를 403으로 막아 정상사이트를 장애로 오탐하는 것 방지).

### ⚠️ 다음 할 일 (우선순위)
1. ~~이 변경 묶음 커밋~~ → **완료 `7efdfe6`**.
2. ~~SMTP 실제값~~ → **완료 (2026-06-18)**: `.env`에 `chjandhot@gmail.com` + 앱비번 입력, 실메일 1건 발송 성공 확인. 발송 중 **비ASCII 호스트명(한글 PC명) EHLO 인코딩 버그** 발견·수정(`email_service` local_hostname='localhost' 고정, 커밋 `b4c8ab1`). ※ 배포 환경(Render)에도 동일 SMTP 환경변수 넣어야 함.
3. 각 고객 온보딩 시 **설정>알림 수신에 병원 담당자 이메일 입력** 필수(안 넣으면 운영자에게만 감).
4. (선택) SMS/카카오 알림톡 게이트웨이 연동하면 notify_phones 실발송 가능.
5. 랜딩·앱의 `02-1234-5678` 실제 번호 교체.
6. 끝나면 GitHub push → 배포. push는 이 PC TLS 가로채기로 `git -c http.sslVerify=false push origin production-refactor` 필요(자동 보안검사가 막으면 사용자가 `! ...`로 직접 실행).

---

## 🟢 2026-06-16에 한 것

1. **디자인 건메탈/택티컬 리스킨 완료 — 커밋 `e4c9713`**
   - 랜딩(`app/static/landing.css`): 흑백 → 차가운 강철빛 + 각진 모서리 + 브러시드 패널 + 메탈(은빛) 버튼.
   - 앱 전체(15개 `.tsx`): 브랜드 강조 `emerald`→스틸(`#9fb2c2`/`#c8d4de`). **상태색(정상=초록/장애=빨강/주의=주황)은 의미상 유지.** 동일 규칙서로 서브에이전트 4명 병렬 변환 후 빌드·스크린샷 검수.
   - 로그인/회원가입(`LoginView`·`RegisterView`): emerald→스틸, **"Keepy V2" → "Keepy"**(V2 표기 전부 제거). `index.css`의 `gradient-text`(초록→파랑)도 스틸로, 사이드바 V2 배지 제거.
   - 잠재버그 수정: 기능 아이콘 `.fi` 클래스 충돌(문의폼 입력칸 `padding` 누수로 svg가 6px로 찌부러짐), 요금 카드 CTA 하단 정렬.

2. **핵심 7기능 실동작 검증 — 7/7 통과**
   - 제품 실제 점검함수(`check_homepage`/`check_form`/`check_contact`/`check_visual_defacement`/`ssl_service`/`handle_check_result`/배너 공개 API)를 **격리 임시 DB + 내가 통제하는 로컬 테스트 사이트**로 호출, 정상→일부러 장애→탐지·알림 확인. 이메일은 가로채 실발송 안 함. (검증 하네스 `_verify_features.py`는 정리·삭제함)

3. **검증 중 실버그 1개 발견·수정 (⚠️ 아직 커밋 안 됨 — working tree에만 있음)**
   - `app/services/alert_service.py`: 스케줄러는 `handle_check_result(..., check_type=f"form:{name}", ...)`로 넘기는데 알림 분기는 `if check_type == "form"`(정확 일치)만 봐서 **상담폼 장애 시 알림/이메일이 한 번도 안 나가던 버그**. → `check_type.startswith("form")`으로 수정. **내일 이 수정부터 커밋할 것.**

### ⚠️ 내일 할 일 (우선순위)
1. **`alert_service.py` 폼 버그 수정 커밋** (지금 uncommitted).
2. **이메일 알림 커버리지 보완**: 현재 이메일 발송은 `homepage`·`form`·`spam`만. **`contact_hijack`(연락처 변조)·`visual_defacement`·`ssl`은 체커 내부에서 Alert(대시보드)만 만들고 이메일은 안 감.** 헤드라인 기능인 연락처 변조 즉시알림이 메일로 안 나가므로 판매 전 연결 필요. (단, 중복 Alert 안 생기게 주의 — 이 3개는 이미 체커가 Alert를 직접 생성함)
3. **SMTP 실제값 입력**: `.env`의 `SMTP_USER`/`SMTP_PASSWORD`가 아직 `your_email`/`your_app_password` **placeholder** → Gmail 앱 비밀번호 넣어야 실제 메일 발송됨.
4. (랜딩·앱 곳곳의 `02-1234-5678`도 실제 번호로 교체 필요)
5. 위 끝나면 **GitHub push → 배포**. **push는 이 PC TLS 가로채기로 `git -c http.sslVerify=false push origin production-refactor` 필요한데, 자동 보안검사가 막음** → 사용자가 직접 `! ...`로 실행하거나 Bash 권한 추가해야 함.

---


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
