"""
Playwright 브라우저 동시 실행을 제한하는 글로벌 세마포어.
Chromium 인스턴스가 동시에 여러 개 뜨면 메모리 폭주가 발생하므로,
한 번에 최대 1개만 실행되도록 제한합니다.
"""
import threading

# 동시에 1개의 Playwright 브라우저만 실행 허용
browser_semaphore = threading.Semaphore(1)
