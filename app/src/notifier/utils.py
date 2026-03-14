import logging
import threading
import time

import requests

BASE_URL = "https://api.telegram.org/bot{token}/{method}"
STATUS_TTL = 30

logger = logging.getLogger(__name__)


def delete_message(token: str, chat_id: int, message_id: int, label: str = "message") -> None:
    if not message_id:
        return
    url = BASE_URL.format(token=token, method="deleteMessage")
    try:
        response = requests.post(
            url, json={"chat_id": chat_id, "message_id": message_id}, timeout=10
        )
        response.raise_for_status()
        logger.info("Deleted %s (message_id=%s)", label, message_id)
    except requests.RequestException as e:
        logger.debug("Could not delete %s (message_id=%s): %s", label, message_id, e)


def schedule_delete(token: str, chat_id: int, message_id: int, delay: int, label: str = "message") -> None:
    def _delete():
        time.sleep(delay)
        delete_message(token, chat_id, message_id, label)

    threading.Thread(target=_delete, daemon=True).start()
