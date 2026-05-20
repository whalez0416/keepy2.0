from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from .config import settings

# 동시 실행 스레드를 3개로 제한하여 리소스 고갈 방지
executors = {
    'default': ThreadPoolExecutor(max_workers=3)
}

# misfire_grace_time: 밀린 작업이 60초 이내면 실행, 초과 시 건너뜀
# coalesce: 밀린 같은 작업은 1회만 실행
job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': 60
}

scheduler = BackgroundScheduler(
    executors=executors,
    job_defaults=job_defaults
)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
