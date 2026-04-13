import logging
import sys

# DEBUG level logger for development efficiency
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str):
    return logging.getLogger(name)

# Default logger instance for direct imports
logger = get_logger("app")
