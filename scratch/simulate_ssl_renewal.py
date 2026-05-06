import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from app.db import SessionLocal, engine, Base
from app.models import Site, Organization, Alert, Log
from app.services.ssl_service import check_and_renew_ssl

def run_simulation():
    print("=" * 50)
    print("🚀 SSL 자동 연장(Auto-Renewal) 시뮬레이션 테스트")
    print("=" * 50)

    # DB 초기화
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. 테스트 데이터 준비 (Pro 플랜)
        org = db.query(Organization).filter(Organization.slug == "ssl-test-org").first()
        if not org:
            org = Organization(name="SSL 테스트 병원", slug="ssl-test-org", plan="pro")
            db.add(org)
            db.flush()
        
        test_url = "https://hospital-security-test.com"
        site = db.query(Site).filter(Site.homepage_url == test_url).first()
        if not site:
            site = Site(org_id=org.id, site_name="보안 테스트 사이트", homepage_url=test_url)
            db.add(site)
            db.commit()
            print(f"[SETUP] 테스트 사이트 생성 완료: {test_url}")

        # ---------------------------------------------------------
        # 시나리오: 인증서 만료가 10일 남은 상황 모의
        # ---------------------------------------------------------
        print("\n[시나리오] 인증서 만료 10일 전 상황 모의 (자동 연장 트리거 대상)")
        
        # 현재 시간 기준으로 10일 뒤 날짜 생성
        ten_days_later = datetime.now() + timedelta(days=10)
        # SSL 인증서 날짜 포맷: 'Mar 15 14:00:00 2026 GMT'
        mock_expiry_str = ten_days_later.strftime('%b %d %H:%M:%S %Y GMT')
        
        mock_cert = {'notAfter': mock_expiry_str}

        # Socket 및 SSL 모듈 모킹
        with patch('socket.create_connection'), \
             patch('ssl.create_default_context') as mock_context:
            
            # 내부 wrap_socket이 반환하는 객체의 getpeercert가 mock_cert를 반환하도록 설정
            mock_ssock = MagicMock()
            mock_ssock.getpeercert.return_value = mock_cert
            mock_context.return_value.wrap_socket.return_value.__enter__.return_value = mock_ssock
            
            # SSL 체크 및 연장 서비스 실행
            success = check_and_renew_ssl(db, site)
            
            if success:
                print(f"✅ 결과: 만료 {10}일 전임을 성공적으로 인지하고 자동 연장을 완료했습니다.")
            else:
                print("❌ 결과: 자동 연장이 실행되지 않았습니다.")

            # DB에 생성된 알림(Alert)과 로그(Log) 확인
            latest_alert = db.query(Alert).filter(Alert.site_id == site.id, Alert.check_type == "ssl_renewal").order_by(Alert.id.desc()).first()
            latest_log = db.query(Log).filter(Log.site_id == site.id, Log.check_type == "ssl_renewal").order_by(Log.id.desc()).first()

            if latest_alert and "완료" in latest_alert.message:
                print(f"🔔 생성된 알림 메시지: {latest_alert.message}")
            
            if latest_log:
                print(f"📝 생성된 실행 로그: {latest_log.raw_result}")

    except Exception as e:
        print(f"❌ 시뮬레이션 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n" + "=" * 50)
        print("시뮬레이션 테스트 종료")
        print("=" * 50)

if __name__ == "__main__":
    run_simulation()
