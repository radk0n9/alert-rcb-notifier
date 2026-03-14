import logging
import threading
import time

import requests
from src.db_manager.manager import DatabaseManager
from src.notifier.utils import BASE_URL, STATUS_TTL, delete_message, schedule_delete


class TelegramListener(threading.Thread):
    def __init__(self, token: str, db_manager: DatabaseManager, state: dict, allowed_chat_ids: set):
        super().__init__(daemon=True)
        self.logger = logging.getLogger(__name__)
        self.token = token
        self.db_manager = db_manager
        self.state = state  # shared dict: {"next_check_at": float, "test_mode": bool}
        self.allowed_chat_ids = allowed_chat_ids
        self._offset = None

    def run(self):
        self._delete_webhook()
        self.logger.info("Telegram listener started")
        while True:
            try:
                self._poll()
            except Exception as e:
                self.logger.error("Listener error: %s", e)
                time.sleep(5)

    def _delete_webhook(self):
        url = BASE_URL.format(token=self.token, method="deleteWebhook")
        try:
            response = requests.post(url, json={"drop_pending_updates": False}, timeout=10)
            response.raise_for_status()
            self.logger.debug("Webhook cleared")
        except requests.RequestException as e:
            self.logger.warning("Could not clear webhook: %s", e)

    def _poll(self):
        params = {"timeout": 30, "allowed_updates": ["message", "channel_post"]}
        if self._offset is not None:
            params["offset"] = self._offset

        url = BASE_URL.format(token=self.token, method="getUpdates")
        response = requests.get(url, params=params, timeout=40)
        response.raise_for_status()
        updates = response.json().get("result", [])

        self.logger.debug("Poll: %d update(s)", len(updates))
        for update in updates:
            self._offset = update["update_id"] + 1
            self._handle(update)

    def _handle(self, update: dict):
        message = update.get("message") or update.get("channel_post", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")

        self.logger.debug("Update from chat_id=%s text=%r", chat_id, text)

        if not chat_id or not text.startswith("/status"):
            return

        if str(chat_id) not in self.allowed_chat_ids:
            self.logger.warning("Ignored /status from unauthorized chat_id %s", chat_id)
            return

        self.logger.info("Received /status from chat_id %s", chat_id)
        delete_message(self.token, chat_id, message_id, label="/status command")
        self._send_status(chat_id)

    def _send_status(self, chat_id: int):
        record = self.db_manager.get_latest_record()

        lines = ["<b>alert-rcb status</b>"]

        if record:
            lines.append(f"\nLast alert: <b>{record['title']}</b>")
            lines.append(f"Date: <i>{record['date']}</i>")
        else:
            lines.append("\nNo alerts in DB yet.")

        next_check_at = self.state.get("next_check_at")
        if next_check_at:
            remaining = int(next_check_at - time.time())
            if remaining > 0:
                mins, secs = divmod(remaining, 60)
                lines.append(f"\nNext check in: {mins}m {secs}s")
            else:
                lines.append("\nNext check: running now")

        if self.state.get("test_mode"):
            lines.append("\nMode: <i>test</i>")

        lines.append(f"\n<i>This message will be deleted in {STATUS_TTL}s</i>")

        url = BASE_URL.format(token=self.token, method="sendMessage")
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": "\n".join(lines),
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            response.raise_for_status()
            sent_message_id = response.json()["result"]["message_id"]
            self.logger.info("Sent status message (will delete in %ds)", STATUS_TTL)
            schedule_delete(self.token, chat_id, sent_message_id, STATUS_TTL, label="status reply")
        except requests.RequestException as e:
            self.logger.error("Failed to send /status reply: %s", e)
