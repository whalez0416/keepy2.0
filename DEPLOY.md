# Keepy 배포 가이드 (단일 컨테이너 / A안)

이 문서는 **개발 지식이 없어도** 따라 할 수 있도록 만든 배포 안내입니다.
구조는 **Docker 컨테이너 하나**가 모든 걸 처리합니다:

```
https://(내 주소)/          → 영업 랜딩 페이지
https://(내 주소)/app/login → 관리자 로그인 (마스터 + 고객)
https://(내 주소)/api/...    → API (자동, 직접 쓸 일 없음)
```

---

## 0. 미리 만들어 둘 무료 계정

1. **GitHub** (github.com) — 코드 보관 + 자동 배포 트리거
2. **Render** (render.com) — 서버(백엔드+프론트) 호스팅
3. **Supabase** (supabase.com) — PostgreSQL 데이터베이스 (무료)
4. **UptimeRobot** (uptimerobot.com) — 무료 서버가 잠드는 걸 방지 (선택)

> 💡 OpenAI 키, 이메일(Gmail 앱 비밀번호)은 이미 준비돼 있다고 가정합니다.

---

## 1. 코드를 GitHub에 올리기

> 이 폴더(`keepy_mvp`)를 통째로 GitHub 저장소로 올립니다. (`Dockerfile`이 최상단에 오도록)

터미널에서 `keepy_mvp` 폴더 안에서:

```bash
git init
git add .
git commit -m "Keepy 초기 배포"
# GitHub에서 새 저장소(예: keepy) 만든 뒤, 주소를 아래에 붙여넣기
git remote add origin https://github.com/(내아이디)/keepy.git
git branch -M main
git push -u origin main
```

> ⚠️ `.env` 파일은 `.gitignore`에 의해 **자동으로 제외**됩니다(비밀키가 GitHub에 올라가지 않음). 정상입니다.

---

## 2. 데이터베이스 만들기 (Supabase)

1. Supabase → **New project** 생성 (Region: Northeast Asia(Seoul) 권장)
2. 비밀번호(Database Password)를 정하고 **꼭 메모**
3. 프로젝트 생성 후 → **Project Settings → Database → Connection string → URI** 복사
4. 복사한 주소가 이런 형태입니다:
   ```
   postgresql://postgres:[비밀번호]@db.xxxxxxxx.supabase.co:5432/postgres
   ```
   이 값을 잠시 보관해 두세요. (다음 단계에서 `DATABASE_URL`로 사용)

> `postgres://`로 시작하면 `postgresql://`로 바꿔서 넣으세요.

---

## 3. Render에 서버 배포

1. Render → **New → Web Service**
2. GitHub 저장소(keepy) 연결
3. 설정:
   - **Language/Runtime**: Docker (자동 감지됨 — `Dockerfile`을 읽음)
   - **Instance Type**: Free (파일럿) / Starter $7 (실서비스)
   - **Region**: Singapore
4. **Environment Variables**(환경변수)에 아래를 입력 (가장 중요):

| 키 | 값 |
|---|---|
| `SECRET_KEY` | 아래 4번에서 생성한 랜덤 문자열 |
| `MASTER_EMAIL` | 내 운영자 로그인 이메일 (예: master@keepy.com) |
| `MASTER_PASSWORD` | 내 운영자 로그인 비밀번호 (강하게) |
| `OPENAI_API_KEY` | 내 GPT 키 (sk-...) |
| `DATABASE_URL` | 2단계에서 복사한 Supabase 주소 |
| `SMTP_USER` | 알림 보낼 Gmail 주소 |
| `SMTP_PASSWORD` | Gmail "앱 비밀번호" (일반 비번 아님) |
| `DEBUG` | false |
| `CORS_ORIGINS` | (비워둬도 됨 — 단일 컨테이너라 불필요) |

5. **Create Web Service** → 첫 빌드는 5~10분 (Playwright 브라우저 설치 때문)

### SECRET_KEY 만드는 법
아무 컴퓨터에서 파이썬으로:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
나온 긴 문자열을 `SECRET_KEY`에 넣으세요.

### Gmail 앱 비밀번호
Google 계정 → 보안 → 2단계 인증 켜기 → "앱 비밀번호" 생성 → 16자리를 `SMTP_PASSWORD`에 입력.

---

## 4. 배포 확인

배포가 끝나면 Render가 주소를 줍니다 (예: `https://keepy-xxxx.onrender.com`).

1. `https://keepy-xxxx.onrender.com/` → **영업 랜딩**이 보이면 성공
2. `https://keepy-xxxx.onrender.com/app/login` → 로그인 화면
3. `MASTER_EMAIL` / `MASTER_PASSWORD`로 로그인 → 대시보드 진입
4. **상담 관리** 메뉴 → 랜딩에서 들어온 무료체험 신청이 여기 쌓입니다
5. 고객 계정 발급 → 고객에게 주소 + 임시 비번 전달 → 고객은 **설정 → 비밀번호 변경**

---

## 5. (무료 티어) 서버 잠듦 방지 — UptimeRobot

Render 무료는 **15분간 아무도 안 들어오면 잠들어** 자동 점검이 멈춥니다.
UptimeRobot으로 5분마다 깨워두면 완화됩니다.

1. UptimeRobot → **Add New Monitor**
2. Monitor Type: **HTTP(s)**
3. URL: `https://keepy-xxxx.onrender.com/api/health`
4. Interval: 5분
5. 저장

> ⚠️ 이건 어디까지나 임시방편입니다. **실제 유료 고객을 받으면 Render Starter($7/월)로 올려 항상 켜두세요.** 모니터링 제품이 잠들면 안 됩니다.

---

## 6. (선택) 내 도메인 연결

- 도메인 구매(예: 가비아/Namecheap) → Render의 **Custom Domains**에 추가 → 안내대로 DNS(CNAME) 설정
- 연결 후 `https://keepy.co.kr` 같은 주소로 접속 가능

---

## 7. 코드 수정 후 재배포

코드를 고친 뒤:
```bash
git add .
git commit -m "수정 내용"
git push
```
→ Render가 **자동으로 다시 빌드/배포**합니다. (별도 조작 불필요)

---

## ✅ 비용 요약

| 단계 | 구성 | 월 비용 |
|---|---|---|
| 파일럿/데모 | Render 무료 + Supabase 무료 + UptimeRobot | **0원** (느림/잠듦 감수) |
| 실서비스 | Render Starter + Supabase 무료 | **약 1만원** (항상 켜짐) |
| + 도메인 | (선택) | 연 1~2만원 |

---

## 주의사항

- **무료 Render는 데이터 디스크가 없습니다.** 그래서 DB는 반드시 Supabase(외부)를 써야 데이터가 안 사라집니다. (이 가이드대로 하면 됨)
- **첫 배포 시 DB는 비어 있습니다.** 마스터 계정은 환경변수로 자동 생성됩니다. 로컬 테스트 데이터(keepy.db)는 배포본과 무관합니다.
- **OpenAI 비용**: 스팸 분류 호출당 소액 과금. platform.openai.com에서 사용량/한도 확인.
- **비밀키 관리**: `SECRET_KEY`, `MASTER_PASSWORD`, `OPENAI_API_KEY`는 Render 환경변수에만 넣고 GitHub엔 절대 올리지 마세요. (`.env`는 이미 git 제외됨)
