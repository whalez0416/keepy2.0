from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from .config import settings

# 동시 실행 스레드를 3개로 제한하여 리소스 고갈 방지
executors = {
    'default': ThreadPoolExecutor(max_workers=3)
}

# misfire_grace_time: 예정 시각보다 늦게 시작돼도 이 시간 이내면 실행, 초과 시 '조용히' 건너뜀.
# 브라우저 점검(visual/form/contact/spam)은 단일 세마포어로 직렬화돼 한 건당 10~120초가
# 걸리므로, 같은 시각에 여러 사이트가 몰리면 60초로는 뒤 순번이 누락된다(감시 구멍).
# 5분으로 늘려 대기열이 밀려도 실제로는 실행되게 한다. (점검 시각 분산은 scheduler_service에서)
# coalesce: 밀린 같은 작업은 1회만 실행
job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': 300
}

scheduler = BackgroundScheduler(
    executors=executors,
    job_defaults=job_defaults
)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
