SEARCH_REGEX = '(ABC-[0-9]+)'
POST_CHANNEL = 'development'
BROADCAST_AFTER_SECONDS = 3600
PICKLE_FILE = 'threads.p'

BOT_ID = 'B01234567'
BOT_ALIAS = {
    'B01234567': {'username': 'RS Threader Bot', 'icon_url': 'http://image.png'},
    'B01234567': {'username': 'jira', 'icon_url': 'http://image.png'},
    'B01234567': {'username': 'Bitbucket', 'icon_url': 'http://image.png'}
}

try:
    from local_config import *  # noqa - Intentionally vague import to override configs
except ImportError:
    logging.info("No local_config.py to import, or error importing.")
