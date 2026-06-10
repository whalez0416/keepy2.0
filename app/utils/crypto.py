"""
민감 정보(고객 게시판 관리자 비밀번호 등) 저장 시 사용하는 컬럼 단위 암호화.

SECRET_KEY에서 Fernet 키를 파생하여 DB에는 암호문만 저장한다.
DB 파일이 유출되어도 SECRET_KEY 없이는 비밀번호를 복원할 수 없다.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TypeDecorator, Text

from ..config import settings


def _fernet() -> Fernet:
    # SECRET_KEY(임의 길이 문자열) → 32바이트 → urlsafe base64 → Fernet 키
    seed = (settings.SECRET_KEY or "dev-only-insecure-key-change-me").encode("utf-8")
    digest = hashlib.sha256(seed).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


class EncryptedString(TypeDecorator):
    """저장 시 자동 암호화, 조회 시 자동 복호화되는 문자열 컬럼.

    기존에 평문으로 저장돼 있던 값(복호화 실패)은 그대로 반환하여 하위호환을 유지한다.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None or value == "":
            return value
        return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")

    def process_result_value(self, value, dialect):
        if value is None or value == "":
            return value
        try:
            return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
        except (InvalidToken, ValueError, TypeError):
            # 암호화 이전에 저장된 평문 값 → 그대로 반환
            return value
