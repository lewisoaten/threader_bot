SEARCH_REGEX = '(ABC-[0-9]+)'
BOT_ID = 'B01234567'
POST_CHANNEL = 'development'
BROADCAST_AFTER_SECONDS = 3600
PICKLE_FILE = 'threads.p'

try:
    from local_config import *  # noqa - Intentionally vague import to override configs
except ImportError:
    logging.info("No local_config.py to import, or error importing.")
