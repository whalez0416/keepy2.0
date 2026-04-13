import requests
from sqlalchemy.orm import Session
from ..models import Site, Membership, MembershipRole
from ..utils.logger import get_logger
from ..config import settings

logger = get_logger("legacy_connector")

class LegacyKeepyClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def fetch_sites(self):
        """1.0 서버에서 사이트 리스트를 가져옵니다."""
        try:
            response = requests.get(f"{self.base_url}/sites", headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[LEGACY] 사이트 목록 가져오기 실패: {e}")
            return []

    def import_to_2_0(self, db: Session, user_id: int):
        """가져온 데이터를 2.0 DB에 저장(마이그레이션)합니다."""
        legacy_sites = self.fetch_sites()
        imported_count = 0
        
        for ls in legacy_sites:
            # 중복 체크 (URL 기준)
            existing = db.query(Site).filter(Site.homepage_url == ls.get("url")).first()
            if existing:
                logger.debug(f"[LEGACY] 이미 존재하는 사이트 건너뜀: {ls.get('name')}")
                continue
            
            # 신규 사이트 등록
            new_site = Site(
                site_name=ls.get("name", "Legacy Site"),
                homepage_url=ls.get("url"),
                form_url=ls.get("form_url"),
                is_active=True
            )
            db.add(new_site)
            db.flush() # ID 생성을 위해 flush
            
            # 소유권 설정 (회원 정보 연동)
            membership = Membership(
                user_id=user_id,
                site_id=new_site.id,
                role=MembershipRole.OWNER
            )
            db.add(membership)
            imported_count += 1
            
        db.commit()
        logger.info(f"[LEGACY] 마이그레이션 완료: {imported_count}개의 사이트를 가져왔습니다.")
        return imported_count

# 싱글톤 인스턴스 (설정에서 URL 로드 가능)
legacy_client = LegacyKeepyClient(base_url="https://keepy-api.onrender.com")
