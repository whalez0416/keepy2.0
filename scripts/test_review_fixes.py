# -*- coding: utf-8 -*-
"""2026-07-06 판매 전 정비 수정 검증 (격리 임시 DB, 실제 네트워크/SMTP 없음).

실행: python scripts/test_review_fixes.py
검증 항목:
  T1 연락처 감시(expected_phone) 생성→조회→수정이 ContactConfig에 실제 반영
  T2 hospital_name 수정 반영
  T3 상담폼 1회 실패는 알림 없음, 2연속 실패에만 danger 알림
  T4 정상 복구 시 미해결 알림 resolved_at 세팅 + (발송된 danger면) 복구 메일
  T5 수동 점검 API 즉시 응답 + 중복 실행 가드
  T6 스팸 점검 Log 기록 (탐지=warning / 무탐=success)
  T7 homepage 다운 신호에서 광범위 단독 문구 제거됨
  T8 알림 메일 시각이 KST 표기
"""
import os
import sys
import tempfile

os.environ["DEBUG"] = "true"
_tmp_db = os.path.join(tempfile.mkdtemp(prefix="keepy_test_"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
# SMTP 실발송 차단(설정 자체를 비움 — 코드는 monkeypatch로도 한 번 더 차단)
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db import engine, Base, SessionLocal, get_db
from app import models
from app.api import sites as sites_api
from app.api import checks as checks_api
from app.api.auth import get_current_user
from app.services import alert_service

Base.metadata.create_all(bind=engine)

# ── 테스트 데이터 ──────────────────────────────────────────
db = SessionLocal()
org = models.Organization(name="테스트병원", slug="test-hosp", notify_emails="owner@test.com")
db.add(org)
admin = models.User(email="admin@test.com", hashed_password="x", role=models.UserRole.SUPERADMIN)
db.add(admin)
db.commit()
db.refresh(org); db.refresh(admin)
ORG_ID, ADMIN_ID = org.id, admin.id
db.close()

# ── 테스트 앱 (인증 오버라이드) ────────────────────────────
test_app = FastAPI()
test_app.include_router(sites_api.router, prefix="/api/sites")
test_app.include_router(checks_api.router, prefix="/api/checks")

def _fake_user():
    d = SessionLocal()
    try:
        return d.query(models.User).get(ADMIN_ID)
    finally:
        d.close()

test_app.dependency_overrides[get_current_user] = _fake_user
client = TestClient(test_app)

# 이메일 발송 monkeypatch (호출 기록만)
sent_alerts, sent_recoveries = [], []
alert_service.send_alert_email = lambda **kw: (sent_alerts.append(kw), True)[1]
alert_service.send_recovery_email = lambda **kw: (sent_recoveries.append(kw), True)[1]

passed = []

def check(name, cond, detail=""):
    assert cond, f"[FAIL] {name} {detail}"
    passed.append(name)
    print(f"  ✓ {name}")

# ── T1: 연락처 감시 upsert ────────────────────────────────
print("T1 연락처 감시 생성/조회/수정")
r = client.post("/api/sites/", json={
    "site_name": "민병원", "homepage_url": "https://example.com",
    "org_id": ORG_ID, "expected_phone": "02-111-2222",
})
check("사이트 생성", r.status_code == 200, r.text)
site_id = r.json()["id"]
check("생성 응답에 expected_phone", r.json()["expected_phone"] == "02-111-2222")

r = client.get(f"/api/sites/{site_id}")
check("GET 응답에 expected_phone(과거엔 항상 null)", r.json()["expected_phone"] == "02-111-2222")

r = client.patch(f"/api/sites/{site_id}", json={"expected_phone": "02-333-4444"})
check("PATCH 200", r.status_code == 200, r.text)
d = SessionLocal()
cc = d.query(models.ContactConfig).filter_by(site_id=site_id).all()
check("ContactConfig가 실제 DB에서 갱신됨(과거엔 유령 속성)", len(cc) == 1 and cc[0].expected_phone == "02-333-4444")
d.close()
r = client.get(f"/api/sites/{site_id}")
check("수정 후 GET 반영", r.json()["expected_phone"] == "02-333-4444")

# 연락처 설정이 없던 사이트에 PATCH로 새로 추가되는지
r = client.post("/api/sites/", json={"site_name": "제2병원", "homepage_url": "https://example.com", "org_id": ORG_ID})
site2_id = r.json()["id"]
client.patch(f"/api/sites/{site2_id}", json={"expected_kakao_url": "pf.kakao.com/_abc"})
d = SessionLocal()
cc2 = d.query(models.ContactConfig).filter_by(site_id=site2_id).first()
check("기존 설정 없어도 PATCH로 신규 생성", cc2 is not None and cc2.expected_kakao_url == "pf.kakao.com/_abc")
d.close()

# ── T2: hospital_name 수정 ────────────────────────────────
print("T2 hospital_name 수정")
r = client.patch(f"/api/sites/{site_id}", json={"hospital_name": "강남점"})
check("hospital_name 반영(과거엔 조용히 무시)", r.json()["hospital_name"] == "강남점")

# ── T3: 폼 2연속 실패 규칙 ────────────────────────────────
print("T3 상담폼 알림 규칙")
d = SessionLocal()
site = d.query(models.Site).get(site_id)
ct = "form:메인상담"
d.add(models.Log(site_id=site_id, check_type=ct, status="fail")); d.commit()
alert_service.handle_check_result(d, site, ct, "fail", "타임아웃")
check("1회 실패 → 알림 없음", d.query(models.Alert).filter_by(site_id=site_id, check_type=ct).count() == 0)
d.add(models.Log(site_id=site_id, check_type=ct, status="fail")); d.commit()
alert_service.handle_check_result(d, site, ct, "fail", "타임아웃")
alerts = d.query(models.Alert).filter_by(site_id=site_id, check_type=ct).all()
check("2연속 실패 → danger 알림 1건", len(alerts) == 1 and alerts[0].alert_level == "danger")
check("알림 이메일 발송 호출됨", len(sent_alerts) == 1)

# ── T4: 복구 처리 ─────────────────────────────────────────
print("T4 복구(resolved_at + 복구 메일)")
d.add(models.Log(site_id=site_id, check_type=ct, status="success")); d.commit()
alert_service.handle_check_result(d, site, ct, "success", None)
d.expire_all()
a = d.query(models.Alert).filter_by(site_id=site_id, check_type=ct).first()
check("resolved_at 세팅(과거엔 영원히 미해결)", a.resolved_at is not None)
check("발송됐던 danger → 복구 메일 1건", len(sent_recoveries) == 1)
# 복구 후 재발 시 다시 알림 나가는지(중복억제 회복 인지)
d.add(models.Log(site_id=site_id, check_type=ct, status="fail")); d.commit()
alert_service.handle_check_result(d, site, ct, "fail", "재발")
d.add(models.Log(site_id=site_id, check_type=ct, status="fail")); d.commit()
alert_service.handle_check_result(d, site, ct, "fail", "재발")
check("복구 후 재발 → 재알림", d.query(models.Alert).filter_by(site_id=site_id, check_type=ct).count() == 2)
d.close()

# ── T5: 수동 점검 백그라운드 + 중복 가드 ──────────────────
print("T5 수동 점검 API")
ran = []
checks_api._run_all_checks = lambda sid: ran.append(sid)  # 실제 브라우저 점검 대체
r = client.post(f"/api/checks/run/{site_id}")
check("즉시 'started' 응답", r.status_code == 200 and r.json()["status"] == "started", r.text)
check("백그라운드 태스크 실행됨", ran == [site_id])
checks_api._running_manual_checks.add(site_id)  # 진행 중 상황 재현
r = client.post(f"/api/checks/run/{site_id}")
check("진행 중이면 already_running", r.json()["status"] == "already_running")
checks_api._running_manual_checks.discard(site_id)

# ── T6: 스팸 점검 Log 기록 ────────────────────────────────
print("T6 스팸 점검 로그")
from app.services.ai_spam_classifier import _write_spam_log
d = SessionLocal()
spam_cfg = models.SpamConfig(site_id=site_id, board_url="https://example.com/board")
d.add(spam_cfg); d.commit(); d.refresh(spam_cfg)
_write_spam_log(d, spam_cfg, {"status": "success", "spam_detected": 2})
_write_spam_log(d, spam_cfg, {"status": "success", "spam_detected": 0})
logs = d.query(models.Log).filter_by(site_id=site_id, check_type="spam").order_by(models.Log.id).all()
check("탐지 시 warning 로그", logs[0].status == "warning" and "2건" in logs[0].fail_reason)
check("무탐 시 success 로그(회복 인지용)", logs[1].status == "success")
d.close()

# ── T7: homepage 다운 신호 정제 ───────────────────────────
print("T7 homepage 오탐 신호 제거")
import ast, inspect
from app.services import homepage_checker
tree = ast.parse(inspect.getsource(homepage_checker))
signals = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "_DOWN_SIGNALS":
        signals = [c.value for c in node.value.elts]
check('"만료되었습니다" 단독 신호 제거', signals and "만료되었습니다" not in signals)
check('"정지되었습니다" 단독 신호 제거', "정지되었습니다" not in signals)
check('복합 신호("도메인이 만료")는 유지', "도메인이 만료" in signals)

# ── T8: KST 시각 표기 ─────────────────────────────────────
print("T8 알림 시각 KST")
check("발송 시각이 KST 포맷", "(한국시간)" in sent_alerts[0]["checked_at"])

# ── T9: 옛 미해결 알림 일괄 해결 시 복구 메일 억제 ────────
print("T9 복구 메일 게이트(최근 실패 이력 없으면 침묵 해결)")
d = SessionLocal()
site2 = d.query(models.Site).get(site2_id)
from datetime import datetime, timedelta
old = datetime.utcnow() - timedelta(days=20)
d.add(models.Alert(site_id=site2_id, check_type="homepage", alert_level="danger",
                   message="옛 오경보", sent_at=old, created_at=old))
d.commit()
before = len(sent_recoveries)
alert_service.handle_check_result(d, site2, "homepage", "success", None)
d.expire_all()
a2 = d.query(models.Alert).filter_by(site_id=site2_id, check_type="homepage").first()
check("옛 알림 resolved_at 처리됨", a2.resolved_at is not None)
check("최근 실패 이력 없으면 복구 메일 안 나감(배포 백필 보호)", len(sent_recoveries) == before)
d.close()

# ── T10: 연락처 감시 값 모두 비우면 비활성화 ──────────────
print("T10 연락처 감시 비우기 → 비활성화")
client.patch(f"/api/sites/{site_id}", json={"expected_phone": "", "expected_kakao_url": ""})
d = SessionLocal()
cc3 = d.query(models.ContactConfig).filter_by(site_id=site_id).first()
check("둘 다 비우면 is_active=False(유령 점검 방지)", cc3.is_active is False)
d.close()
client.patch(f"/api/sites/{site_id}", json={"expected_phone": "02-999-8888"})
d = SessionLocal()
cc4 = d.query(models.ContactConfig).filter_by(site_id=site_id).first()
check("다시 값 넣으면 재활성화", cc4.is_active is True and cc4.expected_phone == "02-999-8888")
d.close()

print(f"\n전체 통과: {len(passed)}건 ✅")
