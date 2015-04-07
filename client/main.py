import logging
import logging.handlers
from client.core import chat_client

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
fh = logging.handlers.RotatingFileHandler('client.log', maxBytes=1024, backupCount=5)
fh.setLevel(logging.ERROR)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)

try:
    client = chat_client.ChatClient()
    client.start()
except Exception as ex:
    logging.getLogger(__name__).error(ex)
