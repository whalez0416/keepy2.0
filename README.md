# Keepy MVP

병원 홈페이지 모니터링 시스템 (MVP)

## 주요 기능
- 홈페이지 HTTP 상태 및 응답 속도 주기적 점검.
- Playwright를 이용한 상담 폼 자동 제출 테스트.
- 장애 발생 시 이메일(SMTP) 알림 발송.
- 점검 이력 및 알림 로그 저장.

## 설치 및 설정

1. **패키지 설치**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **환경 설정**:
   `.env.example` 파일을 `.env`로 복사하고 SMTP 설정을 입력합니다.
   ```bash
   cp .env.example .env
   ```

3. **서버 실행**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API 사용법

- **사이트 등록**: `POST /sites`
- **사이트 목록**: `GET /sites`
- **수동 점검 실행**: `POST /checks/run/{site_id}`
- **로그 조회**: `GET /logs`
- **알림 조회**: `GET /alerts`

## 상담 폼 테스트 설정
사이트 등록 시 아래 셀렉터 정보를 입력하여 폼 테스트를 활성화할 수 있습니다:
- `form_url`: 상담 신청 페이지 URL.
- `name_selector`: 이름 입력 필드 CSS 셀렉터.
- `phone_selector`: 연락처 입력 필드 CSS 셀렉터.
- `message_selector`: 문의 내용 입력 필드 CSS 셀렉터.
- `submit_selector`: 제출 버튼 CSS 셀렉터.
- `expected_success_text`: 성공 시 화면에 나타날 확인 문구.

## 프로젝트 구조
```
keepy_mvp/
  app/
    main.py         # 실행 엔트리포인트
    models.py       # 데이터베이스 모델
    services/       # 체크 및 알림 로직
    api/            # FastAPI 라우터
  requirements.txt
  .env
```
