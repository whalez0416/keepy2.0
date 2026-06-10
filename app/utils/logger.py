import logging
import sys
from ..config import settings

# 운영(DEBUG=False)에서는 INFO 레벨로 올려 민감정보/페이로드 과다 로깅을 방지.
_level = logging.DEBUG if settings.DEBUG else logging.INFO

logging.basicConfig(
    level=_level,
    format='[%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str):
    return logging.getLogger(name)

# Default logger instance for direct imports
logger = get_logger("app")
